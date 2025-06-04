"""
Agent7 Persistence 性能テスト
100ms保存目標達成確認・ベンチマーク・性能回帰検知
"""

import os
import time
import tempfile
import unittest
import statistics
from datetime import datetime
from typing import List

from src.persistence.file_io.txt_handler import YOLOTxtHandler, BBEntity, Coordinates
from src.persistence.file_io.json_handler import JSONHandler, ProjectEntity
from src.persistence.backup.auto_saver import AutoSaver
from src.persistence.exceptions import PerformanceError


class TestPersistencePerformance(unittest.TestCase):
    """Persistence層性能テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.txt_handler = YOLOTxtHandler()
        self.json_handler = JSONHandler()
        
        # 性能テスト用データ生成
        self.small_bb_list = self._generate_bb_entities(10)
        self.medium_bb_list = self._generate_bb_entities(100)
        self.large_bb_list = self._generate_bb_entities(1000)
        
        # 性能基準値（ms）
        self.SAVE_TARGET = 100
        self.LOAD_TARGET = 50
        self.JSON_SAVE_TARGET = 30
        self.JSON_LOAD_TARGET = 20
        
    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _generate_bb_entities(self, count: int) -> List[BBEntity]:
        """BBエンティティ生成"""
        entities = []
        for i in range(count):
            entity = BBEntity(
                id=f"perf_bb_{i}",
                frame_id=f"{i:06d}",
                individual_id=i % 16,
                action_id=i % 5,
                coordinates=Coordinates(
                    (i % 10) * 0.1,
                    (i % 10) * 0.1,
                    0.1,
                    0.1
                ),
                confidence=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            entities.append(entity)
        return entities
        
    def test_txt_save_100ms_target(self):
        """YOLO txt保存100ms目標達成確認"""
        test_cases = [
            ("small", self.small_bb_list),
            ("medium", self.medium_bb_list),
            ("large", self.large_bb_list)
        ]
        
        for case_name, bb_entities in test_cases:
            with self.subTest(case=case_name):
                frame_id = f"{hash(case_name) % 1000000:06d}"
                
                # 性能測定
                start_time = time.perf_counter()
                success = self.txt_handler.save_annotations(
                    frame_id, bb_entities, self.temp_dir
                )
                elapsed_time = (time.perf_counter() - start_time) * 1000
                
                # 結果確認
                self.assertTrue(success)
                self.assertLess(
                    elapsed_time, self.SAVE_TARGET,
                    f"Save time {elapsed_time:.2f}ms exceeds {self.SAVE_TARGET}ms target for {case_name} ({len(bb_entities)} entities)"
                )
                
                print(f"TXT Save Performance ({case_name}): {elapsed_time:.2f}ms for {len(bb_entities)} entities")
                
    def test_txt_load_50ms_target(self):
        """YOLO txt読み込み50ms目標達成確認"""
        test_cases = [
            ("small", self.small_bb_list),
            ("medium", self.medium_bb_list),
            ("large", self.large_bb_list)
        ]
        
        for case_name, bb_entities in test_cases:
            with self.subTest(case=case_name):
                frame_id = f"{hash(f'load_{case_name}') % 1000000:06d}"
                
                # 事前保存
                self.txt_handler.save_annotations(frame_id, bb_entities, self.temp_dir)
                
                # 性能測定
                start_time = time.perf_counter()
                loaded_entities = self.txt_handler.load_annotations(frame_id, self.temp_dir)
                elapsed_time = (time.perf_counter() - start_time) * 1000
                
                # 結果確認
                self.assertEqual(len(loaded_entities), len(bb_entities))
                self.assertLess(
                    elapsed_time, self.LOAD_TARGET,
                    f"Load time {elapsed_time:.2f}ms exceeds {self.LOAD_TARGET}ms target for {case_name} ({len(bb_entities)} entities)"
                )
                
                print(f"TXT Load Performance ({case_name}): {elapsed_time:.2f}ms for {len(bb_entities)} entities")
                
    def test_json_save_30ms_target(self):
        """JSON保存30ms目標達成確認"""
        project = ProjectEntity(
            name="performance_test",
            version="1.0.0",
            created_at=datetime.now(),
            video_source="/test/video.mp4",
            frame_output="/test/frames",
            annotation_output="/test/annotations",
            backup_path="/test/backup",
            total_frames=1000,
            annotated_frames=500,
            frame_rate_original=30.0,
            frame_rate_target=5.0,
            resolution_width=1920,
            resolution_height=1080,
            annotation_config={"individuals": list(range(16))},
            tracking_config={"iou_threshold": 0.5},
            performance_config={"cache_size": "20GB"},
            ui_config={"theme": "dark"},
            export_config={"formats": ["yolo", "coco"]}
        )
        
        config_path = os.path.join(self.temp_dir, "project.json")
        
        # 性能測定
        start_time = time.perf_counter()
        success = self.json_handler.save_project_config(project, config_path)
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        # 結果確認
        self.assertTrue(success)
        self.assertLess(
            elapsed_time, self.JSON_SAVE_TARGET,
            f"JSON save time {elapsed_time:.2f}ms exceeds {self.JSON_SAVE_TARGET}ms target"
        )
        
        print(f"JSON Save Performance: {elapsed_time:.2f}ms")
        
    def test_json_load_20ms_target(self):
        """JSON読み込み20ms目標達成確認"""
        project = ProjectEntity(
            name="performance_test",
            version="1.0.0",
            created_at=datetime.now(),
            video_source="/test/video.mp4",
            frame_output="/test/frames",
            annotation_output="/test/annotations",
            backup_path="/test/backup",
            total_frames=1000,
            annotated_frames=500,
            frame_rate_original=30.0,
            frame_rate_target=5.0,
            resolution_width=1920,
            resolution_height=1080,
            annotation_config={"individuals": list(range(16))},
            tracking_config={"iou_threshold": 0.5},
            performance_config={"cache_size": "20GB"},
            ui_config={"theme": "dark"},
            export_config={"formats": ["yolo", "coco"]}
        )
        
        config_path = os.path.join(self.temp_dir, "project.json")
        
        # 事前保存
        self.json_handler.save_project_config(project, config_path)
        
        # 性能測定
        start_time = time.perf_counter()
        loaded_project = self.json_handler.load_project_config(config_path)
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        # 結果確認
        self.assertEqual(loaded_project.name, project.name)
        self.assertLess(
            elapsed_time, self.JSON_LOAD_TARGET,
            f"JSON load time {elapsed_time:.2f}ms exceeds {self.JSON_LOAD_TARGET}ms target"
        )
        
        print(f"JSON Load Performance: {elapsed_time:.2f}ms")
        
    def test_batch_save_performance(self):
        """一括保存性能確認"""
        from src.persistence.file_io.batch_writer import BatchWriter
        
        batch_writer = BatchWriter(max_workers=4)
        
        # 一括保存データ準備
        frame_bb_pairs = []
        for i in range(100):  # 100フレーム
            frame_id = f"{i:06d}"
            bb_entities = self._generate_bb_entities(10)  # 各フレーム10個のBB
            frame_bb_pairs.append((frame_id, bb_entities))
            
        # 性能測定
        start_time = time.perf_counter()
        results = batch_writer.batch_save_annotations(frame_bb_pairs, self.temp_dir)
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        # 結果確認
        successful_saves = sum(1 for success in results.values() if success)
        self.assertEqual(successful_saves, 100)
        
        # 平均保存時間確認
        avg_time_per_frame = elapsed_time / 100
        self.assertLess(
            avg_time_per_frame, self.SAVE_TARGET,
            f"Average save time per frame {avg_time_per_frame:.2f}ms exceeds {self.SAVE_TARGET}ms target"
        )
        
        print(f"Batch Save Performance: {elapsed_time:.2f}ms total, {avg_time_per_frame:.2f}ms per frame")
        
    def test_auto_saver_performance(self):
        """自動保存性能確認"""
        auto_saver = AutoSaver(save_interval=1, max_workers=2)
        auto_saver.start_auto_save()
        
        try:
            # 複数タスクスケジューリング
            task_ids = []
            start_time = time.perf_counter()
            
            for i in range(50):
                task_id = auto_saver.schedule_save(
                    f"auto_perf_{i:03d}",
                    self.small_bb_list,
                    priority="high"
                )
                task_ids.append(task_id)
                
            scheduling_time = (time.perf_counter() - start_time) * 1000
            
            # 処理完了まで待機
            time.sleep(2.0)
            
            # 統計確認
            stats = auto_saver.get_save_statistics()
            
            # スケジューリング性能確認
            avg_scheduling_time = scheduling_time / 50
            self.assertLess(
                avg_scheduling_time, 5.0,
                f"Average scheduling time {avg_scheduling_time:.2f}ms exceeds 5ms target"
            )
            
            # 保存成功率確認
            self.assertGreaterEqual(stats["success_rate"], 95.0)
            
            # 平均保存時間確認
            self.assertLess(
                stats["average_save_time"], self.SAVE_TARGET,
                f"Average save time {stats['average_save_time']:.2f}ms exceeds {self.SAVE_TARGET}ms target"
            )
            
            print(f"Auto Saver Performance: scheduling={avg_scheduling_time:.2f}ms/task, "
                  f"saving={stats['average_save_time']:.2f}ms/save, success_rate={stats['success_rate']:.1f}%")
                  
        finally:
            auto_saver.stop_auto_save()
            
    def test_memory_usage_efficiency(self):
        """メモリ使用効率確認"""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # 初期メモリ使用量
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 大量データ処理
        for i in range(10):
            large_entities = self._generate_bb_entities(1000)
            frame_id = f"memory_test_{i:03d}"
            
            self.txt_handler.save_annotations(frame_id, large_entities, self.temp_dir)
            loaded_entities = self.txt_handler.load_annotations(frame_id, self.temp_dir)
            
            # 処理済みデータクリア
            del large_entities
            del loaded_entities
            
        # ガベージコレクション
        gc.collect()
        
        # 最終メモリ使用量
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # メモリリーク確認（100MB未満の増加を許容）
        self.assertLess(
            memory_increase, 100,
            f"Memory increase {memory_increase:.1f}MB suggests potential memory leak"
        )
        
        print(f"Memory Usage: initial={initial_memory:.1f}MB, final={final_memory:.1f}MB, "
              f"increase={memory_increase:.1f}MB")
              
    def test_concurrent_performance(self):
        """並行処理性能確認"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def save_task(thread_id: int, entity_count: int):
            entities = self._generate_bb_entities(entity_count)
            frame_id = f"concurrent_{thread_id:02d}"
            
            start_time = time.perf_counter()
            success = self.txt_handler.save_annotations(frame_id, entities, self.temp_dir)
            elapsed_time = (time.perf_counter() - start_time) * 1000
            
            results_queue.put((thread_id, success, elapsed_time, entity_count))
            
        # 並行保存実行
        threads = []
        for i in range(8):  # 8スレッド
            t = threading.Thread(target=save_task, args=(i, 100))
            threads.append(t)
            
        start_time = time.perf_counter()
        for t in threads:
            t.start()
            
        for t in threads:
            t.join()
            
        total_elapsed = (time.perf_counter() - start_time) * 1000
        
        # 結果収集
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
            
        # 性能確認
        self.assertEqual(len(results), 8)
        
        all_successful = all(result[1] for result in results)
        self.assertTrue(all_successful)
        
        max_individual_time = max(result[2] for result in results)
        avg_individual_time = statistics.mean(result[2] for result in results)
        
        # 個別タスクが目標時間内
        self.assertLess(max_individual_time, self.SAVE_TARGET)
        
        # 並行処理の効率性確認（単純合計より速い）
        sequential_estimate = avg_individual_time * 8
        efficiency = (sequential_estimate - total_elapsed) / sequential_estimate * 100
        
        self.assertGreater(efficiency, 50.0, "Concurrent processing should be at least 50% more efficient")
        
        print(f"Concurrent Performance: total={total_elapsed:.2f}ms, "
              f"avg_individual={avg_individual_time:.2f}ms, efficiency={efficiency:.1f}%")
              
    def test_performance_consistency(self):
        """性能一貫性確認（性能回帰検知）"""
        # 同一条件で複数回実行
        execution_times = []
        
        for i in range(20):
            frame_id = f"consistency_{i:02d}"
            
            start_time = time.perf_counter()
            success = self.txt_handler.save_annotations(
                frame_id, self.medium_bb_list, self.temp_dir
            )
            elapsed_time = (time.perf_counter() - start_time) * 1000
            
            self.assertTrue(success)
            execution_times.append(elapsed_time)
            
        # 統計分析
        mean_time = statistics.mean(execution_times)
        std_dev = statistics.stdev(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        # 一貫性確認
        coefficient_of_variation = std_dev / mean_time
        self.assertLess(
            coefficient_of_variation, 0.5,
            f"Performance variation too high: CV={coefficient_of_variation:.3f}"
        )
        
        # 全実行が目標時間内
        self.assertLess(max_time, self.SAVE_TARGET)
        
        print(f"Performance Consistency: mean={mean_time:.2f}ms, std={std_dev:.2f}ms, "
              f"min={min_time:.2f}ms, max={max_time:.2f}ms, CV={coefficient_of_variation:.3f}")
              
    def test_large_file_performance(self):
        """大容量ファイル性能確認"""
        # 極大データセット（10,000 BB）
        huge_bb_list = self._generate_bb_entities(10000)
        frame_id = "huge_dataset"
        
        # 保存性能
        start_time = time.perf_counter()
        success = self.txt_handler.save_annotations(frame_id, huge_bb_list, self.temp_dir)
        save_time = (time.perf_counter() - start_time) * 1000
        
        self.assertTrue(success)
        
        # ファイルサイズ確認
        file_path = os.path.join(self.temp_dir, f"{frame_id}.txt")
        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
        
        # 読み込み性能
        start_time = time.perf_counter()
        loaded_entities = self.txt_handler.load_annotations(frame_id, self.temp_dir)
        load_time = (time.perf_counter() - start_time) * 1000
        
        self.assertEqual(len(loaded_entities), 10000)
        
        # 大容量データでも適切な性能を維持
        # 線形スケーリング想定で目標時間調整
        adjusted_save_target = self.SAVE_TARGET * 10  # 100倍データなら10倍時間許容
        adjusted_load_target = self.LOAD_TARGET * 10
        
        self.assertLess(save_time, adjusted_save_target)
        self.assertLess(load_time, adjusted_load_target)
        
        print(f"Large File Performance: file_size={file_size:.1f}MB, "
              f"save={save_time:.2f}ms, load={load_time:.2f}ms")


if __name__ == '__main__':
    # 性能テスト実行
    unittest.main(verbosity=2)