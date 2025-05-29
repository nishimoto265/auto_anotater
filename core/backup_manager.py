"""
バックアップ管理システム
アノテーションデータ、設定ファイル、作業セッションの完全バックアップ機能を提供
"""

import os
import json
import shutil
import zipfile
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable, Tuple
from dataclasses import dataclass, asdict
import time
import schedule

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """バックアップメタデータ"""
    version: str = "1.0.0"
    created_at: str = ""
    backup_type: str = "full"  # full, incremental, differential
    source_directory: str = ""
    annotation_count: int = 0
    config_included: bool = True
    session_included: bool = True
    description: str = ""
    compression_level: int = 6
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)


@dataclass
class BackupOptions:
    """バックアップオプション"""
    include_annotations: bool = True
    include_config: bool = True
    include_session: bool = True
    compression_level: int = 6  # 0-9 (0=no compression, 9=max)
    verify_after_backup: bool = True
    max_backups_to_keep: int = 10
    backup_prefix: str = "backup"
    include_logs: bool = False


@dataclass
class RestoreOptions:
    """復元オプション"""
    restore_annotations: bool = True
    restore_config: bool = True
    restore_session: bool = True
    overwrite_existing: bool = False
    create_restore_point: bool = True  # 復元前に現在の状態をバックアップ


