"""
座標値オブジェクト単体テスト - Agent3専用
IOU計算1ms以下・座標変換0.5ms以下のパフォーマンステスト
"""

import time
import pytest
import numpy as np

from src.domain.value_objects.coordinates import Coordinates, PixelCoordinates, batch_coordinate_transform
from src.domain.exceptions import ValidationError, PerformanceError


class TestCoordinates:
    """YOLO正規化座標テスト"""
    
    def test_coordinate_validation_success(self):
        """座標検証成功ケース"""
        # 正常範囲
        coords = Coordinates(0.5, 0.5, 0.2, 0.2)
        assert coords.x == 0.5
        assert coords.y == 0.5
        assert coords.w == 0.2
        assert coords.h == 0.2
        
        # 境界値
        coords_boundary = Coordinates(0.0, 0.0, 1.0, 1.0)
        assert coords_boundary.x == 0.0
        assert coords_boundary.y == 0.0
        assert coords_boundary.w == 1.0
        assert coords_boundary.h == 1.0
    
    def test_coordinate_validation_failure(self):
        """座標検証失敗ケース"""
        # X座標範囲外
        with pytest.raises(ValidationError):
            Coordinates(-0.1, 0.5, 0.2, 0.2)
        
        with pytest.raises(ValidationError):
            Coordinates(1.1, 0.5, 0.2, 0.2)
        
        # Y座標範囲外
        with pytest.raises(ValidationError):
            Coordinates(0.5, -0.1, 0.2, 0.2)
        
        with pytest.raises(ValidationError):
            Coordinates(0.5, 1.1, 0.2, 0.2)
        
        # 幅・高さ範囲外
        with pytest.raises(ValidationError):
            Coordinates(0.5, 0.5, -0.1, 0.2)
        
        with pytest.raises(ValidationError):
            Coordinates(0.5, 0.5, 1.1, 0.2)
        
        # 幅・高さがゼロ
        with pytest.raises(ValidationError):
            Coordinates(0.5, 0.5, 0.0, 0.2)
        
        with pytest.raises(ValidationError):
            Coordinates(0.5, 0.5, 0.2, 0.0)
    
    def test_coordinate_transform_performance_0_5ms(self):
        """座標変換0.5ms以下パフォーマンステスト（最重要）"""
        coords = Coordinates(0.5, 0.5, 0.2, 0.2)
        
        # 1000回テストして全て0.5ms以下であることを確認
        times = []
        for _ in range(1000):
            start_time = time.perf_counter()
            pixel_coords = coords.to_pixel_coordinates(1920, 1080)
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)
            
            # 個別確認
            assert elapsed <= 0.5, f"Coordinate transform took {elapsed}ms (target: 0.5ms)"
        
        # 統計確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time <= 0.25, f"Average transform time {avg_time}ms exceeds 0.25ms"
        assert max_time <= 0.5, f"Max transform time {max_time}ms exceeds 0.5ms"
        
        print(f"座標変換パフォーマンス: 平均{avg_time:.3f}ms, 最大{max_time:.3f}ms")
    
    def test_iou_calculation_performance_1ms(self):
        """IOU計算1ms以下パフォーマンステスト（最重要）"""
        coords1 = Coordinates(0.5, 0.5, 0.2, 0.2)
        coords2 = Coordinates(0.6, 0.6, 0.2, 0.2)
        
        # 1000回テストして全て1ms以下であることを確認
        times = []
        for _ in range(1000):
            start_time = time.perf_counter()
            iou = coords1.iou_with(coords2)
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)
            
            # 個別確認
            assert elapsed <= 1.0, f"IOU calculation took {elapsed}ms (target: 1.0ms)"
            assert 0.0 <= iou <= 1.0, f"IOU value {iou} out of range [0.0, 1.0]"
        
        # 統計確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time <= 0.5, f"Average IOU time {avg_time}ms exceeds 0.5ms"
        assert max_time <= 1.0, f"Max IOU time {max_time}ms exceeds 1.0ms"
        
        print(f"IOU計算パフォーマンス: 平均{avg_time:.3f}ms, 最大{max_time:.3f}ms")
    
    def test_iou_calculation_accuracy(self):
        """IOU計算精度テスト"""
        # 完全一致（IOU = 1.0）
        coords1 = Coordinates(0.5, 0.5, 0.2, 0.2)
        coords2 = Coordinates(0.5, 0.5, 0.2, 0.2)
        assert abs(coords1.iou_with(coords2) - 1.0) < 1e-6
        
        # 重複なし（IOU = 0.0）
        coords3 = Coordinates(0.2, 0.2, 0.1, 0.1)
        coords4 = Coordinates(0.8, 0.8, 0.1, 0.1)
        assert abs(coords3.iou_with(coords4) - 0.0) < 1e-6
        
        # 50%重複ケース
        coords5 = Coordinates(0.5, 0.5, 0.4, 0.4)  # 面積: 0.16
        coords6 = Coordinates(0.6, 0.5, 0.4, 0.4)  # 面積: 0.16, 重複面積: 0.12
        expected_iou = 0.12 / (0.16 + 0.16 - 0.12)  # 0.12 / 0.2 = 0.6
        actual_iou = coords5.iou_with(coords6)
        assert abs(actual_iou - expected_iou) < 1e-2
    
    def test_overlap_detection_performance_0_5ms(self):
        """重複判定0.5ms以下パフォーマンステスト"""
        coords1 = Coordinates(0.5, 0.5, 0.2, 0.2)
        coords2 = Coordinates(0.6, 0.6, 0.2, 0.2)
        
        # 1000回テストして全て0.5ms以下であることを確認
        times = []
        for _ in range(1000):
            start_time = time.perf_counter()
            overlaps = coords1.overlaps_with(coords2, 0.1)
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)
            
            # 個別確認
            assert elapsed <= 0.5, f"Overlap detection took {elapsed}ms (target: 0.5ms)"
            assert isinstance(overlaps, bool)
        
        # 統計確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time <= 0.25, f"Average overlap time {avg_time}ms exceeds 0.25ms"
        assert max_time <= 0.5, f"Max overlap time {max_time}ms exceeds 0.5ms"
        
        print(f"重複判定パフォーマンス: 平均{avg_time:.3f}ms, 最大{max_time:.3f}ms")
    
    def test_coordinate_utilities(self):
        """座標ユーティリティ機能テスト"""
        coords = Coordinates(0.5, 0.5, 0.2, 0.2)
        
        # 面積計算
        area = coords.get_area()
        assert abs(area - 0.04) < 1e-6  # 0.2 * 0.2 = 0.04
        
        # 中心座標取得
        center = coords.get_center()
        assert center == (0.5, 0.5)
        
        # 四隅座標取得
        corners = coords.get_corners()
        expected = (0.4, 0.4, 0.6, 0.6)  # (x_min, y_min, x_max, y_max)
        assert all(abs(a - b) < 1e-6 for a, b in zip(corners, expected))


