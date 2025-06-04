"""
復旧システム
バックアップからの高速復旧・整合性検証・復旧戦略
"""

import os
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .backup_manager import BackupManager, BackupInfo
from ..file_io.txt_handler import YOLOTxtHandler
from ..file_io.json_handler import JSONHandler
from ..exceptions import BackupError, ValidationError


@dataclass
class RecoveryPlan:
    """復旧計画"""
    recovery_id: str
    target_path: str
    backup_sequence: List[BackupInfo]  # 復旧順序
    recovery_type: str  # full/partial/incremental
    estimated_time: float  # 推定時間（秒）
    file_count: int
    total_size: int
    validation_required: bool = True


@dataclass
class RecoveryResult:
    """復旧結果"""
    recovery_id: str
    success: bool
    recovered_files: int
    failed_files: int
    elapsed_time: float
    validation_passed: bool
    error_message: Optional[str] = None


class RecoverySystem:
    """
    復旧システム
    
    機能:
    - バックアップからの高速復旧
    - 増分復旧（複数バックアップ統合）
    - データ整合性検証
    - 復旧戦略自動選択
    - 復旧進捗監視
    """
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.txt_handler = YOLOTxtHandler()
        self.json_handler = JSONHandler()
        
        # 復旧履歴
        self.recovery_history: List[RecoveryResult] = []
        
    def analyze_recovery_options(self, target_path: str,
                                point_in_time: Optional[datetime] = None) -> List[RecoveryPlan]:
        """
        復旧オプション分析
        
        Args:
            target_path: 復旧対象パス
            point_in_time: 復旧時点（None=最新）
            
        Returns:
            List[RecoveryPlan]: 復旧計画リスト（推奨順）
        """
        available_backups = self.backup_manager.list_available_backups(source_path=target_path)
        
        if not available_backups:
            return []
            
        # 時点指定フィルター
        if point_in_time:
            available_backups = [
                b for b in available_backups 
                if b.created_at <= point_in_time
            ]
            
        recovery_plans = []
        
        # 1. フル復旧プラン（最新フルバックアップ）
        full_backups = [b for b in available_backups if b.backup_type == "full"]
        if full_backups:
            latest_full = max(full_backups, key=lambda x: x.created_at)
            
            plan = RecoveryPlan(
                recovery_id=f"full_{int(time.time())}",
                target_path=target_path,
                backup_sequence=[latest_full],
                recovery_type="full",
                estimated_time=self._estimate_recovery_time(latest_full.size_bytes),
                file_count=latest_full.file_count,
                total_size=latest_full.size_bytes
            )
            recovery_plans.append(plan)
            
        # 2. 増分復旧プラン（フル + 増分バックアップ）
        if full_backups:
            latest_full = max(full_backups, key=lambda x: x.created_at)
            
            # フル以降の増分バックアップ
            incremental_backups = [
                b for b in available_backups
                if b.backup_type == "incremental" and b.created_at > latest_full.created_at
            ]
            
            if incremental_backups:
                # 時系列順ソート
                incremental_backups.sort(key=lambda x: x.created_at)
                backup_sequence = [latest_full] + incremental_backups
                
                total_size = sum(b.size_bytes for b in backup_sequence)
                total_files = sum(b.file_count for b in backup_sequence)
                
                plan = RecoveryPlan(
                    recovery_id=f"incremental_{int(time.time())}",
                    target_path=target_path,
                    backup_sequence=backup_sequence,
                    recovery_type="incremental",
                    estimated_time=self._estimate_recovery_time(total_size) * 1.2,  # オーバーヘッド
                    file_count=total_files,
                    total_size=total_size
                )
                recovery_plans.append(plan)
                
        # 3. 差分復旧プラン（フル + 最新差分）
        differential_backups = [b for b in available_backups if b.backup_type == "differential"]
        if full_backups and differential_backups:
            latest_full = max(full_backups, key=lambda x: x.created_at)
            latest_diff = max(differential_backups, key=lambda x: x.created_at)
            
            backup_sequence = [latest_full, latest_diff]
            total_size = latest_full.size_bytes + latest_diff.size_bytes
            total_files = latest_full.file_count + latest_diff.file_count
            
            plan = RecoveryPlan(
                recovery_id=f"differential_{int(time.time())}",
                target_path=target_path,
                backup_sequence=backup_sequence,
                recovery_type="differential",
                estimated_time=self._estimate_recovery_time(total_size) * 1.1,
                file_count=total_files,
                total_size=total_size
            )
            recovery_plans.append(plan)
            
        # 推奨順ソート（推定時間 + 完全性）
        recovery_plans.sort(key=lambda x: (x.estimated_time, -x.file_count))
        
        return recovery_plans
        
    def execute_recovery(self, recovery_plan: RecoveryPlan,
                        overwrite: bool = True,
                        validate_data: bool = True) -> RecoveryResult:
        """
        復旧実行
        
        Args:
            recovery_plan: 復旧計画
            overwrite: 既存ファイル上書き
            validate_data: データ検証実行
            
        Returns:
            RecoveryResult: 復旧結果
        """
        start_time = time.perf_counter()
        
        try:
            print(f"Starting recovery: {recovery_plan.recovery_id}")
            
            # 復旧先ディレクトリ準備
            os.makedirs(recovery_plan.target_path, exist_ok=True)
            
            recovered_files = 0
            failed_files = 0
            
            # バックアップ順序で復旧
            for i, backup_info in enumerate(recovery_plan.backup_sequence):
                print(f"Restoring backup {i+1}/{len(recovery_plan.backup_sequence)}: {backup_info.backup_id}")
                
                try:
                    # バックアップ復旧
                    success = self.backup_manager.restore_backup(
                        backup_info, 
                        recovery_plan.target_path,
                        overwrite=overwrite
                    )
                    
                    if success:
                        recovered_files += backup_info.file_count
                    else:
                        failed_files += backup_info.file_count
                        
                except Exception as e:
                    print(f"Backup restoration failed: {backup_info.backup_id}, {e}")
                    failed_files += backup_info.file_count
                    
            # データ検証
            validation_passed = True
            if validate_data and recovered_files > 0:
                validation_passed = self._validate_recovered_data(recovery_plan.target_path)
                
            elapsed_time = time.perf_counter() - start_time
            success = failed_files == 0 and validation_passed
            
            result = RecoveryResult(
                recovery_id=recovery_plan.recovery_id,
                success=success,
                recovered_files=recovered_files,
                failed_files=failed_files,
                elapsed_time=elapsed_time,
                validation_passed=validation_passed
            )
            
            # 復旧履歴に追加
            self.recovery_history.append(result)
            
            print(f"Recovery completed: {recovery_plan.recovery_id}, "
                  f"success={success}, files={recovered_files}, time={elapsed_time:.2f}s")
            
            return result
            
        except Exception as e:
            elapsed_time = time.perf_counter() - start_time
            
            result = RecoveryResult(
                recovery_id=recovery_plan.recovery_id,
                success=False,
                recovered_files=0,
                failed_files=recovery_plan.file_count,
                elapsed_time=elapsed_time,
                validation_passed=False,
                error_message=str(e)
            )
            
            self.recovery_history.append(result)
            raise BackupError(f"Recovery failed: {e}")
            
    def quick_recovery(self, target_path: str, 
                      strategy: str = "auto") -> RecoveryResult:
        """
        高速復旧（自動戦略選択）
        
        Args:
            target_path: 復旧対象パス
            strategy: auto/fastest/safest
            
        Returns:
            RecoveryResult: 復旧結果
        """
        # 復旧プラン分析
        recovery_plans = self.analyze_recovery_options(target_path)
        
        if not recovery_plans:
            raise BackupError(f"No recovery options available for {target_path}")
            
        # 戦略別プラン選択
        if strategy == "fastest":
            # 最速（推定時間最小）
            selected_plan = min(recovery_plans, key=lambda x: x.estimated_time)
        elif strategy == "safest":
            # 最安全（ファイル数最大）
            selected_plan = max(recovery_plans, key=lambda x: x.file_count)
        else:  # auto
            # バランス（最初の推奨プラン）
            selected_plan = recovery_plans[0]
            
        print(f"Selected recovery strategy: {strategy}, plan: {selected_plan.recovery_type}")
        
        # 復旧実行
        return self.execute_recovery(selected_plan)
        
    def validate_backup_integrity(self, backup_info: BackupInfo) -> bool:
        """バックアップ整合性検証"""
        try:
            if not os.path.exists(backup_info.backup_path):
                return False
                
            # ファイルサイズチェック
            actual_size = os.path.getsize(backup_info.backup_path)
            if abs(actual_size - backup_info.size_bytes) > 1024:  # 1KB許容差
                return False
                
            # 圧縮ファイルの場合は展開テスト
            if backup_info.compressed and backup_info.backup_path.endswith('.zip'):
                import zipfile
                try:
                    with zipfile.ZipFile(backup_info.backup_path, 'r') as zipf:
                        # テスト展開（実際には展開しない）
                        zipf.testzip()
                        return True
                except zipfile.BadZipFile:
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Backup integrity validation failed: {backup_info.backup_id}, {e}")
            return False
            
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """復旧統計情報"""
        if not self.recovery_history:
            return {"total_recoveries": 0}
            
        total_recoveries = len(self.recovery_history)
        successful_recoveries = sum(1 for r in self.recovery_history if r.success)
        total_files_recovered = sum(r.recovered_files for r in self.recovery_history)
        
        average_time = sum(r.elapsed_time for r in self.recovery_history) / total_recoveries
        
        latest_recovery = max(self.recovery_history, key=lambda x: x.recovery_id)
        
        return {
            "total_recoveries": total_recoveries,
            "successful_recoveries": successful_recoveries,
            "success_rate": successful_recoveries / total_recoveries * 100,
            "total_files_recovered": total_files_recovered,
            "average_recovery_time": average_time,
            "latest_recovery": {
                "recovery_id": latest_recovery.recovery_id,
                "success": latest_recovery.success,
                "elapsed_time": latest_recovery.elapsed_time
            }
        }
        
    def _estimate_recovery_time(self, size_bytes: int) -> float:
        """復旧時間推定（秒）"""
        # SSD想定: 500MB/s読み込み
        base_speed = 500 * 1024 * 1024  # bytes/sec
        
        # オーバーヘッド考慮
        overhead_factor = 1.5
        
        return (size_bytes / base_speed) * overhead_factor
        
    def _validate_recovered_data(self, target_path: str) -> bool:
        """復旧データ検証"""
        try:
            validation_errors = 0
            total_files = 0
            
            # アノテーションファイル検証
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_files += 1
                    
                    try:
                        if file.endswith('.txt'):
                            # YOLO形式検証
                            frame_id = os.path.splitext(file)[0]
                            bb_entities = self.txt_handler.load_annotations(frame_id, root)
                            # 読み込み成功 = 検証OK
                            
                        elif file.endswith('.json'):
                            # JSON形式検証
                            if not self.json_handler.validate_json_file(file_path):
                                validation_errors += 1
                                
                    except Exception as e:
                        print(f"Validation error for {file_path}: {e}")
                        validation_errors += 1
                        
            # 検証結果判定
            if total_files == 0:
                return True  # ファイルなし = OK
                
            error_rate = validation_errors / total_files
            return error_rate < 0.05  # エラー率5%未満でOK
            
        except Exception as e:
            print(f"Data validation failed: {e}")
            return False