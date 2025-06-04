"""
YOLO txtハンドラー単体テスト
100ms保存・50ms読み込み性能要件確認
"""

import os
import time
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch, mock_open

from src.persistence.file_io.txt_handler import (
    YOLOTxtHandler, BBEntity, Coordinates
)
from src.persistence.exceptions import FileIOError, ValidationError, PerformanceError


class TestYOLOTxtHandler(unittest.TestCase):
    """YOLO txtハンドラーテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.handler = YOLOTxtHandler()
        self.temp_dir = tempfile.mkdtemp()
        
        # テスト用BBエンティティ
        self.test_bb_entities = [
            BBEntity(
                id="bb1",
                frame_id="000001",
                individual_id=0,
                action_id=2,
                coordinates=Coordinates(0.5123, 0.3456, 0.1234, 0.0987),
                confidence=0.9512,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BBEntity(
                id="bb2", 
                frame_id="000001",
                individual_id=1,
                action_id=0,
                coordinates=Coordinates(0.2345, 0.7890, 0.0876, 0.1234),
                confidence=0.8743,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_save_annotations_100ms(self):
        """アノテーション保存100ms以下確認"""
        frame_id = "000001"
        
        # 性能測定
        start_time = time.perf_counter()
        success = self.handler.save_annotations(
            frame_id, self.test_bb_entities, self.temp_dir
        )
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        # 性能要件確認
        self.assertTrue(success)
        self.assertLess(elapsed_time, 100, f"Save time {elapsed_time:.2f}ms exceeds 100ms limit")
        
        # ファイル存在確認
        expected_file = os.path.join(self.temp_dir, f"{frame_id}.txt")
        self.assertTrue(os.path.exists(expected_file))
        
    def test_load_annotations_50ms(self):
        """アノテーション読み込み50ms以下確認"""
        frame_id = "000001"
        
        # 事前にファイル保存
        self.handler.save_annotations(frame_id, self.test_bb_entities, self.temp_dir)
        
        # 性能測定
        start_time = time.perf_counter()
        loaded_entities = self.handler.load_annotations(frame_id, self.temp_dir)
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        # 性能要件確認
        self.assertLess(elapsed_time, 50, f"Load time {elapsed_time:.2f}ms exceeds 50ms limit")
        
        # データ整合性確認
        self.assertEqual(len(loaded_entities), 2)
        self.assertEqual(loaded_entities[0].individual_id, 0)
        self.assertEqual(loaded_entities[1].individual_id, 1)
        
    def test_yolo_format_accuracy(self):
        """YOLO形式精度確認"""
        frame_id = "000001"
        
        # 保存・読み込み
        self.handler.save_annotations(frame_id, self.test_bb_entities, self.temp_dir)
        loaded_entities = self.handler.load_annotations(frame_id, self.temp_dir)
        
        # 座標精度確認（小数点4桁）
        original = self.test_bb_entities[0]
        loaded = loaded_entities[0]
        
        self.assertAlmostEqual(original.coordinates.x, loaded.coordinates.x, places=4)
        self.assertAlmostEqual(original.coordinates.y, loaded.coordinates.y, places=4)
        self.assertAlmostEqual(original.coordinates.w, loaded.coordinates.w, places=4)
        self.assertAlmostEqual(original.coordinates.h, loaded.coordinates.h, places=4)
        self.assertAlmostEqual(original.confidence, loaded.confidence, places=4)
        
    def test_data_validation(self):
        """データ検証確認"""
        # 不正な個体ID
        with self.assertRaises(ValidationError):
            invalid_bb = BBEntity(
                id="invalid",
                frame_id="000001",
                individual_id=16,  # 範囲外
                action_id=0,
                coordinates=Coordinates(0.5, 0.5, 0.1, 0.1),
                confidence=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.handler.save_annotations("000001", [invalid_bb], self.temp_dir)
            
        # 不正な行動ID
        with self.assertRaises(ValidationError):
            invalid_bb = BBEntity(
                id="invalid",
                frame_id="000001", 
                individual_id=0,
                action_id=5,  # 範囲外
                coordinates=Coordinates(0.5, 0.5, 0.1, 0.1),
                confidence=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.handler.save_annotations("000001", [invalid_bb], self.temp_dir)
            
        # 不正な座標
        with self.assertRaises(ValidationError):
            invalid_bb = BBEntity(
                id="invalid",
                frame_id="000001",
                individual_id=0,
                action_id=0,
                coordinates=Coordinates(1.5, 0.5, 0.1, 0.1),  # 範囲外
                confidence=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.handler.save_annotations("000001", [invalid_bb], self.temp_dir)
            
    def test_empty_annotations(self):
        """空アノテーション処理確認"""
        frame_id = "000002"
        
        # 空リスト保存
        success = self.handler.save_annotations(frame_id, [], self.temp_dir)
        self.assertTrue(success)
        
        # 空ファイル読み込み
        loaded_entities = self.handler.load_annotations(frame_id, self.temp_dir)
        self.assertEqual(len(loaded_entities), 0)
        
    def test_nonexistent_file_load(self):
        """存在しないファイル読み込み"""
        loaded_entities = self.handler.load_annotations("999999", self.temp_dir)
        self.assertEqual(len(loaded_entities), 0)
        
    def test_invalid_yolo_line_format(self):
        """不正YOLO行形式処理"""
        # 不正ファイル作成
        invalid_file = os.path.join(self.temp_dir, "invalid.txt")
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write("0 0.5 0.5\n")  # フィールド不足
            f.write("invalid line\n")  # 完全に不正
            
        with self.assertRaises(ValidationError):
            self.handler.load_annotations("invalid", self.temp_dir)
            
    def test_file_encoding(self):
        """ファイルエンコーディング確認"""
        frame_id = "000003"
        
        # UTF-8保存確認
        self.handler.save_annotations(frame_id, self.test_bb_entities, self.temp_dir)
        
        file_path = os.path.join(self.temp_dir, f"{frame_id}.txt")
        
        # UTF-8読み込み確認
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 内容確認
        lines = content.strip().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertIn("0 0.5123 0.3456 0.1234 0.0987 2 0.9512", lines[0])
        
    def test_line_ending_format(self):
        """行末形式確認（Unix LF）"""
        frame_id = "000004"
        
        self.handler.save_annotations(frame_id, self.test_bb_entities, self.temp_dir)
        
        file_path = os.path.join(self.temp_dir, f"{frame_id}.txt")
        
        # バイナリ読み込みで行末確認
        with open(file_path, 'rb') as f:
            content = f.read()
            
        # Unix LF確認
        self.assertIn(b'\n', content)
        self.assertNotIn(b'\r\n', content)  # Windows CRLF不使用
        
    def test_performance_timeout_save(self):
        """保存タイムアウトテスト"""
        # 大量データでタイムアウト発生を模擬
        large_bb_list = []
        for i in range(1000):  # 大量BB
            bb = BBEntity(
                id=f"bb{i}",
                frame_id="large",
                individual_id=i % 16,
                action_id=i % 5,
                coordinates=Coordinates(0.1 * (i % 10), 0.1 * (i % 10), 0.1, 0.1),
                confidence=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            large_bb_list.append(bb)
            
        # タイムアウト設定を短くしてテスト
        original_timeout = self.handler.save_timeout
        self.handler.save_timeout = 1  # 1ms（意図的に短い）
        
        try:
            with self.assertRaises(PerformanceError):
                self.handler.save_annotations("large", large_bb_list, self.temp_dir)
        finally:
            self.handler.save_timeout = original_timeout
            
    def test_performance_timeout_load(self):
        """読み込みタイムアウトテスト"""
        # 事前に大量データ保存
        large_bb_list = []
        for i in range(100):
            bb = BBEntity(
                id=f"bb{i}",
                frame_id="large_load",
                individual_id=i % 16,
                action_id=i % 5,
                coordinates=Coordinates(0.1 * (i % 10), 0.1 * (i % 10), 0.1, 0.1),
                confidence=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            large_bb_list.append(bb)
            
        self.handler.save_annotations("large_load", large_bb_list, self.temp_dir)
        
        # タイムアウト設定を短くしてテスト
        original_timeout = self.handler.load_timeout
        self.handler.load_timeout = 1  # 1ms（意図的に短い）
        
        try:
            with self.assertRaises(PerformanceError):
                self.handler.load_annotations("large_load", self.temp_dir)
        finally:
            self.handler.load_timeout = original_timeout
            
    def test_file_stats(self):
        """ファイル統計情報取得"""
        frame_id = "000005"
        
        # ファイル保存
        self.handler.save_annotations(frame_id, self.test_bb_entities, self.temp_dir)
        
        file_path = os.path.join(self.temp_dir, f"{frame_id}.txt")
        stats = self.handler.get_file_stats(file_path)
        
        self.assertTrue(stats["exists"])
        self.assertGreater(stats["size"], 0)
        self.assertIsInstance(stats["modified"], datetime)
        self.assertIsInstance(stats["created"], datetime)
        
        # 存在しないファイル
        nonexistent_stats = self.handler.get_file_stats("nonexistent.txt")
        self.assertFalse(nonexistent_stats["exists"])
        
    def test_frame_id_validation(self):
        """フレームID検証"""
        # 有効なフレームID
        self.assertTrue(self.handler._validate_frame_id("000001"))
        self.assertTrue(self.handler._validate_frame_id("123456"))
        
        # 無効なフレームID
        self.assertFalse(self.handler._validate_frame_id("00001"))   # 桁数不足
        self.assertFalse(self.handler._validate_frame_id("0000001")) # 桁数超過
        self.assertFalse(self.handler._validate_frame_id("00000a"))  # 数字以外
        self.assertFalse(self.handler._validate_frame_id(None))      # None
        
    def test_concurrent_access(self):
        """並行アクセステスト"""
        import threading
        
        frame_id = "concurrent"
        results = []
        
        def save_task():
            try:
                success = self.handler.save_annotations(
                    frame_id, self.test_bb_entities, self.temp_dir
                )
                results.append(("save", success))
            except Exception as e:
                results.append(("save", str(e)))
                
        def load_task():
            try:
                entities = self.handler.load_annotations(frame_id, self.temp_dir)
                results.append(("load", len(entities)))
            except Exception as e:
                results.append(("load", str(e)))
                
        # 並行実行
        threads = []
        for _ in range(3):
            t1 = threading.Thread(target=save_task)
            t2 = threading.Thread(target=load_task)
            threads.extend([t1, t2])
            
        for t in threads:
            t.start()
            
        for t in threads:
            t.join()
            
        # 結果確認（エラーなく完了）
        self.assertGreater(len(results), 0)
        for operation, result in results:
            if isinstance(result, str) and "Error" in result:
                self.fail(f"Concurrent access failed: {operation} - {result}")


if __name__ == '__main__':
    unittest.main()