"""
自動保存システム単体テスト
非同期保存・差分検知・リトライ機能確認
"""

import os
import time
import tempfile
import unittest
import threading
from unittest.mock import Mock, patch
from datetime import datetime

from src.persistence.backup.auto_saver import AutoSaver, SaveTask, SaveResult
from src.persistence.file_io.txt_handler import BBEntity, Coordinates


class TestAutoSaver(unittest.TestCase):
    """自動保存システムテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.auto_saver = AutoSaver(save_interval=1, max_workers=2)
        self.temp_dir = tempfile.mkdtemp()
        
        # テスト用BBエンティティ
        self.test_bb_entities = [
            BBEntity(
                id="test_bb1",
                frame_id="000001",
                individual_id=0,
                action_id=1,
                coordinates=Coordinates(0.5, 0.5, 0.1, 0.1),
                confidence=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
    def tearDown(self):
        """テストクリーンアップ"""
        self.auto_saver.stop_auto_save()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_async_save_non_blocking(self):
        """非同期保存・UIブロックなし確認"""
        self.auto_saver.start_auto_save()
        
        # 保存スケジュール（非同期）
        start_time = time.perf_counter()
        task_id = self.auto_saver.schedule_save(
            "000001", self.test_bb_entities, priority="high"
        )
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        # スケジュール自体は即座に完了（非同期）
        self.assertLess(elapsed_time, 10, "Schedule operation should be non-blocking")
        self.assertNotEqual(task_id, "")
        
        # 保存完了まで少し待つ
        time.sleep(0.5)
        
        # 統計確認
        stats = self.auto_saver.get_save_statistics()
        self.assertGreater(stats["total_saves"], 0)
        
    def test_save_retry_mechanism(self):
        """保存リトライ機能確認"""
        # 失敗するハンドラーをモック
        with patch.object(self.auto_saver.txt_handler, 'save_annotations') as mock_save:
            mock_save.side_effect = [Exception("First fail"), Exception("Second fail"), True]
            
            self.auto_saver.start_auto_save()
            
            # 失敗するタスクをスケジュール
            task_id = self.auto_saver.schedule_save(
                "retry_test", self.test_bb_entities, priority="high"
            )
            
            # リトライ完了まで待つ
            time.sleep(2.0)
            
            # 3回呼び出し確認（初回 + 2回リトライ）
            self.assertEqual(mock_save.call_count, 3)
            
    def test_differential_save(self):
        """差分保存確認"""
        self.auto_saver.start_auto_save()
        
        # 初回保存
        task_id1 = self.auto_saver.schedule_save(
            "diff_test", self.test_bb_entities, priority="normal"
        )
        time.sleep(0.2)
        
        # 同じデータで再保存（差分なし）
        task_id2 = self.auto_saver.schedule_save(
            "diff_test", self.test_bb_entities, priority="normal", force_save=False
        )
        
        # 差分なしの場合は空のタスクID
        self.assertEqual(task_id2, "")
        
        # データ変更
        modified_entities = self.test_bb_entities.copy()
        modified_entities[0].confidence = 0.8  # 変更
        
        # 変更後保存（差分あり）
        task_id3 = self.auto_saver.schedule_save(
            "diff_test", modified_entities, priority="normal", force_save=False
        )
        self.assertNotEqual(task_id3, "")
        
    def test_priority_queue_ordering(self):
        """優先度キュー順序確認"""
        self.auto_saver.start_auto_save()
        
        # 異なる優先度でタスクスケジュール
        task_low = self.auto_saver.schedule_save(
            "low", self.test_bb_entities, priority="low"
        )
        task_high = self.auto_saver.schedule_save(
            "high", self.test_bb_entities, priority="high"
        )
        task_normal = self.auto_saver.schedule_save(
            "normal", self.test_bb_entities, priority="normal"
        )
        
        # 待機中タスク数確認
        pending = self.auto_saver.get_pending_saves_count()
        self.assertEqual(pending["high"], 1)
        self.assertEqual(pending["normal"], 1)
        self.assertEqual(pending["low"], 1)
        
        # 処理完了まで待つ
        time.sleep(1.0)
        
        # 全て処理されたことを確認
        pending_after = self.auto_saver.get_pending_saves_count()
        self.assertEqual(sum(pending_after.values()), 0)
        
    def test_save_statistics(self):
        """保存統計情報確認"""
        self.auto_saver.start_auto_save()
        
        # 複数保存実行
        for i in range(5):
            self.auto_saver.schedule_save(
                f"stats_{i:03d}", self.test_bb_entities, priority="normal"
            )
            
        # 処理完了まで待つ
        time.sleep(1.0)
        
        stats = self.auto_saver.get_save_statistics()
        
        self.assertGreaterEqual(stats["total_saves"], 5)
        self.assertGreater(stats["successful_saves"], 0)
        self.assertGreaterEqual(stats["success_rate"], 0)
        self.assertGreaterEqual(stats["average_save_time"], 0)
        
    def test_json_save_scheduling(self):
        """JSON保存スケジュール確認"""
        test_config = {
            "project_name": "test_project",
            "version": "1.0.0",
            "settings": {"key": "value"}
        }
        
        config_path = os.path.join(self.temp_dir, "test_config.json")
        
        self.auto_saver.start_auto_save()
        
        # JSON保存スケジュール
        task_id = self.auto_saver.schedule_json_save(
            test_config, config_path, priority="low"
        )
        
        self.assertNotEqual(task_id, "")
        
        # 保存完了まで待つ
        time.sleep(0.5)
        
        # ファイル存在確認
        self.assertTrue(os.path.exists(config_path))
        
    def test_force_save_all_pending(self):
        """待機中タスク強制実行確認"""
        # 自動保存停止状態でテスト
        
        # 複数タスクスケジュール
        for i in range(3):
            self.auto_saver.schedule_save(
                f"force_{i:03d}", self.test_bb_entities, priority="normal"
            )
            
        # 待機中タスク確認
        pending = self.auto_saver.get_pending_saves_count()
        total_pending = sum(pending.values())
        self.assertGreater(total_pending, 0)
        
        # 強制実行
        results = self.auto_saver.force_save_all_pending()
        
        # 結果確認
        self.assertEqual(len(results), total_pending)
        for result in results:
            self.assertIsInstance(result, SaveResult)
            
    def test_memory_management(self):
        """メモリ管理確認"""
        self.auto_saver.start_auto_save()
        
        # 大量のチェックサム蓄積
        for i in range(15000):  # 制限値10000を超過
            frame_id = f"{i:06d}"
            self.auto_saver._has_changes(frame_id, self.test_bb_entities)
            
        # メンテナンス実行
        self.auto_saver._perform_periodic_maintenance()
        
        # チェックサム辞書がクリアされていることを確認
        self.assertLessEqual(len(self.auto_saver.frame_checksums), 10000)
        
    def test_callback_functions(self):
        """コールバック関数確認"""
        success_called = False
        error_called = False
        
        def on_success(result):
            nonlocal success_called
            success_called = True
            
        def on_error(result):
            nonlocal error_called
            error_called = True
            
        self.auto_saver.on_save_complete = on_success
        self.auto_saver.on_save_error = on_error
        
        self.auto_saver.start_auto_save()
        
        # 成功ケース
        self.auto_saver.schedule_save(
            "callback_success", self.test_bb_entities, priority="high"
        )
        
        time.sleep(0.5)
        
        self.assertTrue(success_called)
        
    def test_stop_auto_save_gracefully(self):
        """自動保存の正常停止確認"""
        self.auto_saver.start_auto_save()
        
        # タスクスケジュール
        for i in range(5):
            self.auto_saver.schedule_save(
                f"stop_test_{i}", self.test_bb_entities, priority="normal"
            )
            
        # 停止
        start_time = time.perf_counter()
        self.auto_saver.stop_auto_save()
        elapsed_time = time.perf_counter() - start_time
        
        # 適切な時間内に停止
        self.assertLess(elapsed_time, 10.0, "Stop should complete within 10 seconds")
        
        # ワーカースレッド終了確認
        self.assertFalse(self.auto_saver.is_running)
        self.assertEqual(len(self.auto_saver.worker_threads), 0)
        
    def test_has_changes_detection(self):
        """変更検知機能確認"""
        frame_id = "change_test"
        
        # 初回は変更あり
        has_changes1 = self.auto_saver._has_changes(frame_id, self.test_bb_entities)
        self.assertTrue(has_changes1)
        
        # 同じデータは変更なし
        has_changes2 = self.auto_saver._has_changes(frame_id, self.test_bb_entities)
        self.assertFalse(has_changes2)
        
        # データ変更
        modified_entities = self.test_bb_entities.copy()
        modified_entities[0].confidence = 0.8
        
        # 変更あり
        has_changes3 = self.auto_saver._has_changes(frame_id, modified_entities)
        self.assertTrue(has_changes3)
        
        # 変更後のデータは変更なし
        has_changes4 = self.auto_saver._has_changes(frame_id, modified_entities)
        self.assertFalse(has_changes4)
        
    def test_concurrent_scheduling(self):
        """並行スケジューリングテスト"""
        self.auto_saver.start_auto_save()
        
        task_ids = []
        threads = []
        
        def schedule_task(i):
            task_id = self.auto_saver.schedule_save(
                f"concurrent_{i:03d}", self.test_bb_entities, priority="normal"
            )
            task_ids.append(task_id)
            
        # 並行スケジューリング
        for i in range(10):
            t = threading.Thread(target=schedule_task, args=(i,))
            threads.append(t)
            t.start()
            
        # 完了待ち
        for t in threads:
            t.join()
            
        # 全タスクが正常にスケジュールされたことを確認
        valid_task_ids = [tid for tid in task_ids if tid != ""]
        self.assertEqual(len(valid_task_ids), 10)
        
        # 処理完了まで待つ
        time.sleep(2.0)
        
        stats = self.auto_saver.get_save_statistics()
        self.assertGreaterEqual(stats["total_saves"], 10)


if __name__ == '__main__':
    unittest.main()