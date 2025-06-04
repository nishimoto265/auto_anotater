"""
座標値オブジェクト - Agent3専用
YOLO正規化座標・ピクセル座標の高速変換・IOU計算

パフォーマンス要件:
- IOU計算: 1ms以下
- 座標変換: 0.5ms以下 
- 重複判定: 0.5ms以下
"""

import time
from dataclasses import dataclass
from typing import Tuple
import numpy as np

from ..exceptions import ValidationError, PerformanceError


@dataclass(frozen=True)
class Coordinates:
    """
    YOLO正規化座標値オブジェクト
    
    座標系: 中心X, 中心Y, 幅, 高さ (すべて0.0-1.0)
    不変性: dataclass(frozen=True)により保証
    """
    
    x: float  # 中心X座標 (0.0-1.0)
    y: float  # 中心Y座標 (0.0-1.0) 
    w: float  # 幅 (0.0-1.0)
    h: float  # 高さ (0.0-1.0)
    
    def __post_init__(self):
        """座標検証 - YOLO正規化座標範囲確認"""
        for coord_name, coord_value in [('x', self.x), ('y', self.y), ('w', self.w), ('h', self.h)]:
            if not 0.0 <= coord_value <= 1.0:
                raise ValidationError(coord_name, coord_value, "0.0-1.0")
        
        # 幅・高さが0でないことを確認
        if self.w <= 0.0 or self.h <= 0.0:
            raise ValidationError("width/height", f"w={self.w}, h={self.h}", "> 0.0")
    
    def to_pixel_coordinates(self, image_width: int, image_height: int) -> 'PixelCoordinates':
        """
        YOLO→ピクセル座標変換 (パフォーマンス要件: 0.5ms以下)
        
        Args:
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            PixelCoordinates: ピクセル座標
            
        Raises:
            PerformanceError: 0.5ms超過時
        """
        start_time = time.perf_counter()
        
        # 高速整数変換
        pixel_x = int(self.x * image_width)
        pixel_y = int(self.y * image_height)
        pixel_w = int(self.w * image_width)
        pixel_h = int(self.h * image_height)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 0.5:
            raise PerformanceError("coordinate_transform", elapsed, 0.5)
        
        return PixelCoordinates(pixel_x, pixel_y, pixel_w, pixel_h)
    
    def iou_with(self, other: 'Coordinates') -> float:
        """
        IOU計算 (パフォーマンス要件: 1ms以下)
        
        Args:
            other: 比較対象座標
            
        Returns:
            float: IOU値 (0.0-1.0)
            
        Raises:
            PerformanceError: 1ms超過時
        """
        start_time = time.perf_counter()
        
        # 高速計算のため変数事前計算
        x1_min = self.x - self.w * 0.5
        y1_min = self.y - self.h * 0.5
        x1_max = self.x + self.w * 0.5
        y1_max = self.y + self.h * 0.5
        
        x2_min = other.x - other.w * 0.5
        y2_min = other.y - other.h * 0.5
        x2_max = other.x + other.w * 0.5
        y2_max = other.y + other.h * 0.5
        
        # 交差領域計算
        intersection_xmin = max(x1_min, x2_min)
        intersection_ymin = max(y1_min, y2_min)
        intersection_xmax = min(x1_max, x2_max)
        intersection_ymax = min(y1_max, y2_max)
        
        # 交差なしの場合
        if intersection_xmin >= intersection_xmax or intersection_ymin >= intersection_ymax:
            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > 1.0:
                raise PerformanceError("iou_calculation", elapsed, 1.0)
            return 0.0
        
        # 面積計算
        intersection_area = (intersection_xmax - intersection_xmin) * (intersection_ymax - intersection_ymin)
        area1 = self.w * self.h
        area2 = other.w * other.h
        union_area = area1 + area2 - intersection_area
        
        iou = intersection_area / union_area if union_area > 0 else 0.0
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1.0:
            raise PerformanceError("iou_calculation", elapsed, 1.0)
        
        return iou
    
    def overlaps_with(self, other: 'Coordinates', threshold: float = 0.1) -> bool:
        """
        重複判定 (パフォーマンス要件: 0.5ms以下)
        
        Args:
            other: 比較対象座標
            threshold: 重複判定閾値
            
        Returns:
            bool: 重複判定結果
        """
        start_time = time.perf_counter()
        result = self.iou_with(other) > threshold
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 0.5:
            raise PerformanceError("overlap_detection", elapsed, 0.5)
        return result
    
    def get_area(self) -> float:
        """BB面積取得 (YOLO正規化座標)"""
        return self.w * self.h
    
    def get_center(self) -> Tuple[float, float]:
        """BB中心座標取得"""
        return (self.x, self.y)
    
    def get_corners(self) -> Tuple[float, float, float, float]:
        """BB四隅座標取得 (左上X, 左上Y, 右下X, 右下Y)"""
        x_min = self.x - self.w * 0.5
        y_min = self.y - self.h * 0.5
        x_max = self.x + self.w * 0.5
        y_max = self.y + self.h * 0.5
        return (x_min, y_min, x_max, y_max)


