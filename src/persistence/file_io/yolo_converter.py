"""
YOLO形式変換ユーティリティ
座標変換・フォーマット変換の最適化実装
"""

from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

from .txt_handler import BBEntity, Coordinates
from ..exceptions import ValidationError


@dataclass
class PixelCoordinates:
    """ピクセル座標（絶対座標）"""
    x: int  # 左上X座標
    y: int  # 左上Y座標
    w: int  # 幅
    h: int  # 高さ


class YOLOConverter:
    """
    YOLO形式変換ユーティリティ
    
    機能:
    - ピクセル座標 ↔ YOLO正規化座標変換
    - 他形式（COCO、CSV）への変換
    - 高速一括変換
    """
    
    @staticmethod
    def pixel_to_yolo(pixel_coords: PixelCoordinates, 
                     image_width: int, image_height: int) -> Coordinates:
        """
        ピクセル座標→YOLO正規化座標変換
        
        Args:
            pixel_coords: ピクセル座標（左上基点）
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            Coordinates: YOLO正規化座標（中心基点）
        """
        if image_width <= 0 or image_height <= 0:
            raise ValidationError(f"Invalid image dimensions: {image_width}x{image_height}")
            
        # 左上基点→中心基点変換
        center_x = pixel_coords.x + pixel_coords.w / 2
        center_y = pixel_coords.y + pixel_coords.h / 2
        
        # 正規化
        x_norm = center_x / image_width
        y_norm = center_y / image_height
        w_norm = pixel_coords.w / image_width
        h_norm = pixel_coords.h / image_height
        
        # 範囲チェック
        if not (0.0 <= x_norm <= 1.0 and 0.0 <= y_norm <= 1.0 and
                0.0 <= w_norm <= 1.0 and 0.0 <= h_norm <= 1.0):
            raise ValidationError(f"Coordinates out of bounds: ({x_norm}, {y_norm}, {w_norm}, {h_norm})")
            
        return Coordinates(x_norm, y_norm, w_norm, h_norm)
        
    @staticmethod
    def yolo_to_pixel(yolo_coords: Coordinates,
                     image_width: int, image_height: int) -> PixelCoordinates:
        """
        YOLO正規化座標→ピクセル座標変換
        
        Args:
            yolo_coords: YOLO正規化座標（中心基点）
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            PixelCoordinates: ピクセル座標（左上基点）
        """
        if image_width <= 0 or image_height <= 0:
            raise ValidationError(f"Invalid image dimensions: {image_width}x{image_height}")
            
        # 非正規化
        center_x = yolo_coords.x * image_width
        center_y = yolo_coords.y * image_height
        width = yolo_coords.w * image_width
        height = yolo_coords.h * image_height
        
        # 中心基点→左上基点変換
        x = int(center_x - width / 2)
        y = int(center_y - height / 2)
        w = int(width)
        h = int(height)
        
        # 境界制限
        x = max(0, min(x, image_width - 1))
        y = max(0, min(y, image_height - 1))
        w = max(1, min(w, image_width - x))
        h = max(1, min(h, image_height - y))
        
        return PixelCoordinates(x, y, w, h)
        
    @staticmethod
    def batch_pixel_to_yolo(pixel_coords_list: List[PixelCoordinates],
                           image_width: int, image_height: int) -> List[Coordinates]:
        """ピクセル座標一括変換（高速化）"""
        return [YOLOConverter.pixel_to_yolo(coords, image_width, image_height)
                for coords in pixel_coords_list]
                
    @staticmethod
    def batch_yolo_to_pixel(yolo_coords_list: List[Coordinates],
                           image_width: int, image_height: int) -> List[PixelCoordinates]:
        """YOLO座標一括変換（高速化）"""
        return [YOLOConverter.yolo_to_pixel(coords, image_width, image_height)
                for coords in yolo_coords_list]
                
    @staticmethod
    def to_coco_format(bb_entities: List[BBEntity], 
                      image_width: int, image_height: int) -> List[Dict[str, Any]]:
        """
        COCO形式変換
        
        Returns:
            List[Dict]: COCO形式アノテーション
        """
        coco_annotations = []
        
        for i, bb in enumerate(bb_entities):
            pixel_coords = YOLOConverter.yolo_to_pixel(bb.coordinates, image_width, image_height)
            
            annotation = {
                "id": i + 1,
                "image_id": int(bb.frame_id),
                "category_id": bb.action_id + 1,  # COCOは1始まり
                "bbox": [pixel_coords.x, pixel_coords.y, pixel_coords.w, pixel_coords.h],
                "area": pixel_coords.w * pixel_coords.h,
                "iscrowd": 0,
                "individual_id": bb.individual_id,
                "confidence": bb.confidence
            }
            coco_annotations.append(annotation)
            
        return coco_annotations
        
    @staticmethod
    def to_csv_format(bb_entities: List[BBEntity]) -> List[List[str]]:
        """
        CSV形式変換
        
        Returns:
            List[List[str]]: CSV行データ
        """
        headers = ["frame_id", "individual_id", "action_id", "x", "y", "w", "h", "confidence"]
        rows = [headers]
        
        for bb in bb_entities:
            row = [
                bb.frame_id,
                str(bb.individual_id),
                str(bb.action_id),
                f"{bb.coordinates.x:.4f}",
                f"{bb.coordinates.y:.4f}",
                f"{bb.coordinates.w:.4f}",
                f"{bb.coordinates.h:.4f}",
                f"{bb.confidence:.4f}"
            ]
            rows.append(row)
            
        return rows
        
    @staticmethod
    def validate_coordinates_range(coords: Coordinates) -> bool:
        """座標範囲検証"""
        return (0.0 <= coords.x <= 1.0 and 0.0 <= coords.y <= 1.0 and
                0.0 <= coords.w <= 1.0 and 0.0 <= coords.h <= 1.0)
                
    @staticmethod
    def normalize_confidence(confidence: float) -> float:
        """信頼度正規化（0.0-1.0範囲）"""
        return max(0.0, min(1.0, confidence))