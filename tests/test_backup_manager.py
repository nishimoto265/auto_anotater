"""
バックアップマネージャーのテスト
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backup_manager import BackupManager, BackupOptions, RestoreOptions


def test_backup_manager():
    """バックアップマネージャーの基本機能をテスト"""
    
    # テスト用の一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # テスト用のディレクトリ構造を作成
        project_root = temp_path / "test_project"
        annotations_dir = project_root / "annotations"
        config_path = project_root / "config" / "app_config.json"
        backup_dir = project_root / "backups"
        checkpoint_dir = project_root / "checkpoints"
        
        # ディレクトリを作成
        annotations_dir.mkdir(parents=True)
        config_path.parent.mkdir(parents=True)
        checkpoint_dir.mkdir(parents=True)
        
        # テストデータを作成
        # アノテーションファイル
        for i in range(5):
            ann_file = annotations_dir / f"{i:06d}.txt"
            ann_file.write_text(f"0 0.5 0.5 0.1 0.1 1 0.95\n1 0.3 0.3 0.2 0.2 2 0.88\n")
        
        # 設定ファイル
        config_data = {
            "individual_ids": {
                "0": {"name": "Person 1", "color": "#FF0000"},
                "1": {"name": "Person 2", "color": "#00FF00"}
            },
            "action_ids": {
                "1": {"name": "Walking", "color": "#0000FF"},
                "2": {"name": "Running", "color": "#FFFF00"}
            }
        }
        config_path.write_text(json.dumps(config_data, indent=2))
        
        # チェックポイントファイル
        checkpoint_file = checkpoint_dir / "checkpoint_20240101_120000.json"
        checkpoint_data = {
            "timestamp": "2024-01-01T12:00:00",
            "frames_processed": 100,
            "total_frames": 1000
        }
        checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2))
        
        # バックアップマネージャーを初期化
        backup_manager = BackupManager(
            project_root=str(project_root),
            annotations_dir=str(annotations_dir),
            config_path=str(config_path),
            backup_dir=str(backup_dir)
        )
        
        print("=== バックアップマネージャーのテスト ===")
        
        # 1. 完全バックアップの作成
        print("\n1. 完全バックアップを作成中...")
        options = BackupOptions(
            include_annotations=True,
            include_config=True,
            include_session=True,
            compression_level=6,
            verify_after_backup=True,
            max_backups_to_keep=3
        )
        
        success, backup_path = backup_manager.create_backup(
            options=options,
            description="テスト用バックアップ"
        )
        
        if success:
            print(f"✓ バックアップ作成成功: {backup_path}")
            print(f"  ファイルサイズ: {Path(backup_path).stat().st_size:,} bytes")
        else:
            print(f"✗ バックアップ作成失敗: {backup_path}")
            return
        
        # 2. バックアップの情報を取得
        print("\n2. バックアップ情報を取得中...")
        backup_info = backup_manager.get_backup_info(backup_path)
        if backup_info:
            print(f"✓ バックアップ情報:")
            print(f"  - ファイル数: {backup_info['file_count']}")
            print(f"  - アノテーション: {backup_info['annotation_files']} ファイル")
            print(f"  - 設定: {backup_info['config_files']} ファイル")
            print(f"  - セッション: {backup_info['session_files']} ファイル")
        
        # 3. バックアップリストの取得
        print("\n3. バックアップリストを取得中...")
        backups = backup_manager.list_backups()
        print(f"✓ 利用可能なバックアップ: {len(backups)} 個")
        for backup in backups:
            print(f"  - {backup['filename']} ({backup['size']:,} bytes)")
        
        # 4. 復元テスト
        print("\n4. バックアップから復元中...")
        
        # 元のファイルを削除
        shutil.rmtree(annotations_dir)
        config_path.unlink()
        
        # 復元
        restore_options = RestoreOptions(
            restore_annotations=True,
            restore_config=True,
            restore_session=True,
            overwrite_existing=True,
            create_restore_point=False  # テストでは復元ポイントは作成しない
        )
        
        success, message = backup_manager.restore_backup(
            backup_path=backup_path,
            options=restore_options
        )
        
        if success:
            print(f"✓ 復元成功: {message}")
            
            # 復元されたファイルを確認
            restored_annotations = list(annotations_dir.glob("*.txt"))
            print(f"  - 復元されたアノテーション: {len(restored_annotations)} ファイル")
            
            if config_path.exists():
                print(f"  - 設定ファイル復元: ✓")
        else:
            print(f"✗ 復元失敗: {message}")
        
        # 5. 自動バックアップのテスト（実際には実行しない）
        print("\n5. 自動バックアップ設定...")
        backup_manager.start_auto_backup(interval_minutes=30, options=options)
        print("✓ 30分間隔の自動バックアップを設定")
        
        backup_manager.schedule_daily_backup(time_str="02:00", options=options)
        print("✓ 毎日2:00の定時バックアップを設定")
        
        backup_manager.stop_auto_backup()
        print("✓ 自動バックアップを停止")
        
        print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_backup_manager()