@dataclass(frozen=True)
class PixelCoordinates:
    """
    ピクセル座標値オブジェクト
    
    座標系: 中心X, 中心Y, 幅, 高さ (ピクセル単位)
    用途: UI描画・マウス操作
    """
    
    x: int  # 中心X座標 (ピクセル)
    y: int  # 中心Y座標 (ピクセル)
    w: int  # 幅 (ピクセル)
    h: int  # 高さ (ピクセル)
    
    def __post_init__(self):
        """ピクセル座標検証"""
        if self.w <= 0 or self.h <= 0:
            raise ValidationError("pixel_width/height", f"w={self.w}, h={self.h}", "> 0")
    
    def to_yolo_coordinates(self, image_width: int, image_height: int) -> Coordinates:
        """
        ピクセル→YOLO座標変換 (パフォーマンス要件: 0.5ms以下)
        
        Args:
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            Coordinates: YOLO正規化座標
        """
        start_time = time.perf_counter()
        
        # 高速浮動小数点変換
        yolo_x = self.x / image_width
        yolo_y = self.y / image_height
        yolo_w = self.w / image_width
        yolo_h = self.h / image_height
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 0.5:
            raise PerformanceError("pixel_to_yolo_transform", elapsed, 0.5)
        
        return Coordinates(yolo_x, yolo_y, yolo_w, yolo_h)
    
    def get_bounding_rect(self) -> Tuple[int, int, int, int]:
        """描画用矩形座標取得 (左上X, 左上Y, 幅, 高さ)"""
        left = self.x - self.w // 2
        top = self.y - self.h // 2
        return (left, top, self.w, self.h)
    
    def contains_point(self, px: int, py: int) -> bool:
        """点が矩形内に含まれるかチェック"""
        left = self.x - self.w // 2
        top = self.y - self.h // 2
        right = left + self.w
        bottom = top + self.h
        return left <= px <= right and top <= py <= bottom


def batch_coordinate_transform(coordinates_list: list[Coordinates], 
                             image_width: int, 
                             image_height: int) -> list[PixelCoordinates]:
    """
    一括座標変換 (NumPy最適化版)
    
    Args:
        coordinates_list: YOLO座標リスト
        image_width: 画像幅
        image_height: 画像高さ
        
    Returns:
        list[PixelCoordinates]: ピクセル座標リスト
    """
    if not coordinates_list:
        return []
    
    start_time = time.perf_counter()
    
    # NumPy配列化で高速計算
    coords_array = np.array([[c.x, c.y, c.w, c.h] for c in coordinates_list])
    
    # ベクトル化変換
    pixel_coords = coords_array.copy()
    pixel_coords[:, 0] *= image_width   # x
    pixel_coords[:, 1] *= image_height  # y
    pixel_coords[:, 2] *= image_width   # w
    pixel_coords[:, 3] *= image_height  # h
    
    # 整数変換
    pixel_coords = pixel_coords.astype(int)
    
    # PixelCoordinatesオブジェクト生成
    result = [PixelCoordinates(row[0], row[1], row[2], row[3]) for row in pixel_coords]
    
    elapsed = (time.perf_counter() - start_time) * 1000
    target_time = len(coordinates_list) * 0.5  # 0.5ms per coordinate
    if elapsed > target_time:
        raise PerformanceError("batch_coordinate_transform", elapsed, target_time)
    
    return result