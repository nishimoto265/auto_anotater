"""
バックアップ管理システム単体テスト
5分毎バックアップ・復旧・世代管理確認
"""

import os
import time
import tempfile
import unittest
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch

from src.persistence.backup.backup_manager import BackupManager, BackupInfo
from src.persistence.exceptions import BackupError


class TestBackupManager(unittest.TestCase):
    """バックアップ管理システムテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.source_dir = os.path.join(self.temp_dir, "source")
        
        # バックアップマネージャー初期化
        self.backup_manager = BackupManager(
            backup_root_dir=self.backup_dir,
            backup_interval=5  # 5秒（テスト用）
        )
        
        # テスト用ソースデータ作成
        os.makedirs(self.source_dir, exist_ok=True)
        self._create_test_data()
        
    def tearDown(self):
        """テストクリーンアップ"""
        self.backup_manager.stop_auto_backup()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _create_test_data(self):
        """テストデータ作成"""
        # アノテーションファイル
        annotations_dir = os.path.join(self.source_dir, "annotations")
        os.makedirs(annotations_dir, exist_ok=True)
        
        for i in range(5):
            file_path = os.path.join(annotations_dir, f"{i:06d}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"0 0.5 0.5 0.1 0.1 {i % 5} 0.9\n")
                
        # 設定ファイル
        config_path = os.path.join(self.source_dir, "project.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write('{"name": "test_project", "version": "1.0"}')
            
    def test_backup_creation_5min_interval(self):
        """5分毎バックアップ作成確認"""
        # 自動バックアップ開始
        self.backup_manager.start_auto_backup([self.source_dir])
        
        # 短時間でテストするため間隔を短縮
        original_interval = self.backup_manager.backup_interval
        self.backup_manager.backup_interval = 1  # 1秒
        
        try:
            # 2秒待機（2回バックアップが実行される可能性）
            time.sleep(2.5)
            
            # バックアップ履歴確認
            backups = self.backup_manager.list_available_backups(self.source_dir)
            self.assertGreater(len(backups), 0, "Auto backup should create at least one backup")
            
        finally:
            self.backup_manager.backup_interval = original_interval
            
    def test_backup_restoration_accuracy(self):
        """バックアップ復旧精度確認"""
        # フルバックアップ作成
        backup_info = self.backup_manager.create_backup(
            self.source_dir, 
            backup_name="test_full_backup",
            backup_type="full"
        )
        
        # 復旧先ディレクトリ
        restore_dir = os.path.join(self.temp_dir, "restored")
        
        # バックアップ復旧
        success = self.backup_manager.restore_backup(
            backup_info, restore_dir, overwrite=True
        )
        
        self.assertTrue(success)
        
        # ファイル内容比較
        self._compare_directories(self.source_dir, restore_dir)
        
    def test_generation_management(self):
        """世代管理確認"""
        # 最大世代数を3に設定
        self.backup_manager.max_backup_generations = 3
        
        # 5個のバックアップ作成
        for i in range(5):
            backup_info = self.backup_manager.create_backup(
                self.source_dir,
                backup_name=f"generation_test_{i}",
                backup_type="full"
            )
            time.sleep(0.1)  # 作成時間を区別
            
        # 3個まで削減されていることを確認
        backups = self.backup_manager.list_available_backups(self.source_dir)
        self.assertLessEqual(len(backups), 3, "Backup count should be limited by max_generations")
        
        # 最新の3個が残っていることを確認
        backup_names = [b.backup_path for b in backups]
        self.assertIn("generation_test_4", str(backup_names))
        self.assertIn("generation_test_3", str(backup_names))
        self.assertIn("generation_test_2", str(backup_names))
        
    def test_incremental_backup(self):
        """増分バックアップ確認"""
        # 初回フルバックアップ
        full_backup = self.backup_manager.create_backup(
            self.source_dir,
            backup_name="incremental_test_full",
            backup_type="full"
        )
        
        # ソースディレクトリにファイル追加
        new_file = os.path.join(self.source_dir, "annotations", "new_file.txt")
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write("1 0.3 0.3 0.2 0.2 1 0.8\n")
            
        time.sleep(0.1)  # ファイル変更時刻を確実に分ける
        
        # 増分バックアップ
        incremental_backup = self.backup_manager.create_backup(
            self.source_dir,
            backup_name="incremental_test_inc",
            backup_type="incremental"
        )
        
        # 増分バックアップが追加ファイルのみ含むことを確認
        self.assertLess(incremental_backup.file_count, full_backup.file_count)
        self.assertLess(incremental_backup.size_bytes, full_backup.size_bytes)
        
    def test_differential_backup(self):
        """差分バックアップ確認"""
        # 初回フルバックアップ
        full_backup = self.backup_manager.create_backup(
            self.source_dir,
            backup_name="differential_test_full", 
            backup_type="full"
        )
        
        # ファイル変更1
        modified_file = os.path.join(self.source_dir, "annotations", "000001.txt")
        with open(modified_file, 'w', encoding='utf-8') as f:
            f.write("0 0.6 0.6 0.15 0.15 2 0.95\n")
            
        time.sleep(0.1)
        
        # 増分バックアップ1
        inc_backup1 = self.backup_manager.create_backup(
            self.source_dir,
            backup_name="differential_test_inc1",
            backup_type="incremental"
        )
        
        # ファイル変更2
        another_file = os.path.join(self.source_dir, "annotations", "000002.txt")
        with open(another_file, 'w', encoding='utf-8') as f:
            f.write("1 0.7 0.7 0.12 0.12 3 0.88\n")
            
        time.sleep(0.1)
        
        # 差分バックアップ（フル以降の全変更）
        diff_backup = self.backup_manager.create_backup(
            self.source_dir,
            backup_name="differential_test_diff",
            backup_type="differential"
        )
        
        # 差分バックアップが両方の変更を含むことを確認
        self.assertGreaterEqual(diff_backup.file_count, 2)
        
    def test_compression_functionality(self):
        """圧縮機能確認"""
        # 圧縮有効でバックアップ
        self.backup_manager.compression_enabled = True
        
        backup_info = self.backup_manager.create_backup(
            self.source_dir,
            backup_name="compression_test",
            backup_type="full"
        )
        
        self.assertTrue(backup_info.compressed)
        self.assertTrue(backup_info.backup_path.endswith('.zip'))
        self.assertTrue(os.path.exists(backup_info.backup_path))
        
        # 圧縮ファイルから復旧
        restore_dir = os.path.join(self.temp_dir, "compressed_restore")
        success = self.backup_manager.restore_backup(
            backup_info, restore_dir, overwrite=True
        )
        
        self.assertTrue(success)
        self._compare_directories(self.source_dir, restore_dir)
        
    def test_backup_statistics(self):
        """バックアップ統計情報確認"""
        # 複数バックアップ作成
        for i in range(3):
            self.backup_manager.create_backup(
                self.source_dir,
                backup_name=f"stats_test_{i}",
                backup_type="full"
            )
            
        stats = self.backup_manager.get_backup_statistics()
        
        self.assertEqual(stats["total_backups"], 3)
        self.assertGreater(stats["total_size_bytes"], 0)
        self.assertGreater(stats["total_files"], 0)
        self.assertIn("full", stats["backup_types"])
        self.assertEqual(stats["backup_types"]["full"], 3)
        
    def test_backup_deletion(self):
        """バックアップ削除確認"""
        # バックアップ作成
        backup_info = self.backup_manager.create_backup(
            self.source_dir,
            backup_name="deletion_test",
            backup_type="full"
        )
        
        # 削除前確認
        self.assertTrue(os.path.exists(backup_info.backup_path))
        backups_before = len(self.backup_manager.backup_history)
        
        # バックアップ削除
        success = self.backup_manager.delete_backup(backup_info.backup_id)
        
        self.assertTrue(success)
        self.assertFalse(os.path.exists(backup_info.backup_path))
        
        # 履歴から削除されていることを確認
        backups_after = len(self.backup_manager.backup_history)
        self.assertEqual(backups_after, backups_before - 1)
        
    def test_backup_history_persistence(self):
        """バックアップ履歴永続化確認"""
        # バックアップ作成
        backup_info = self.backup_manager.create_backup(
            self.source_dir,
            backup_name="history_test",
            backup_type="full"
        )
        
        # 新しいマネージャーインスタンス作成
        new_manager = BackupManager(
            backup_root_dir=self.backup_dir,
            backup_interval=300
        )
        
        # 履歴が復旧されていることを確認
        loaded_backups = new_manager.list_available_backups()
        backup_ids = [b.backup_id for b in loaded_backups]
        self.assertIn(backup_info.backup_id, backup_ids)
        
    def test_directory_change_detection(self):
        """ディレクトリ変更検知確認"""
        # 初期状態（変更なし）
        has_changes_initial = self.backup_manager._has_directory_changes(self.source_dir)
        self.assertTrue(has_changes_initial)  # 初回は変更あり
        
        # バックアップ実行（時刻記録）
        self.backup_manager.create_backup(self.source_dir, backup_type="incremental")
        
        # 変更なし確認
        has_changes_after_backup = self.backup_manager._has_directory_changes(self.source_dir)
        self.assertFalse(has_changes_after_backup)
        
        # ファイル変更
        test_file = os.path.join(self.source_dir, "annotations", "000000.txt")
        with open(test_file, 'a', encoding='utf-8') as f:
            f.write("# modified\n")
            
        # 変更検知
        has_changes_after_modify = self.backup_manager._has_directory_changes(self.source_dir)
        self.assertTrue(has_changes_after_modify)
        
    def test_error_handling(self):
        """エラーハンドリング確認"""
        # 存在しないディレクトリのバックアップ
        with self.assertRaises(BackupError):
            self.backup_manager.create_backup(
                "/nonexistent/directory",
                backup_name="error_test",
                backup_type="full"
            )
            
        # 不正なバックアップタイプ
        with self.assertRaises(BackupError):
            self.backup_manager.create_backup(
                self.source_dir,
                backup_name="invalid_type_test",
                backup_type="invalid_type"
            )
            
    def test_concurrent_backup_operations(self):
        """並行バックアップ操作確認"""
        import threading
        
        results = []
        
        def create_backup_task(i):
            try:
                backup_info = self.backup_manager.create_backup(
                    self.source_dir,
                    backup_name=f"concurrent_{i}",
                    backup_type="full"
                )
                results.append(("success", backup_info.backup_id))
            except Exception as e:
                results.append(("error", str(e)))
                
        # 並行バックアップ実行
        threads = []
        for i in range(3):
            t = threading.Thread(target=create_backup_task, args=(i,))
            threads.append(t)
            t.start()
            
        # 完了待ち
        for t in threads:
            t.join()
            
        # 結果確認
        self.assertEqual(len(results), 3)
        successful_backups = [r for r in results if r[0] == "success"]
        self.assertGreater(len(successful_backups), 0)
        
    def _compare_directories(self, dir1: str, dir2: str):
        """ディレクトリ内容比較"""
        # ファイル一覧比較
        files1 = set()
        files2 = set()
        
        for root, dirs, files in os.walk(dir1):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), dir1)
                files1.add(rel_path)
                
        for root, dirs, files in os.walk(dir2):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), dir2)
                files2.add(rel_path)
                
        self.assertEqual(files1, files2, "File lists should match")
        
        # ファイル内容比較
        for rel_path in files1:
            file1_path = os.path.join(dir1, rel_path)
            file2_path = os.path.join(dir2, rel_path)
            
            with open(file1_path, 'r', encoding='utf-8') as f1, \
                 open(file2_path, 'r', encoding='utf-8') as f2:
                content1 = f1.read()
                content2 = f2.read()
                self.assertEqual(content1, content2, f"Content should match for {rel_path}")


if __name__ == '__main__':
    unittest.main()