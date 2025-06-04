"""
バックアップ管理システム
5分毎自動バックアップ・差分バックアップ・圧縮・世代管理
"""

import os
import time
import shutil
import zipfile
import threading
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from ..exceptions import BackupError, FileIOError


@dataclass
class BackupInfo:
    """バックアップ情報"""
    backup_id: str
    backup_path: str
    created_at: datetime
    source_path: str
    backup_type: str  # full/incremental/differential
    compressed: bool
    size_bytes: int
    file_count: int
    description: str = ""


class BackupManager:
    """
    バックアップ管理システム
    
    機能:
    - 5分毎自動バックアップ
    - 差分バックアップ（変更ファイルのみ）
    - 圧縮バックアップ
    - 世代管理（古いバックアップ自動削除）
    - 高速復旧
    """
    
    def __init__(self, backup_root_dir: str, backup_interval: int = 300):  # 5分
        self.backup_root_dir = backup_root_dir
        self.backup_interval = backup_interval
        self.max_backup_generations = 10
        self.compression_enabled = True
        self.compression_level = 6  # 0-9, 6が標準
        
        # 自動バックアップ制御
        self.auto_backup_thread = None
        self.is_running = False
        
        # 実行中タスク管理
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # バックアップ履歴
        self.backup_history: List[BackupInfo] = []
        self._load_backup_history()
        
        # 変更検知用
        self.last_backup_time = {}  # source_path -> timestamp
        self.file_checksums = {}   # file_path -> checksum
        
        # ディレクトリ初期化
        os.makedirs(self.backup_root_dir, exist_ok=True)
        
    def start_auto_backup(self, source_directories: List[str]):
        """自動バックアップ開始"""
        if self.is_running:
            return
            
        self.is_running = True
        self.source_directories = source_directories
        
        self.auto_backup_thread = threading.Thread(
            target=self._auto_backup_worker, 
            args=(source_directories,)
        )
        self.auto_backup_thread.daemon = True
        self.auto_backup_thread.start()
        
        print(f"Auto backup started for {len(source_directories)} directories")
        
    def stop_auto_backup(self):
        """自動バックアップ停止"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.auto_backup_thread:
            self.auto_backup_thread.join(timeout=10.0)
            
        self.executor.shutdown(wait=True)
        print("Auto backup stopped")
        
    def create_backup(self, source_path: str, backup_name: str = None,
                     backup_type: str = "incremental") -> BackupInfo:
        """
        バックアップ作成
        
        Args:
            source_path: バックアップ元パス
            backup_name: バックアップ名（None時は自動生成）
            backup_type: full/incremental/differential
            
        Returns:
            BackupInfo: バックアップ情報
        """
        start_time = time.perf_counter()
        
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{backup_type}_{timestamp}"
            
        backup_id = f"{backup_name}_{int(time.time())}"
        backup_path = os.path.join(self.backup_root_dir, backup_name)
        
        try:
            # バックアップタイプ別処理
            if backup_type == "full":
                file_count, size_bytes = self._create_full_backup(source_path, backup_path)
            elif backup_type == "incremental":
                file_count, size_bytes = self._create_incremental_backup(source_path, backup_path)
            elif backup_type == "differential":
                file_count, size_bytes = self._create_differential_backup(source_path, backup_path)
            else:
                raise BackupError(f"Unknown backup type: {backup_type}")
                
            # 圧縮処理
            if self.compression_enabled:
                compressed_path = backup_path + ".zip"
                self._compress_backup(backup_path, compressed_path)
                
                # 元ディレクトリ削除
                if os.path.isdir(backup_path):
                    shutil.rmtree(backup_path)
                    
                backup_path = compressed_path
                size_bytes = os.path.getsize(compressed_path)
                
            # バックアップ情報作成
            backup_info = BackupInfo(
                backup_id=backup_id,
                backup_path=backup_path,
                created_at=datetime.now(),
                source_path=source_path,
                backup_type=backup_type,
                compressed=self.compression_enabled,
                size_bytes=size_bytes,
                file_count=file_count,
                description=f"Auto backup of {os.path.basename(source_path)}"
            )
            
            # 履歴に追加
            self.backup_history.append(backup_info)
            self._save_backup_history()
            
            # 古いバックアップ削除
            self._cleanup_old_backups()
            
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"Backup created: {backup_name} ({file_count} files, {size_bytes} bytes, {elapsed_time:.2f}ms)")
            
            return backup_info
            
        except Exception as e:
            raise BackupError(f"Backup creation failed: {e}")
            
    def restore_backup(self, backup_info: BackupInfo, restore_path: str,
                      overwrite: bool = False) -> bool:
        """
        バックアップ復旧
        
        Args:
            backup_info: バックアップ情報
            restore_path: 復旧先パス
            overwrite: 既存ファイル上書き
            
        Returns:
            bool: 復旧成功フラグ
        """
        start_time = time.perf_counter()
        
        if not os.path.exists(backup_info.backup_path):
            raise BackupError(f"Backup file not found: {backup_info.backup_path}")
            
        try:
            # 復旧先ディレクトリ準備
            os.makedirs(restore_path, exist_ok=True)
            
            if backup_info.compressed:
                # 圧縮ファイルから復旧
                with zipfile.ZipFile(backup_info.backup_path, 'r') as zipf:
                    for member in zipf.namelist():
                        target_path = os.path.join(restore_path, member)
                        
                        # 既存ファイルチェック
                        if os.path.exists(target_path) and not overwrite:
                            continue
                            
                        # ディレクトリ作成
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        # ファイル展開
                        with zipf.open(member) as src, open(target_path, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
            else:
                # ディレクトリから復旧
                if overwrite:
                    shutil.copytree(backup_info.backup_path, restore_path, dirs_exist_ok=True)
                else:
                    self._copy_tree_no_overwrite(backup_info.backup_path, restore_path)
                    
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"Backup restored: {backup_info.backup_id} to {restore_path} ({elapsed_time:.2f}ms)")
            
            return True
            
        except Exception as e:
            raise BackupError(f"Backup restoration failed: {e}")
            
    def list_available_backups(self, source_path: str = None,
                              backup_type: str = None) -> List[BackupInfo]:
        """
        利用可能バックアップ一覧
        
        Args:
            source_path: ソースパスでフィルター
            backup_type: バックアップタイプでフィルター
            
        Returns:
            List[BackupInfo]: バックアップ情報リスト
        """
        filtered_backups = self.backup_history.copy()
        
        # フィルター適用
        if source_path:
            filtered_backups = [b for b in filtered_backups if b.source_path == source_path]
            
        if backup_type:
            filtered_backups = [b for b in filtered_backups if b.backup_type == backup_type]
            
        # 作成日時の降順でソート
        filtered_backups.sort(key=lambda x: x.created_at, reverse=True)
        
        return filtered_backups
        
    def get_backup_statistics(self) -> Dict[str, Any]:
        """バックアップ統計情報"""
        if not self.backup_history:
            return {"total_backups": 0}
            
        total_size = sum(b.size_bytes for b in self.backup_history)
        total_files = sum(b.file_count for b in self.backup_history)
        
        backup_types = {}
        for backup in self.backup_history:
            backup_types[backup.backup_type] = backup_types.get(backup.backup_type, 0) + 1
            
        latest_backup = max(self.backup_history, key=lambda x: x.created_at)
        
        return {
            "total_backups": len(self.backup_history),
            "total_size_bytes": total_size,
            "total_files": total_files,
            "backup_types": backup_types,
            "latest_backup": latest_backup.created_at.isoformat(),
            "compression_enabled": self.compression_enabled,
            "max_generations": self.max_backup_generations
        }
        
    def delete_backup(self, backup_id: str) -> bool:
        """バックアップ削除"""
        backup_info = None
        for backup in self.backup_history:
            if backup.backup_id == backup_id:
                backup_info = backup
                break
                
        if not backup_info:
            return False
            
        try:
            # ファイル削除
            if os.path.exists(backup_info.backup_path):
                if os.path.isdir(backup_info.backup_path):
                    shutil.rmtree(backup_info.backup_path)
                else:
                    os.remove(backup_info.backup_path)
                    
            # 履歴から削除
            self.backup_history.remove(backup_info)
            self._save_backup_history()
            
            return True
            
        except Exception as e:
            print(f"Failed to delete backup {backup_id}: {e}")
            return False
            
    def _auto_backup_worker(self, source_directories: List[str]):
        """自動バックアップワーカー"""
        print("Auto backup worker started")
        
        while self.is_running:
            try:
                for source_dir in source_directories:
                    if not self.is_running:
                        break
                        
                    # ディレクトリ存在確認
                    if not os.path.exists(source_dir):
                        continue
                        
                    # 変更検知
                    if self._has_directory_changes(source_dir):
                        # 非同期バックアップ実行
                        future = self.executor.submit(
                            self._create_scheduled_backup, source_dir
                        )
                        # エラーハンドリング
                        future.add_done_callback(self._handle_backup_result)
                        
                # インターバル待機
                time.sleep(self.backup_interval)
                
            except Exception as e:
                print(f"Auto backup worker error: {e}")
                time.sleep(30)  # エラー時は30秒待機
                
        print("Auto backup worker stopped")
        
    def _create_scheduled_backup(self, source_path: str) -> BackupInfo:
        """スケジュールバックアップ作成"""
        try:
            return self.create_backup(source_path, backup_type="incremental")
        except Exception as e:
            print(f"Scheduled backup failed for {source_path}: {e}")
            raise
            
    def _handle_backup_result(self, future):
        """バックアップ結果処理"""
        try:
            backup_info = future.result()
            print(f"Scheduled backup completed: {backup_info.backup_id}")
        except Exception as e:
            print(f"Scheduled backup failed: {e}")
            
    def _create_full_backup(self, source_path: str, backup_path: str) -> tuple:
        """フルバックアップ作成"""
        if os.path.isfile(source_path):
            # 単一ファイル
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(source_path, backup_path)
            return 1, os.path.getsize(backup_path)
        else:
            # ディレクトリ
            shutil.copytree(source_path, backup_path)
            return self._count_files_and_size(backup_path)
            
    def _create_incremental_backup(self, source_path: str, backup_path: str) -> tuple:
        """増分バックアップ作成（前回バックアップ以降の変更）"""
        last_backup_time = self.last_backup_time.get(source_path, 0)
        
        file_count = 0
        total_size = 0
        
        # 変更されたファイルのみコピー
        for root, dirs, files in os.walk(source_path):
            for file in files:
                source_file = os.path.join(root, file)
                file_mtime = os.path.getmtime(source_file)
                
                # 変更時刻チェック
                if file_mtime > last_backup_time:
                    # 相対パス計算
                    rel_path = os.path.relpath(source_file, source_path)
                    backup_file = os.path.join(backup_path, rel_path)
                    
                    # ディレクトリ作成
                    os.makedirs(os.path.dirname(backup_file), exist_ok=True)
                    
                    # ファイルコピー
                    shutil.copy2(source_file, backup_file)
                    
                    file_count += 1
                    total_size += os.path.getsize(backup_file)
                    
        # バックアップ時刻更新
        self.last_backup_time[source_path] = time.time()
        
        return file_count, total_size
        
    def _create_differential_backup(self, source_path: str, backup_path: str) -> tuple:
        """差分バックアップ作成（初回フルバックアップ以降の変更）"""
        # 初回フルバックアップ検索
        full_backups = [b for b in self.backup_history 
                       if b.source_path == source_path and b.backup_type == "full"]
        
        if not full_backups:
            # フルバックアップなし → フルバックアップ作成
            return self._create_full_backup(source_path, backup_path)
            
        # 最新のフルバックアップ以降の変更
        latest_full = max(full_backups, key=lambda x: x.created_at)
        base_time = latest_full.created_at.timestamp()
        
        file_count = 0
        total_size = 0
        
        for root, dirs, files in os.walk(source_path):
            for file in files:
                source_file = os.path.join(root, file)
                file_mtime = os.path.getmtime(source_file)
                
                if file_mtime > base_time:
                    rel_path = os.path.relpath(source_file, source_path)
                    backup_file = os.path.join(backup_path, rel_path)
                    
                    os.makedirs(os.path.dirname(backup_file), exist_ok=True)
                    shutil.copy2(source_file, backup_file)
                    
                    file_count += 1
                    total_size += os.path.getsize(backup_file)
                    
        return file_count, total_size
        
    def _compress_backup(self, backup_path: str, compressed_path: str):
        """バックアップ圧縮"""
        with zipfile.ZipFile(compressed_path, 'w', 
                           compression=zipfile.ZIP_DEFLATED,
                           compresslevel=self.compression_level) as zipf:
            
            if os.path.isfile(backup_path):
                # 単一ファイル
                zipf.write(backup_path, os.path.basename(backup_path))
            else:
                # ディレクトリ
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
                        
    def _cleanup_old_backups(self):
        """古いバックアップ削除"""
        if len(self.backup_history) <= self.max_backup_generations:
            return
            
        # 作成日時順でソート
        sorted_backups = sorted(self.backup_history, key=lambda x: x.created_at)
        
        # 古いバックアップ削除
        backups_to_delete = sorted_backups[:-self.max_backup_generations]
        
        for backup in backups_to_delete:
            self.delete_backup(backup.backup_id)
            
    def _has_directory_changes(self, directory: str) -> bool:
        """ディレクトリ変更検知"""
        last_backup = self.last_backup_time.get(directory, 0)
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) > last_backup:
                    return True
                    
        return False
        
    def _count_files_and_size(self, path: str) -> tuple:
        """ファイル数・サイズカウント"""
        file_count = 0
        total_size = 0
        
        if os.path.isfile(path):
            return 1, os.path.getsize(path)
            
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                file_count += 1
                total_size += os.path.getsize(file_path)
                
        return file_count, total_size
        
    def _copy_tree_no_overwrite(self, src: str, dst: str):
        """上書きなしツリーコピー"""
        for root, dirs, files in os.walk(src):
            # 相対パス計算
            rel_root = os.path.relpath(root, src)
            dst_root = os.path.join(dst, rel_root) if rel_root != '.' else dst
            
            # ディレクトリ作成
            os.makedirs(dst_root, exist_ok=True)
            
            # ファイルコピー
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_root, file)
                
                if not os.path.exists(dst_file):
                    shutil.copy2(src_file, dst_file)
                    
    def _save_backup_history(self):
        """バックアップ履歴保存"""
        history_file = os.path.join(self.backup_root_dir, "backup_history.json")
        
        try:
            history_data = []
            for backup in self.backup_history:
                data = {
                    "backup_id": backup.backup_id,
                    "backup_path": backup.backup_path,
                    "created_at": backup.created_at.isoformat(),
                    "source_path": backup.source_path,
                    "backup_type": backup.backup_type,
                    "compressed": backup.compressed,
                    "size_bytes": backup.size_bytes,
                    "file_count": backup.file_count,
                    "description": backup.description
                }
                history_data.append(data)
                
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Failed to save backup history: {e}")
            
    def _load_backup_history(self):
        """バックアップ履歴読み込み"""
        history_file = os.path.join(self.backup_root_dir, "backup_history.json")
        
        if not os.path.exists(history_file):
            return
            
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                
            self.backup_history = []
            for data in history_data:
                backup_info = BackupInfo(
                    backup_id=data["backup_id"],
                    backup_path=data["backup_path"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    source_path=data["source_path"],
                    backup_type=data["backup_type"],
                    compressed=data["compressed"],
                    size_bytes=data["size_bytes"],
                    file_count=data["file_count"],
                    description=data.get("description", "")
                )
                self.backup_history.append(backup_info)
                
        except Exception as e:
            print(f"Failed to load backup history: {e}")
            self.backup_history = []