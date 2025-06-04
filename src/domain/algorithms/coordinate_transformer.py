"""
座標変換アルゴリズム - Agent3専用
高速座標変換・バッチ処理・NumPy最適化

パフォーマンス要件:
- 単体座標変換: 0.5ms以下
- バッチ座標変換: 100件/5ms以下
"""

import time
from typing import List
import numpy as np

from ..value_objects.coordinates import Coordinates, PixelCoordinates
from ..entities.bb_entity import BBEntity
from ..exceptions import PerformanceError, ValidationError


class CoordinateTransformer:
    """
    高速座標変換エンジン
    
    変換種別:
    - YOLO正規化座標 ↔ ピクセル座標
    - 単体変換・バッチ変換対応
    - NumPy最適化による高速処理
    """
    
    @staticmethod
    def yolo_to_pixel(coordinates: Coordinates, 
                     image_width: int, image_height: int) -> PixelCoordinates:
        """
        YOLO→ピクセル座標変換 (パフォーマンス要件: 0.5ms以下)
        
        Args:
            coordinates: YOLO正規化座標
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            PixelCoordinates: ピクセル座標
            
        Raises:
            PerformanceError: 0.5ms超過時
        """
        start_time = time.perf_counter()
        
        result = coordinates.to_pixel_coordinates(image_width, image_height)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 0.5:
            raise PerformanceError("yolo_to_pixel_transform", elapsed, 0.5)
        
        return result
    
    @staticmethod
    def pixel_to_yolo(pixel_coordinates: PixelCoordinates,
                     image_width: int, image_height: int) -> Coordinates:
        """
        ピクセル→YOLO座標変換 (パフォーマンス要件: 0.5ms以下)
        
        Args:
            pixel_coordinates: ピクセル座標
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            Coordinates: YOLO正規化座標
            
        Raises:
            PerformanceError: 0.5ms超過時
        """
        start_time = time.perf_counter()
        
        result = pixel_coordinates.to_yolo_coordinates(image_width, image_height)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 0.5:
            raise PerformanceError("pixel_to_yolo_transform", elapsed, 0.5)
        
        return result
    
    @staticmethod
    def batch_yolo_to_pixel(coordinates_list: List[Coordinates],
                           image_width: int, image_height: int) -> List[PixelCoordinates]:
        """
        バッチYOLO→ピクセル座標変換 (NumPy最適化)
        
        Args:
            coordinates_list: YOLO座標リスト
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            List[PixelCoordinates]: ピクセル座標リスト
            
        Raises:
            PerformanceError: 性能要件違反時
        """
        start_time = time.perf_counter()
        
        if not coordinates_list:
            return []
        
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
        target_time = len(coordinates_list) * 0.05  # 0.05ms per coordinate
        if elapsed > target_time:
            raise PerformanceError("batch_yolo_to_pixel_transform", elapsed, target_time)
        
        return result
    
    @staticmethod
    def batch_pixel_to_yolo(pixel_coordinates_list: List[PixelCoordinates],
                           image_width: int, image_height: int) -> List[Coordinates]:
        """
        バッチピクセル→YOLO座標変換 (NumPy最適化)
        
        Args:
            pixel_coordinates_list: ピクセル座標リスト
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            List[Coordinates]: YOLO正規化座標リスト
            
        Raises:
            PerformanceError: 性能要件違反時
        """
        start_time = time.perf_counter()
        
        if not pixel_coordinates_list:
            return []
        
        # NumPy配列化で高速計算
        pixel_array = np.array([[c.x, c.y, c.w, c.h] for c in pixel_coordinates_list], dtype=float)
        
        # ベクトル化変換
        yolo_coords = pixel_array.copy()
        yolo_coords[:, 0] /= image_width   # x
        yolo_coords[:, 1] /= image_height  # y
        yolo_coords[:, 2] /= image_width   # w
        yolo_coords[:, 3] /= image_height  # h
        
        # Coordinatesオブジェクト生成
        result = [Coordinates(row[0], row[1], row[2], row[3]) for row in yolo_coords]
        
        elapsed = (time.perf_counter() - start_time) * 1000
        target_time = len(pixel_coordinates_list) * 0.05  # 0.05ms per coordinate
        if elapsed > target_time:
            raise PerformanceError("batch_pixel_to_yolo_transform", elapsed, target_time)
        
        return result
    
    @staticmethod
    def transform_bb_to_pixel(bb: BBEntity, 
                             image_width: int, image_height: int) -> dict:
        """
        BBエンティティのピクセル座標変換
        
        Args:
            bb: BBエンティティ
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            dict: ピクセル座標情報
        """
        pixel_coords = CoordinateTransformer.yolo_to_pixel(
            bb.coordinates, image_width, image_height
        )
        
        left, top, width, height = pixel_coords.get_bounding_rect()
        
        return {
            "bb_id": bb.id,
            "individual_id": bb.individual_id.value,
            "action_type": int(bb.action_type),
            "center_x": pixel_coords.x,
            "center_y": pixel_coords.y,
            "width": pixel_coords.w,
            "height": pixel_coords.h,
            "left": left,
            "top": top,
            "right": left + width,
            "bottom": top + height,
            "confidence": bb.confidence.value
        }
    
    @staticmethod
    def batch_transform_bbs_to_pixel(bb_list: List[BBEntity],
                                   image_width: int, image_height: int) -> List[dict]:
        """
        BBエンティティリストのバッチピクセル座標変換
        
        Args:
            bb_list: BBエンティティリスト
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            List[dict]: ピクセル座標情報リスト
        """
        if not bb_list:
            return []
        
        # 座標のみバッチ変換
        coordinates_list = [bb.coordinates for bb in bb_list]
        pixel_coordinates_list = CoordinateTransformer.batch_yolo_to_pixel(
            coordinates_list, image_width, image_height
        )
        
        # 結果辞書生成
        result = []
        for bb, pixel_coords in zip(bb_list, pixel_coordinates_list):
            left, top, width, height = pixel_coords.get_bounding_rect()
            
            result.append({
                "bb_id": bb.id,
                "individual_id": bb.individual_id.value,
                "action_type": int(bb.action_type),
                "center_x": pixel_coords.x,
                "center_y": pixel_coords.y,
                "width": pixel_coords.w,
                "height": pixel_coords.h,
                "left": left,
                "top": top,
                "right": left + width,
                "bottom": top + height,
                "confidence": bb.confidence.value
            })
        
        return result
    
    @staticmethod
    def validate_image_dimensions(width: int, height: int) -> None:
        """画像寸法検証"""
        if width <= 0 or height <= 0:
            raise ValidationError("image_dimensions", f"{width}x{height}", "positive integers")
        
        # 最大解像度チェック（8K上限）
        if width > 7680 or height > 4320:
            raise ValidationError("image_dimensions", f"{width}x{height}", "≤8K (7680x4320)")
    
    @staticmethod
    def get_scale_factors(source_width: int, source_height: int,
                         target_width: int, target_height: int) -> tuple[float, float]:
        """スケール係数取得"""
        CoordinateTransformer.validate_image_dimensions(source_width, source_height)
        CoordinateTransformer.validate_image_dimensions(target_width, target_height)
        
        scale_x = target_width / source_width
        scale_y = target_height / source_height
        
        return (scale_x, scale_y)
    
    @staticmethod
    def scale_coordinates(coordinates: Coordinates,
                         scale_x: float, scale_y: float) -> Coordinates:
        """座標スケーリング"""
        if scale_x <= 0 or scale_y <= 0:
            raise ValidationError("scale_factors", f"({scale_x}, {scale_y})", "positive numbers")
        
        return Coordinates(
            x=coordinates.x,  # 正規化座標なのでスケーリング不要
            y=coordinates.y,  # 正規化座標なのでスケーリング不要
            w=coordinates.w,  # 正規化座標なのでスケーリング不要
            h=coordinates.h   # 正規化座標なのでスケーリング不要
        )