"""
CoordinateValidator - Agent2 Application Layer
座標検証クラス（BBValidatorのサブセット）

機能:
- 座標系変換検証
- ピクセル座標↔YOLO正規化座標
- 座標範囲検証
"""

from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache
import math


@dataclass
class CoordinateTransform:
    """座標変換結果"""
    x: float
    y: float
    w: float
    h: float
    source_format: str
    target_format: str


class CoordinateValidator:
    """
    座標検証クラス
    """
    
    def __init__(self):
        """初期化"""
        pass
    
    @lru_cache(maxsize=1000)
    def validate_yolo_coordinates(self, x: float, y: float, w: float, h: float) -> bool:
        """YOLO正規化座標検証"""
        # 範囲チェック [0.0, 1.0]
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            return False
        
        # 幅・高さの正の値チェック
        if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
            return False
        
        # 境界チェック
        if not (x + w <= 1.0 and y + h <= 1.0):
            return False
        
        return True
    
    def validate_pixel_coordinates(self, x: int, y: int, w: int, h: int, 
                                 image_width: int, image_height: int) -> bool:
        """ピクセル座標検証"""
        # 範囲チェック
        if not (0 <= x < image_width and 0 <= y < image_height):
            return False
        
        # 幅・高さの正の値チェック
        if not (0 < w <= image_width and 0 < h <= image_height):
            return False
        
        # 境界チェック
        if not (x + w <= image_width and y + h <= image_height):
            return False
        
        return True
    
    def pixel_to_yolo(self, x: int, y: int, w: int, h: int, 
                     image_width: int, image_height: int) -> CoordinateTransform:
        """ピクセル座標→YOLO正規化座標変換"""
        yolo_x = x / image_width
        yolo_y = y / image_height
        yolo_w = w / image_width
        yolo_h = h / image_height
        
        return CoordinateTransform(
            x=yolo_x, y=yolo_y, w=yolo_w, h=yolo_h,
            source_format="pixel", target_format="yolo"
        )
    
    def yolo_to_pixel(self, x: float, y: float, w: float, h: float,
                     image_width: int, image_height: int) -> CoordinateTransform:
        """YOLO正規化座標→ピクセル座標変換"""
        pixel_x = int(x * image_width)
        pixel_y = int(y * image_height)
        pixel_w = int(w * image_width)
        pixel_h = int(h * image_height)
        
        return CoordinateTransform(
            x=pixel_x, y=pixel_y, w=pixel_w, h=pixel_h,
            source_format="yolo", target_format="pixel"
        )
    
    def clear_cache(self):
        """キャッシュクリア"""
        self.validate_yolo_coordinates.cache_clear()