class BackupManager:
    """バックアップ管理クラス"""
    
    def __init__(self, 
                 project_root: str,
                 annotations_dir: str,
                 config_path: str,
                 backup_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            project_root: プロジェクトルートディレクトリ
            annotations_dir: アノテーションファイルのディレクトリ
            config_path: 設定ファイルのパス
            backup_dir: バックアップ保存先ディレクトリ（Noneの場合はproject_root/backups）
        """
        self.project_root = Path(project_root)
        self.annotations_dir = Path(annotations_dir)
        self.config_path = Path(config_path)
        
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = self.project_root / "backups"
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 自動バックアップ用
        self._scheduler_thread: Optional[threading.Thread] = None
        self._scheduler_running = False
        self._schedule_lock = threading.Lock()
        
        # 進捗コールバック
        self._progress_callback: Optional[Callable[[str, float], None]] = None
        
        logger.info(f"BackupManager initialized with backup_dir: {self.backup_dir}")
    
    def set_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """進捗コールバックを設定"""
        self._progress_callback = callback
    
    def _report_progress(self, message: str, progress: float) -> None:
        """進捗を報告"""
        if self._progress_callback:
            self._progress_callback(message, progress)
        logger.debug(f"Backup progress: {message} ({progress:.1f}%)")
    
    def create_backup(self, 
                     options: Optional[BackupOptions] = None,
                     description: str = "") -> Tuple[bool, str]:
        """
        完全バックアップを作成
        
        Args:
            options: バックアップオプション
            description: バックアップの説明
            
        Returns:
            (成功フラグ, バックアップファイルパスまたはエラーメッセージ)
        """
        if options is None:
            options = BackupOptions()
        
        try:
            # バックアップファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{options.backup_prefix}_{timestamp}.zip"
            backup_path = self.backup_dir / backup_filename
            
            self._report_progress("バックアップを開始しています...", 0)
            
            # メタデータを準備
            metadata = BackupMetadata(
                created_at=datetime.now().isoformat(),
                source_directory=str(self.project_root),
                description=description,
                compression_level=options.compression_level
            )
            
            # ZIPファイルを作成
            with zipfile.ZipFile(backup_path, 'w', 
                               compression=zipfile.ZIP_DEFLATED,
                               compresslevel=options.compression_level) as zipf:
                
                total_steps = sum([
                    options.include_annotations,
                    options.include_config,
                    options.include_session,
                    options.include_logs
                ]) + 2  # メタデータとverifyで+2
                current_step = 0
                
                # アノテーションデータをバックアップ
                if options.include_annotations:
                    self._report_progress("アノテーションデータをバックアップ中...", 
                                        (current_step / total_steps) * 100)
                    annotation_count = self._backup_annotations(zipf)
                    metadata.annotation_count = annotation_count
                    current_step += 1
                
                # 設定ファイルをバックアップ
                if options.include_config:
                    self._report_progress("設定ファイルをバックアップ中...", 
                                        (current_step / total_steps) * 100)
                    self._backup_config(zipf)
                    metadata.config_included = True
                    current_step += 1
                
                # セッション情報をバックアップ
                if options.include_session:
                    self._report_progress("セッション情報をバックアップ中...", 
                                        (current_step / total_steps) * 100)
                    self._backup_session(zipf)
                    metadata.session_included = True
                    current_step += 1
                
                # ログファイルをバックアップ（オプション）
                if options.include_logs:
                    self._report_progress("ログファイルをバックアップ中...", 
                                        (current_step / total_steps) * 100)
                    self._backup_logs(zipf)
                    current_step += 1
                
                # メタデータを保存
                self._report_progress("メタデータを保存中...", 
                                    (current_step / total_steps) * 100)
                zipf.writestr("metadata.json", 
                            json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2))
                current_step += 1
            
            # バックアップの検証
            if options.verify_after_backup:
                self._report_progress("バックアップを検証中...", 
                                    (current_step / total_steps) * 100)
                if not self._verify_backup(backup_path):
                    raise Exception("バックアップの検証に失敗しました")
            
            # 古いバックアップを削除
            if options.max_backups_to_keep > 0:
                self._cleanup_old_backups(options.max_backups_to_keep, options.backup_prefix)
            
            self._report_progress("バックアップが完了しました", 100)
            logger.info(f"Backup created successfully: {backup_path}")
            return True, str(backup_path)
            
        except Exception as e:
            error_msg = f"バックアップの作成に失敗しました: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def _backup_annotations(self, zipf: zipfile.ZipFile) -> int:
        """アノテーションデータをバックアップ"""
        count = 0
        if self.annotations_dir.exists():
            for ann_file in self.annotations_dir.glob("*.txt"):
                if ann_file.stat().st_size > 0:  # 空でないファイルのみ
                    arcname = f"annotations/{ann_file.name}"
                    zipf.write(ann_file, arcname)
                    count += 1
        return count
    
    def _backup_config(self, zipf: zipfile.ZipFile) -> None:
        """設定ファイルをバックアップ"""
        if self.config_path.exists():
            zipf.write(self.config_path, f"config/{self.config_path.name}")
            
            # バックアップファイルも含める
            backup_path = Path(str(self.config_path) + ".bak")
            if backup_path.exists():
                zipf.write(backup_path, f"config/{backup_path.name}")
    
    def _backup_session(self, zipf: zipfile.ZipFile) -> None:
        """セッション情報をバックアップ"""
        # プログレストラッカーのチェックポイントファイルを探す
        checkpoint_dir = self.project_root / "checkpoints"
        if checkpoint_dir.exists():
            for checkpoint_file in checkpoint_dir.glob("*.json"):
                arcname = f"session/checkpoints/{checkpoint_file.name}"
                zipf.write(checkpoint_file, arcname)
        
        # 現在の作業状態を保存
        session_info = {
            "backup_time": datetime.now().isoformat(),
            "working_directory": str(self.annotations_dir),
            "config_path": str(self.config_path)
        }
        zipf.writestr("session/session_info.json", 
                     json.dumps(session_info, ensure_ascii=False, indent=2))
    
    def _backup_logs(self, zipf: zipfile.ZipFile) -> None:
        """ログファイルをバックアップ"""
        log_dir = self.project_root / "logs"
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                # 最新の1MBまでを保存
                if log_file.stat().st_size > 1024 * 1024:
                    with open(log_file, 'rb') as f:
                        f.seek(-1024 * 1024, 2)  # 末尾から1MB
                        content = f.read()
                    zipf.writestr(f"logs/{log_file.name}", content)
                else:
                    zipf.write(log_file, f"logs/{log_file.name}")
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """バックアップファイルを検証"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # 破損チェック
                bad_file = zipf.testzip()
                if bad_file:
                    logger.error(f"Corrupted file in backup: {bad_file}")
                    return False
                
                # メタデータの存在確認
                if "metadata.json" not in zipf.namelist():
                    logger.error("Metadata not found in backup")
                    return False
                
                return True
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def _cleanup_old_backups(self, max_backups: int, prefix: str) -> None:
        """古いバックアップを削除"""
        backup_files = sorted([
            f for f in self.backup_dir.glob(f"{prefix}_*.zip")
        ], key=lambda x: x.stat().st_mtime, reverse=True)
        
        for old_backup in backup_files[max_backups:]:
            try:
                old_backup.unlink()
                logger.info(f"Deleted old backup: {old_backup}")
            except Exception as e:
                logger.error(f"Failed to delete old backup {old_backup}: {e}")
    
    def restore_backup(self, 
                      backup_path: str,
                      options: Optional[RestoreOptions] = None) -> Tuple[bool, str]:
        """
        バックアップから復元
        
        Args:
            backup_path: バックアップファイルのパス
            options: 復元オプション
            
        Returns:
            (成功フラグ, メッセージ)
        """
        if options is None:
            options = RestoreOptions()
        
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                return False, f"バックアップファイルが見つかりません: {backup_path}"
            
            self._report_progress("バックアップの復元を開始しています...", 0)
            
            # 復元前に現在の状態をバックアップ
            if options.create_restore_point:
                self._report_progress("復元ポイントを作成中...", 10)
                success, restore_point = self.create_backup(
                    options=BackupOptions(backup_prefix="restore_point"),
                    description="自動復元ポイント"
                )
                if success:
                    logger.info(f"Restore point created: {restore_point}")
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # メタデータを読み込む
                try:
                    metadata_json = zipf.read("metadata.json").decode('utf-8')
                    metadata = json.loads(metadata_json)
                except KeyError:
                    return False, "バックアップファイルにメタデータが含まれていません"
                
                total_steps = sum([
                    options.restore_annotations and metadata.get('annotation_count', 0) > 0,
                    options.restore_config and metadata.get('config_included', False),
                    options.restore_session and metadata.get('session_included', False)
                ])
                current_step = 0
                
                # アノテーションデータを復元
                if options.restore_annotations and metadata.get('annotation_count', 0) > 0:
                    self._report_progress("アノテーションデータを復元中...", 
                                        (current_step / total_steps) * 80 + 20)
                    self._restore_annotations(zipf, options.overwrite_existing)
                    current_step += 1
                
                # 設定ファイルを復元
                if options.restore_config and metadata.get('config_included', False):
                    self._report_progress("設定ファイルを復元中...", 
                                        (current_step / total_steps) * 80 + 20)
                    self._restore_config(zipf, options.overwrite_existing)
                    current_step += 1
                
                # セッション情報を復元
                if options.restore_session and metadata.get('session_included', False):
                    self._report_progress("セッション情報を復元中...", 
                                        (current_step / total_steps) * 80 + 20)
                    self._restore_session(zipf, options.overwrite_existing)
                    current_step += 1
            
            self._report_progress("復元が完了しました", 100)
            return True, f"バックアップの復元が完了しました: {backup_path}"
            
        except Exception as e:
            error_msg = f"バックアップの復元に失敗しました: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def _restore_annotations(self, zipf: zipfile.ZipFile, overwrite: bool) -> None:
        """アノテーションデータを復元"""
        for file_info in zipf.filelist:
            if file_info.filename.startswith("annotations/") and not file_info.is_dir():
                target_path = self.annotations_dir / Path(file_info.filename).name
                
                if target_path.exists() and not overwrite:
                    # 既存ファイルをバックアップ
                    backup_path = target_path.with_suffix(target_path.suffix + '.restore_bak')
                    shutil.copy2(target_path, backup_path)
                
                # ファイルを抽出
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, 'wb') as f:
                    f.write(zipf.read(file_info.filename))
    
    def _restore_config(self, zipf: zipfile.ZipFile, overwrite: bool) -> None:
        """設定ファイルを復元"""
        for file_info in zipf.filelist:
            if file_info.filename.startswith("config/") and not file_info.is_dir():
                if self.config_path.name in file_info.filename:
                    if self.config_path.exists() and not overwrite:
                        # 既存ファイルをバックアップ
                        backup_path = self.config_path.with_suffix('.restore_bak')
                        shutil.copy2(self.config_path, backup_path)
                    
                    # ファイルを抽出
                    with open(self.config_path, 'wb') as f:
                        f.write(zipf.read(file_info.filename))
    
    def _restore_session(self, zipf: zipfile.ZipFile, overwrite: bool) -> None:
        """セッション情報を復元"""
        checkpoint_dir = self.project_root / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        for file_info in zipf.filelist:
            if file_info.filename.startswith("session/checkpoints/") and not file_info.is_dir():
                target_path = checkpoint_dir / Path(file_info.filename).name
                
                if target_path.exists() and not overwrite:
                    # 既存ファイルをバックアップ
                    backup_path = target_path.with_suffix('.restore_bak')
                    shutil.copy2(target_path, backup_path)
                
                # ファイルを抽出
                with open(target_path, 'wb') as f:
                    f.write(zipf.read(file_info.filename))
    
    def list_backups(self, prefix: str = "backup") -> List[Dict[str, Any]]:
        """
        利用可能なバックアップのリストを取得
        
        Returns:
            バックアップ情報のリスト
        """
        backups = []
        
        for backup_file in self.backup_dir.glob(f"{prefix}_*.zip"):
            try:
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if "metadata.json" in zipf.namelist():
                        metadata = json.loads(zipf.read("metadata.json").decode('utf-8'))
                        file_stat = backup_file.stat()
                        backups.append({
                            "path": str(backup_file),
                            "filename": backup_file.name,
                            "size": file_stat.st_size,
                            "created_at": metadata.get("created_at", ""),
                            "annotation_count": metadata.get("annotation_count", 0),
                            "description": metadata.get("description", ""),
                            "backup_type": metadata.get("backup_type", "full")
                        })
            except Exception as e:
                logger.warning(f"Failed to read backup metadata from {backup_file}: {e}")
        
        # 作成日時でソート（新しい順）
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def get_backup_info(self, backup_path: str) -> Optional[Dict[str, Any]]:
        """
        バックアップファイルの詳細情報を取得
        
        Args:
            backup_path: バックアップファイルのパス
            
        Returns:
            バックアップ情報の辞書、または None
        """
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                return None
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # ファイルリストを取得
                file_list = zipf.namelist()
                
                # メタデータを読み込む
                metadata = {}
                if "metadata.json" in file_list:
                    metadata = json.loads(zipf.read("metadata.json").decode('utf-8'))
                
                # ファイル統計を計算
                annotation_files = [f for f in file_list if f.startswith("annotations/")]
                config_files = [f for f in file_list if f.startswith("config/")]
                session_files = [f for f in file_list if f.startswith("session/")]
                log_files = [f for f in file_list if f.startswith("logs/")]
                
                return {
                    "path": str(backup_path),
                    "filename": backup_path.name,
                    "size": backup_path.stat().st_size,
                    "metadata": metadata,
                    "file_count": len(file_list),
                    "annotation_files": len(annotation_files),
                    "config_files": len(config_files),
                    "session_files": len(session_files),
                    "log_files": len(log_files),
                    "compression_info": zipf.compression
                }
                
        except Exception as e:
            logger.error(f"Failed to get backup info: {e}")
            return None
    
    def start_auto_backup(self, 
                         interval_minutes: int = 30,
                         options: Optional[BackupOptions] = None) -> None:
        """
        自動バックアップを開始
        
        Args:
            interval_minutes: バックアップ間隔（分）
            options: バックアップオプション
        """
        if self._scheduler_running:
            logger.warning("Auto backup is already running")
            return
        
        if options is None:
            options = BackupOptions()
        
        # スケジュールを設定
        schedule.every(interval_minutes).minutes.do(
            lambda: self.create_backup(options, f"自動バックアップ ({interval_minutes}分間隔)")
        )
        
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()
        
        logger.info(f"Auto backup started with {interval_minutes} minutes interval")
    
    def stop_auto_backup(self) -> None:
        """自動バックアップを停止"""
        with self._schedule_lock:
            self._scheduler_running = False
            schedule.clear()
        
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5)
        
        logger.info("Auto backup stopped")
    
    def _run_scheduler(self) -> None:
        """スケジューラーを実行"""
        while self._scheduler_running:
            with self._schedule_lock:
                schedule.run_pending()
            time.sleep(1)
    
    def schedule_daily_backup(self, 
                            time_str: str = "02:00",
                            options: Optional[BackupOptions] = None) -> None:
        """
        毎日定時バックアップを設定
        
        Args:
            time_str: バックアップ時刻（HH:MM形式）
            options: バックアップオプション
        """
        if options is None:
            options = BackupOptions()
        
        schedule.every().day.at(time_str).do(
            lambda: self.create_backup(options, f"定時バックアップ ({time_str})")
        )
        
        if not self._scheduler_running:
            self._scheduler_running = True
            self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self._scheduler_thread.start()
        
        logger.info(f"Daily backup scheduled at {time_str}")
    
    def create_incremental_backup(self, 
                                last_backup_path: str,
                                options: Optional[BackupOptions] = None) -> Tuple[bool, str]:
        """
        差分バックアップを作成（未実装のプレースホルダー）
        
        Args:
            last_backup_path: 前回のバックアップファイルパス
            options: バックアップオプション
            
        Returns:
            (成功フラグ, バックアップファイルパスまたはエラーメッセージ)
        """
        # TODO: 差分バックアップの実装
        # - 前回のバックアップ以降に変更されたファイルのみを保存
        # - メタデータに前回のバックアップへの参照を含める
        logger.warning("Incremental backup is not implemented yet, creating full backup instead")
        return self.create_backup(options, "差分バックアップ（フル）")