"""
IOU計算ユーティリティ
YOLO形式座標（中心座標）でのIOU計算
"""

from typing import Dict, Tuple


def calculate_iou(bb1: Dict, bb2: Dict) -> float:
    """
    2つのBB間のIOU（Intersection over Union）を計算
    
    Args:
        bb1: BBデータ {'x': float, 'y': float, 'w': float, 'h': float}
        bb2: BBデータ {'x': float, 'y': float, 'w': float, 'h': float}
        
    Returns:
        float: IOU値（0.0-1.0）
    """
    # YOLO形式（中心座標）から左上・右下座標に変換
    x1_min = bb1['x'] - bb1['w'] / 2
    y1_min = bb1['y'] - bb1['h'] / 2
    x1_max = bb1['x'] + bb1['w'] / 2
    y1_max = bb1['y'] + bb1['h'] / 2
    
    x2_min = bb2['x'] - bb2['w'] / 2
    y2_min = bb2['y'] - bb2['h'] / 2
    x2_max = bb2['x'] + bb2['w'] / 2
    y2_max = bb2['y'] + bb2['h'] / 2
    
    # 交差領域の計算
    intersection_xmin = max(x1_min, x2_min)
    intersection_ymin = max(y1_min, y2_min)
    intersection_xmax = min(x1_max, x2_max)
    intersection_ymax = min(y1_max, y2_max)
    
    # 交差していない場合
    if intersection_xmin >= intersection_xmax or intersection_ymin >= intersection_ymax:
        return 0.0
    
    # 交差領域の面積
    intersection_area = (intersection_xmax - intersection_xmin) * (intersection_ymax - intersection_ymin)
    
    # 各BBの面積
    bb1_area = bb1['w'] * bb1['h']
    bb2_area = bb2['w'] * bb2['h']
    
    # 和集合の面積
    union_area = bb1_area + bb2_area - intersection_area
    
    # IOU計算
    return intersection_area / union_area if union_area > 0 else 0.0


def has_high_overlap(new_bb: Dict, existing_bbs: list, 
                     individual_id: int, iou_threshold: float = 0.8) -> Tuple[bool, float]:
    """
    新しいBBが既存BBと高い重複度を持つかチェック
    
    Args:
        new_bb: 新しいBBデータ
        existing_bbs: 既存BBリスト
        individual_id: チェック対象の個体ID
        iou_threshold: IOU閾値（デフォルト: 0.8）
        
    Returns:
        Tuple[bool, float]: (重複あり, 最大IOU値)
    """
    max_iou = 0.0
    
    for existing_bb in existing_bbs:
        # 同じ個体IDのBBのみチェック
        if existing_bb.get('individual_id') == individual_id:
            iou = calculate_iou(new_bb, existing_bb)
            max_iou = max(max_iou, iou)
            
            if iou > iou_threshold:
                return True, iou
                
    return False, max_iou