"""
IOU計算アルゴリズム - Agent3専用
高速IOU計算エンジン・NumPy最適化・バッチ処理

パフォーマンス要件:
- 単体IOU計算: 1ms以下
- バッチIOU計算: 100ペア/10ms以下
- メモリ効率: NumPy vectorized計算
"""

import time
from typing import List, Tuple
import numpy as np
from functools import lru_cache

from ..entities.bb_entity import BBEntity
from ..value_objects.coordinates import Coordinates
from ..exceptions import PerformanceError


class IOUCalculator:
    """
    高速IOU計算エンジン
    
    最適化技術:
    - NumPy vectorized計算
    - LRUキャッシュによる重複計算回避
    - メモリ効率的なバッチ処理
    """
    
    @staticmethod
    def calculate_iou(bb1: BBEntity, bb2: BBEntity) -> float:
        """
        単体IOU計算 (パフォーマンス要件: 1ms以下)
        
        Args:
            bb1: BB1エンティティ
            bb2: BB2エンティティ
            
        Returns:
            float: IOU値（0.0-1.0）
            
        Raises:
            PerformanceError: 1ms超過時
        """
        start_time = time.perf_counter()
        
        result = bb1.coordinates.iou_with(bb2.coordinates)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1.0:
            raise PerformanceError("single_iou_calculation", elapsed, 1.0)
        
        return result
    
    @staticmethod
    def calculate_iou_matrix(bb_list1: List[BBEntity], 
                           bb_list2: List[BBEntity]) -> np.ndarray:
        """
        IOU行列計算 (パフォーマンス要件: バッチ処理最適化)
        
        Args:
            bb_list1: BBリスト1
            bb_list2: BBリスト2
            
        Returns:
            np.ndarray: IOU行列（len(bb_list1) x len(bb_list2)）
            
        Raises:
            PerformanceError: 性能要件違反時
        """
        start_time = time.perf_counter()
        
        if not bb_list1 or not bb_list2:
            return np.zeros((len(bb_list1), len(bb_list2)))
        
        # NumPy配列化で高速計算
        coords1 = np.array([[bb.coordinates.x, bb.coordinates.y, 
                           bb.coordinates.w, bb.coordinates.h] 
                          for bb in bb_list1])
        coords2 = np.array([[bb.coordinates.x, bb.coordinates.y,
                           bb.coordinates.w, bb.coordinates.h] 
                          for bb in bb_list2])
        
        iou_matrix = IOUCalculator._vectorized_iou_calculation(coords1, coords2)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        target_time = len(bb_list1) * len(bb_list2) * 0.1  # 0.1ms per pair
        if elapsed > target_time:
            raise PerformanceError("batch_iou_calculation", elapsed, target_time)
        
        return iou_matrix
    
    @staticmethod
    def _vectorized_iou_calculation(coords1: np.ndarray, 
                                  coords2: np.ndarray) -> np.ndarray:
        """
        NumPy vectorized IOU計算
        
        Args:
            coords1: 座標配列1 (N x 4: x, y, w, h)
            coords2: 座標配列2 (M x 4: x, y, w, h)
            
        Returns:
            np.ndarray: IOU行列 (N x M)
        """
        # BB1の四隅座標計算 (N x 4)
        x1_min = coords1[:, 0] - coords1[:, 2] * 0.5
        y1_min = coords1[:, 1] - coords1[:, 3] * 0.5
        x1_max = coords1[:, 0] + coords1[:, 2] * 0.5
        y1_max = coords1[:, 1] + coords1[:, 3] * 0.5
        
        # BB2の四隅座標計算 (M x 4)
        x2_min = coords2[:, 0] - coords2[:, 2] * 0.5
        y2_min = coords2[:, 1] - coords2[:, 3] * 0.5
        x2_max = coords2[:, 0] + coords2[:, 2] * 0.5
        y2_max = coords2[:, 1] + coords2[:, 3] * 0.5
        
        # ブロードキャストによる全ペア計算 (N x M)
        intersection_xmin = np.maximum(x1_min[:, np.newaxis], x2_min[np.newaxis, :])
        intersection_ymin = np.maximum(y1_min[:, np.newaxis], y2_min[np.newaxis, :])
        intersection_xmax = np.minimum(x1_max[:, np.newaxis], x2_max[np.newaxis, :])
        intersection_ymax = np.minimum(y1_max[:, np.newaxis], y2_max[np.newaxis, :])
        
        # 交差領域幅・高さ計算
        intersection_width = np.maximum(0, intersection_xmax - intersection_xmin)
        intersection_height = np.maximum(0, intersection_ymax - intersection_ymin)
        intersection_area = intersection_width * intersection_height
        
        # 各BBの面積計算
        area1 = coords1[:, 2] * coords1[:, 3]  # (N,)
        area2 = coords2[:, 2] * coords2[:, 3]  # (M,)
        
        # Union面積計算 (N x M)
        union_area = area1[:, np.newaxis] + area2[np.newaxis, :] - intersection_area
        
        # IOU計算 (ゼロ除算回避)
        iou_matrix = np.divide(intersection_area, union_area, 
                              out=np.zeros_like(intersection_area), 
                              where=union_area > 0)
        
        return iou_matrix
    
    @staticmethod
    @lru_cache(maxsize=10000)
    def calculate_cached_iou(coords1_tuple: Tuple[float, float, float, float],
                           coords2_tuple: Tuple[float, float, float, float]) -> float:
        """
        キャッシュ付きIOU計算 (重複計算回避)
        
        Args:
            coords1_tuple: 座標1タプル (x, y, w, h)
            coords2_tuple: 座標2タプル (x, y, w, h)
            
        Returns:
            float: IOU値（0.0-1.0）
        """
        coords1 = Coordinates(*coords1_tuple)
        coords2 = Coordinates(*coords2_tuple)
        return coords1.iou_with(coords2)
    
    @staticmethod
    def find_best_matches(source_bbs: List[BBEntity], 
                         target_bbs: List[BBEntity],
                         iou_threshold: float = 0.5) -> List[Tuple[str, str, float]]:
        """
        最適マッチング検索 (追跡用)
        
        Args:
            source_bbs: 追跡元BBリスト
            target_bbs: 追跡先BBリスト
            iou_threshold: IOU閾値
            
        Returns:
            List[Tuple[source_id, target_id, iou_score]]: マッチング結果
        """
        if not source_bbs or not target_bbs:
            return []
        
        # IOU行列計算
        iou_matrix = IOUCalculator.calculate_iou_matrix(source_bbs, target_bbs)
        
        matches = []
        used_targets = set()
        
        # 貪欲マッチング（最高IOUから順に割り当て）
        for source_idx in range(len(source_bbs)):
            best_target_idx = -1
            best_iou = iou_threshold
            
            for target_idx in range(len(target_bbs)):
                if target_idx in used_targets:
                    continue
                
                iou_score = iou_matrix[source_idx, target_idx]
                if iou_score > best_iou:
                    best_iou = iou_score
                    best_target_idx = target_idx
            
            if best_target_idx >= 0:
                matches.append((
                    source_bbs[source_idx].id,
                    target_bbs[best_target_idx].id,
                    best_iou
                ))
                used_targets.add(best_target_idx)
        
        return matches
    
    @staticmethod
    def calculate_overlap_statistics(bb_list: List[BBEntity], 
                                   threshold: float = 0.1) -> dict:
        """
        重複統計計算
        
        Args:
            bb_list: BBリスト
            threshold: 重複判定閾値
            
        Returns:
            dict: 重複統計情報
        """
        if len(bb_list) < 2:
            return {
                "total_pairs": 0,
                "overlapping_pairs": 0,
                "overlap_ratio": 0.0,
                "max_iou": 0.0,
                "avg_iou": 0.0
            }
        
        # 自己IOU行列計算
        iou_matrix = IOUCalculator.calculate_iou_matrix(bb_list, bb_list)
        
        # 上三角部分のみ抽出（自分自身は除外）
        upper_triangle = np.triu(iou_matrix, k=1)
        iou_values = upper_triangle[upper_triangle > 0]
        
        total_pairs = len(iou_values)
        overlapping_pairs = np.sum(iou_values > threshold)
        
        return {
            "total_pairs": total_pairs,
            "overlapping_pairs": overlapping_pairs,
            "overlap_ratio": overlapping_pairs / total_pairs if total_pairs > 0 else 0.0,
            "max_iou": np.max(iou_values) if len(iou_values) > 0 else 0.0,
            "avg_iou": np.mean(iou_values) if len(iou_values) > 0 else 0.0
        }
    
    @staticmethod
    def clear_cache():
        """キャッシュクリア"""
        IOUCalculator.calculate_cached_iou.cache_clear()
    
    @staticmethod
    def get_cache_info():
        """キャッシュ情報取得"""
        return IOUCalculator.calculate_cached_iou.cache_info()