class TestPixelCoordinates:
    """ピクセル座標テスト"""
    
    def test_pixel_coordinate_validation_success(self):
        """ピクセル座標検証成功ケース"""
        pixel_coords = PixelCoordinates(960, 540, 200, 200)
        assert pixel_coords.x == 960
        assert pixel_coords.y == 540
        assert pixel_coords.w == 200
        assert pixel_coords.h == 200
    
    def test_pixel_coordinate_validation_failure(self):
        """ピクセル座標検証失敗ケース"""
        # 幅・高さがゼロ以下
        with pytest.raises(ValidationError):
            PixelCoordinates(100, 100, 0, 100)
        
        with pytest.raises(ValidationError):
            PixelCoordinates(100, 100, 100, 0)
        
        with pytest.raises(ValidationError):
            PixelCoordinates(100, 100, -10, 100)
    
    def test_pixel_to_yolo_transform_performance_0_5ms(self):
        """ピクセル→YOLO変換0.5ms以下パフォーマンステスト"""
        pixel_coords = PixelCoordinates(960, 540, 200, 200)
        
        # 1000回テストして全て0.5ms以下であることを確認
        times = []
        for _ in range(1000):
            start_time = time.perf_counter()
            yolo_coords = pixel_coords.to_yolo_coordinates(1920, 1080)
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)
            
            # 個別確認
            assert elapsed <= 0.5, f"Pixel to YOLO transform took {elapsed}ms (target: 0.5ms)"
        
        # 統計確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time <= 0.25, f"Average transform time {avg_time}ms exceeds 0.25ms"
        assert max_time <= 0.5, f"Max transform time {max_time}ms exceeds 0.5ms"
        
        print(f"ピクセル→YOLO変換パフォーマンス: 平均{avg_time:.3f}ms, 最大{max_time:.3f}ms")
    
    def test_pixel_coordinate_utilities(self):
        """ピクセル座標ユーティリティ機能テスト"""
        pixel_coords = PixelCoordinates(960, 540, 200, 200)
        
        # 描画用矩形座標取得
        rect = pixel_coords.get_bounding_rect()
        expected = (860, 440, 200, 200)  # (left, top, width, height)
        assert rect == expected
        
        # 点含有判定
        assert pixel_coords.contains_point(960, 540)  # 中心
        assert pixel_coords.contains_point(860, 440)  # 左上
        assert pixel_coords.contains_point(1060, 640)  # 右下
        assert not pixel_coords.contains_point(800, 400)  # 外側
        assert not pixel_coords.contains_point(1100, 700)  # 外側


