import unittest
import os
import tempfile
import shutil
from pathlib import Path
import numpy as np
from src.core.annotation_manager import AnnotationManager

class TestAnnotationManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.annotation_manager = AnnotationManager(self.temp_dir)
        
        # テスト用のサンプルデータ
        self.sample_annotation = {
            "frame_id": "000001",
            "bboxes": [
                {
                    "individual_id": 1,
                    "x": 0.5,
                    "y": 0.5,
                    "w": 0.1,
                    "h": 0.2,
                    "action_id": 1,
                    "confidence": 0.95
                }
            ]
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_yolo_format_io(self):
        # YOLOフォーマットの読み書きテスト
        frame_id = "000001"
        self.annotation_manager.save_annotation(frame_id, self.sample_annotation["bboxes"])
        loaded_annotation = self.annotation_manager.load_annotation(frame_id)
        self.assertEqual(len(loaded_annotation), 1)
        self.assertAlmostEqual(loaded_annotation[0]["x"], 0.5)

    def test_data_integrity(self):
        # データ整合性チェック
        frame_id = "000002"
        self.annotation_manager.save_annotation(frame_id, self.sample_annotation["bboxes"])
        self.assertTrue(self.annotation_manager.verify_annotation(frame_id))

    def test_file_io_errors(self):
        # ファイルI/Oエラーハンドリング
        with self.assertRaises(FileNotFoundError):
            self.annotation_manager.load_annotation("999999")

    def test_large_data_processing(self):
        # 大容量データ処理テスト
        large_bboxes = []
        for i in range(1000):
            bbox = {
                "individual_id": i % 16,
                "x": np.random.random(),
                "y": np.random.random(),
                "w": np.random.random() * 0.3,
                "h": np.random.random() * 0.3,
                "action_id": i % 5,
                "confidence": 0.9
            }
            large_bboxes.append(bbox)
        
        frame_id = "000003"
        self.annotation_manager.save_annotation(frame_id, large_bboxes)
        loaded_bboxes = self.annotation_manager.load_annotation(frame_id)
        self.assertEqual(len(loaded_bboxes), 1000)

    def test_annotation_crud(self):
        # アノテーションのCRUD操作テスト
        frame_id = "000004"
        
        # Create
        self.annotation_manager.save_annotation(frame_id, self.sample_annotation["bboxes"])
        
        # Read
        loaded = self.annotation_manager.load_annotation(frame_id)
        self.assertEqual(len(loaded), 1)
        
        # Update
        updated_bbox = self.sample_annotation["bboxes"][0].copy()
        updated_bbox["x"] = 0.6
        self.annotation_manager.update_annotation(frame_id, 0, updated_bbox)
        
        # Delete
        self.annotation_manager.delete_annotation(frame_id)
        self.assertFalse(Path(self.temp_dir, f"{frame_id}.txt").exists())

    def test_coordinate_conversion(self):
        # 座標変換の正確性テスト
        frame_id = "000005"
        bbox = self.sample_annotation["bboxes"][0]
        
        # YOLO形式 → ピクセル座標 → YOLO形式の変換
        pixel_bbox = self.annotation_manager.yolo_to_pixel(bbox, 1920, 1080)
        converted_bbox = self.annotation_manager.pixel_to_yolo(pixel_bbox, 1920, 1080)
        
        self.assertAlmostEqual(bbox["x"], converted_bbox["x"], places=6)
        self.assertAlmostEqual(bbox["y"], converted_bbox["y"], places=6)

    def test_backup_restore(self):
        # バックアップとリストア機能のテスト
        frame_id = "000006"
        self.annotation_manager.save_annotation(frame_id, self.sample_annotation["bboxes"])
        
        # バックアップ作成
        backup_path = self.annotation_manager.create_backup()
        
        # 元データ削除
        self.annotation_manager.delete_annotation(frame_id)
        
        # リストア
        self.annotation_manager.restore_from_backup(backup_path)
        restored = self.annotation_manager.load_annotation(frame_id)
        self.assertEqual(len(restored), 1)

    def test_error_handling(self):
        # エラーハンドリングテスト
        
        # 破損ファイル
        corrupt_path = Path(self.temp_dir, "corrupt.txt")
        corrupt_path.write_text("invalid data")
        with self.assertRaises(ValueError):
            self.annotation_manager.load_annotation("corrupt")
        
        # 権限エラー
        if os.name != 'nt':  # Windowsでは権限テストをスキップ
            readonly_path = Path(self.temp_dir, "readonly.txt")
            readonly_path.touch()
            os.chmod(readonly_path, 0o444)
            with self.assertRaises(PermissionError):
                self.annotation_manager.save_annotation("readonly", self.sample_annotation["bboxes"])

if __name__ == '__main__':
    unittest.main()