class TestBatchCoordinateTransform:
    """バッチ座標変換テスト"""
    
    def test_batch_transform_performance(self):
        """バッチ座標変換パフォーマンステスト（0.05ms per coordinate）"""
        # 100座標のバッチ変換テスト
        coordinates_list = [
            Coordinates(0.1 + i * 0.01, 0.1 + i * 0.01, 0.05, 0.05)
            for i in range(100)
        ]
        
        start_time = time.perf_counter()
        pixel_coords_list = batch_coordinate_transform(coordinates_list, 1920, 1080)
        elapsed = (time.perf_counter() - start_time) * 1000
        
        # 5ms以下（100座標 * 0.05ms = 5ms）
        assert elapsed <= 5.0, f"Batch transform took {elapsed}ms (target: 5.0ms)"
        
        # 結果検証
        assert len(pixel_coords_list) == 100
        assert all(isinstance(pc, PixelCoordinates) for pc in pixel_coords_list)
        
        print(f"バッチ変換パフォーマンス: {elapsed:.3f}ms for 100 coordinates")
    
    def test_batch_transform_accuracy(self):
        """バッチ座標変換精度テスト"""
        coordinates_list = [
            Coordinates(0.5, 0.5, 0.2, 0.2),
            Coordinates(0.25, 0.25, 0.1, 0.1),
            Coordinates(0.75, 0.75, 0.3, 0.3)
        ]
        
        # バッチ変換
        pixel_coords_list = batch_coordinate_transform(coordinates_list, 1920, 1080)
        
        # 個別変換と比較
        for i, coords in enumerate(coordinates_list):
            expected = coords.to_pixel_coordinates(1920, 1080)
            actual = pixel_coords_list[i]
            
            assert actual.x == expected.x
            assert actual.y == expected.y
            assert actual.w == expected.w
            assert actual.h == expected.h
    
    def test_batch_transform_empty_list(self):
        """空リストのバッチ変換テスト"""
        result = batch_coordinate_transform([], 1920, 1080)
        assert result == []


class TestCoordinateConversion:
    """座標変換往復テスト"""
    
    def test_yolo_pixel_conversion_accuracy(self):
        """YOLO↔ピクセル変換精度テスト（往復変換）"""
        original_coords = Coordinates(0.5, 0.3, 0.2, 0.4)
        
        # YOLO → ピクセル → YOLO
        pixel_coords = original_coords.to_pixel_coordinates(1920, 1080)
        converted_coords = pixel_coords.to_yolo_coordinates(1920, 1080)
        
        # 誤差許容範囲内での一致確認（整数変換による誤差考慮）
        assert abs(converted_coords.x - original_coords.x) < 0.001
        assert abs(converted_coords.y - original_coords.y) < 0.001
        assert abs(converted_coords.w - original_coords.w) < 0.001
        assert abs(converted_coords.h - original_coords.h) < 0.001
    
    def test_conversion_with_different_resolutions(self):
        """異なる解像度での変換テスト"""
        coords = Coordinates(0.5, 0.5, 0.25, 0.25)
        
        resolutions = [
            (1920, 1080),  # FHD
            (3840, 2160),  # 4K
            (1280, 720),   # HD
            (640, 480)     # VGA
        ]
        
        for width, height in resolutions:
            pixel_coords = coords.to_pixel_coordinates(width, height)
            
            # 中心座標確認
            assert pixel_coords.x == width // 2
            assert pixel_coords.y == height // 2
            
            # サイズ確認
            assert pixel_coords.w == width // 4
            assert pixel_coords.h == height // 4