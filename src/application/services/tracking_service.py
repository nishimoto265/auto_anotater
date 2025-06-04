"""
TrackingService - Agent2 Application Layer
IOU追跡・ID継承制御サービス

性能要件:
- IOU追跡処理: 5ms以下
- ID継承判定: 3ms以下
- 追跡断絶検知: 2ms以下
- 後続フレーム更新: バッチ処理最適化
"""

import time
import threading
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
import numpy as np
from concurrent.futures import ThreadPoolExecutor


class TrackingError(Exception):
    """追跡処理エラー基底クラス"""
    pass


class IOUCalculationError(TrackingError):
    """IOU計算エラー"""
    pass


class IDInheritanceError(TrackingError):
    """ID継承エラー"""
    pass


@dataclass
class TrackingRequest:
    """追跡要求"""
    source_frame_id: str
    target_frame_id: str
    source_bbs: List[Dict[str, Any]]
    target_bbs: List[Dict[str, Any]]
    iou_threshold: float = 0.5
    individual_ids: Optional[List[int]] = None  # None時は全個体追跡


@dataclass
class TrackingResult:
    """追跡結果"""
    source_frame_id: str
    target_frame_id: str
    matches: List[Dict[str, Any]]  # マッチしたBBペア
    unmatched_source: List[Dict[str, Any]]  # マッチしなかった元BB
    unmatched_target: List[Dict[str, Any]]  # マッチしなかった先BB
    processing_time: float
    iou_threshold: float


@dataclass
class TrackingBreak:
    """追跡断絶情報"""
    individual_id: int
    last_seen_frame: str
    break_frame: str
    last_bb: Dict[str, Any]
    break_type: str  # "disappeared", "id_conflict", "low_confidence"


class PerformanceOptimizer:
    """性能最適化ヘルパー"""
    
    @staticmethod
    @lru_cache(maxsize=10000)
    def calculate_iou_cached(x1: float, y1: float, w1: float, h1: float,
                           x2: float, y2: float, w2: float, h2: float) -> float:
        """IOU計算（キャッシュ付き）"""
        # BB1の座標
        left1, top1 = x1, y1
        right1, bottom1 = x1 + w1, y1 + h1
        
        # BB2の座標
        left2, top2 = x2, y2
        right2, bottom2 = x2 + w2, y2 + h2
        
        # 交差領域
        intersection_left = max(left1, left2)
        intersection_top = max(top1, top2)
        intersection_right = min(right1, right2)
        intersection_bottom = min(bottom1, bottom2)
        
        # 交差面積
        if intersection_left >= intersection_right or intersection_top >= intersection_bottom:
            intersection_area = 0.0
        else:
            intersection_area = (intersection_right - intersection_left) * (intersection_bottom - intersection_top)
        
        # 各BBの面積
        area1 = w1 * h1
        area2 = w2 * h2
        
        # 和集合面積
        union_area = area1 + area2 - intersection_area
        
        # IOU計算
        if union_area == 0:
            return 0.0
        
        return intersection_area / union_area
    
    @staticmethod
    def vectorized_iou_calculation(source_bbs: List[Dict], target_bbs: List[Dict]) -> np.ndarray:
        """ベクトル化IOU計算"""
        if not source_bbs or not target_bbs:
            return np.array([])
        
        # NumPy配列に変換
        source_coords = np.array([[bb["x"], bb["y"], bb["w"], bb["h"]] for bb in source_bbs])
        target_coords = np.array([[bb["x"], bb["y"], bb["w"], bb["h"]] for bb in target_bbs])
        
        # ブロードキャストでIOU計算
        iou_matrix = np.zeros((len(source_bbs), len(target_bbs)))
        
        for i, s_bb in enumerate(source_coords):
            for j, t_bb in enumerate(target_coords):
                iou_matrix[i, j] = PerformanceOptimizer.calculate_iou_cached(
                    s_bb[0], s_bb[1], s_bb[2], s_bb[3],
                    t_bb[0], t_bb[1], t_bb[2], t_bb[3]
                )
        
        return iou_matrix


class TrackingService:
    """
    追跡制御サービス
    
    性能要件:
    - IOU追跡処理: 5ms以下
    - ID継承判定: 3ms以下
    - 追跡断絶検知: 2ms以下
    - 後続フレーム更新: バッチ処理最適化
    """
    
    def __init__(self, domain_service, data_bus, performance_monitor=None):
        """
        初期化
        
        Args:
            domain_service: Domain層サービス
            data_bus: Data Bus通信
            performance_monitor: 性能監視（オプション）
        """
        self.domain_service = domain_service
        self.data_bus = data_bus
        self.performance_monitor = performance_monitor or {}
        self._lock = threading.RLock()
        
        # 性能最適化用キャッシュ
        self._tracking_history = {}  # フレーム間追跡履歴
        self._iou_cache = {}
        
        # 統計情報
        self._stats = {
            "start_tracking": {"times": [], "count": 0},
            "id_inheritance": {"times": [], "count": 0},
            "break_detection": {"times": [], "count": 0}
        }
    
    def _measure_time(self, operation_name: str):
        """時間測定デコレータ"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end = time.perf_counter()
                    exec_time = (end - start) * 1000  # ms
                    
                    with self._lock:
                        if operation_name in self._stats:
                            self._stats[operation_name]["times"].append(exec_time)
                            self._stats[operation_name]["count"] += 1
            return wrapper
        return decorator
    
    def _publish_tracking_event(self, event_type: str, **event_data):
        """追跡イベント発行"""
        try:
            self.data_bus.publish(event_type, **event_data)
        except Exception as e:
            print(f"Warning: Failed to publish {event_type} event: {e}")
    
    @_measure_time("start_tracking")
    def start_tracking(self, request: TrackingRequest) -> TrackingResult:
        """
        追跡処理開始（5ms以下必達）
        
        Args:
            request: 追跡要求
            
        Returns:
            TrackingResult: 追跡結果
            
        Raises:
            TrackingError: 追跡処理エラー
        """
        start_time = time.perf_counter()
        
        try:
            with self._lock:
                # 対象BBフィルタリング
                source_bbs = self._filter_bbs_by_ids(request.source_bbs, request.individual_ids)
                target_bbs = self._filter_bbs_by_ids(request.target_bbs, request.individual_ids)
                
                if not source_bbs or not target_bbs:
                    return TrackingResult(
                        source_frame_id=request.source_frame_id,
                        target_frame_id=request.target_frame_id,
                        matches=[],
                        unmatched_source=source_bbs,
                        unmatched_target=target_bbs,
                        processing_time=0.0,
                        iou_threshold=request.iou_threshold
                    )
                
                # 高速IOU計算（ベクトル化）
                iou_matrix = PerformanceOptimizer.vectorized_iou_calculation(
                    source_bbs, target_bbs
                )
                
                # マッチング実行
                matches, unmatched_source, unmatched_target = self._perform_matching(
                    source_bbs, target_bbs, iou_matrix, request.iou_threshold
                )
                
                processing_time = (time.perf_counter() - start_time) * 1000
                
                # 結果作成
                result = TrackingResult(
                    source_frame_id=request.source_frame_id,
                    target_frame_id=request.target_frame_id,
                    matches=matches,
                    unmatched_source=unmatched_source,
                    unmatched_target=unmatched_target,
                    processing_time=processing_time,
                    iou_threshold=request.iou_threshold
                )
                
                # 追跡履歴更新
                self._update_tracking_history(request.source_frame_id, request.target_frame_id, result)
                
                # 追跡開始イベント発行
                self._publish_tracking_event("tracking_started", 
                                           source_frame_id=request.source_frame_id,
                                           target_frame_id=request.target_frame_id,
                                           target_ids=request.individual_ids or [])
                
                return result
                
        except Exception as e:
            raise TrackingError(f"Tracking failed: {str(e)}") from e
    
    def _filter_bbs_by_ids(self, bbs: List[Dict], individual_ids: Optional[List[int]]) -> List[Dict]:
        """個体IDによるBBフィルタリング"""
        if individual_ids is None:
            return bbs
        
        return [bb for bb in bbs if bb.get("individual_id") in individual_ids]
    
    def _perform_matching(self, source_bbs: List[Dict], target_bbs: List[Dict], 
                         iou_matrix: np.ndarray, threshold: float) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """マッチング実行"""
        matches = []
        used_target_indices = set()
        
        # 貪欲マッチング（IOU値でソート）
        for i, source_bb in enumerate(source_bbs):
            best_iou = 0
            best_j = -1
            
            for j, target_bb in enumerate(target_bbs):
                if j in used_target_indices:
                    continue
                
                iou = iou_matrix[i, j] if i < len(iou_matrix) and j < len(iou_matrix[0]) else 0
                
                if iou >= threshold and iou > best_iou:
                    best_iou = iou
                    best_j = j
            
            if best_j >= 0:
                matches.append({
                    "source_id": source_bb.get("individual_id", i),
                    "target_id": target_bbs[best_j].get("individual_id", best_j),
                    "source_bb": source_bb,
                    "target_bb": target_bbs[best_j],
                    "iou": best_iou,
                    "confidence": min(0.95, best_iou + 0.1)  # IOU基盤の信頼度
                })
                used_target_indices.add(best_j)
        
        # 未マッチBB特定
        matched_source_indices = {match["source_id"] for match in matches}
        matched_target_indices = used_target_indices
        
        unmatched_source = [bb for i, bb in enumerate(source_bbs) 
                          if bb.get("individual_id", i) not in matched_source_indices]
        unmatched_target = [bb for i, bb in enumerate(target_bbs) 
                          if i not in matched_target_indices]
        
        return matches, unmatched_source, unmatched_target
    
    def _update_tracking_history(self, source_frame: str, target_frame: str, result: TrackingResult):
        """追跡履歴更新"""
        if source_frame not in self._tracking_history:
            self._tracking_history[source_frame] = {}
        
        self._tracking_history[source_frame][target_frame] = {
            "matches": result.matches,
            "processing_time": result.processing_time,
            "timestamp": time.time()
        }
        
        # 古い履歴削除（メモリ節約）
        if len(self._tracking_history) > 100:
            oldest_frame = min(self._tracking_history.keys())
            del self._tracking_history[oldest_frame]
    
    @_measure_time("id_inheritance")
    def calculate_id_inheritance(self, source_bbs: List[Dict], target_bbs: List[Dict], 
                                threshold: float) -> List[Dict]:
        """
        ID継承判定（3ms以下必達）
        
        Args:
            source_bbs: 元フレームBBリスト
            target_bbs: 先フレームBBリスト
            threshold: IOU閾値
            
        Returns:
            List[Dict]: ID継承結果
        """
        try:
            if not source_bbs or not target_bbs:
                return []
            
            # 高速IOU計算
            iou_matrix = PerformanceOptimizer.vectorized_iou_calculation(source_bbs, target_bbs)
            
            inheritance_results = []
            
            for i, source_bb in enumerate(source_bbs):
                for j, target_bb in enumerate(target_bbs):
                    if i < len(iou_matrix) and j < len(iou_matrix[0]):
                        iou = iou_matrix[i, j]
                        
                        if iou >= threshold:
                            inheritance_results.append({
                                "source_individual_id": source_bb.get("individual_id"),
                                "target_individual_id": target_bb.get("individual_id"),
                                "iou": iou,
                                "should_inherit": iou >= threshold,
                                "confidence": min(0.95, iou + 0.1)
                            })
            
            return inheritance_results
            
        except Exception as e:
            raise IDInheritanceError(f"ID inheritance calculation failed: {str(e)}") from e
    
    @_measure_time("break_detection")
    def detect_tracking_break(self, frame_id: str, current_bbs: List[Dict]) -> List[TrackingBreak]:
        """
        追跡断絶検知（2ms以下必達）
        
        Args:
            frame_id: 現在フレームID
            current_bbs: 現在フレームBBリスト
            
        Returns:
            List[TrackingBreak]: 断絶検知結果
        """
        try:
            breaks = []
            
            # 履歴から前フレーム情報取得
            previous_frame_data = self._get_previous_frame_data(frame_id)
            if not previous_frame_data:
                return breaks
            
            previous_bbs = previous_frame_data.get("bbs", [])
            current_individual_ids = {bb.get("individual_id") for bb in current_bbs}
            
            # 消失個体検知
            for prev_bb in previous_bbs:
                individual_id = prev_bb.get("individual_id")
                if individual_id is not None and individual_id not in current_individual_ids:
                    breaks.append(TrackingBreak(
                        individual_id=individual_id,
                        last_seen_frame=previous_frame_data.get("frame_id", "unknown"),
                        break_frame=frame_id,
                        last_bb=prev_bb,
                        break_type="disappeared"
                    ))
            
            # 低信頼度BBの断絶チェック
            for current_bb in current_bbs:
                confidence = current_bb.get("confidence", 1.0)
                if confidence < 0.5:  # 低信頼度閾値
                    breaks.append(TrackingBreak(
                        individual_id=current_bb.get("individual_id"),
                        last_seen_frame=previous_frame_data.get("frame_id", "unknown"),
                        break_frame=frame_id,
                        last_bb=current_bb,
                        break_type="low_confidence"
                    ))
            
            return breaks
            
        except Exception as e:
            print(f"Warning: Break detection error: {e}")
            return []
    
    def _get_previous_frame_data(self, current_frame_id: str) -> Optional[Dict]:
        """前フレームデータ取得"""
        try:
            # フレームIDから前フレームID推定
            if current_frame_id.isdigit():
                previous_frame_num = int(current_frame_id) - 1
                if previous_frame_num >= 0:
                    previous_frame_id = f"{previous_frame_num:06d}"
                    return self._tracking_history.get(previous_frame_id, {}).get("data")
        except:
            pass
        
        return None
    
    def apply_tracking_results(self, tracking_result: TrackingResult) -> int:
        """
        追跡結果適用（後続フレーム一括更新）
        
        Args:
            tracking_result: 追跡結果
            
        Returns:
            int: 更新フレーム数
        """
        try:
            updated_frames = 0
            
            # マッチしたBBのID継承を後続フレームに適用
            for match in tracking_result.matches:
                # Domain層にID更新要求
                success = self.domain_service.update_bb_entity(
                    match["target_bb"]["id"],
                    {"individual_id": match["source_id"]}
                )
                
                if success:
                    updated_frames += 1
            
            # 追跡完了イベント発行
            self._publish_tracking_event("tracking_completed",
                                       source_frame_id=tracking_result.source_frame_id,
                                       target_frame_id=tracking_result.target_frame_id,
                                       matches=tracking_result.matches,
                                       processing_time=tracking_result.processing_time)
            
            return updated_frames
            
        except Exception as e:
            raise TrackingError(f"Failed to apply tracking results: {str(e)}") from e
    
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """性能統計情報取得"""
        with self._lock:
            stats = {}
            
            for operation, data in self._stats.items():
                times = data["times"]
                if times:
                    stats[operation] = {
                        "count": data["count"],
                        "avg": sum(times) / len(times),
                        "max": max(times),
                        "min": min(times),
                        "latest": times[-1] if times else 0
                    }
                else:
                    stats[operation] = {"count": 0, "avg": 0, "max": 0, "min": 0, "latest": 0}
            
            return stats
    
    def clear_cache(self):
        """キャッシュクリア"""
        with self._lock:
            self._tracking_history.clear()
            self._iou_cache.clear()
            PerformanceOptimizer.calculate_iou_cached.cache_clear()
    
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        stats = self.get_performance_stats()
        
        health_status = {
            "status": "healthy",
            "cache_size": len(self._tracking_history),
            "performance": {},
            "warnings": []
        }
        
        # 性能チェック
        targets = {"start_tracking": 5, "id_inheritance": 3, "break_detection": 2}
        
        for operation, stat in stats.items():
            target = targets.get(operation, 5)
            avg_time = stat.get("avg", 0)
            max_time = stat.get("max", 0)
            
            health_status["performance"][operation] = {
                "avg_time": avg_time,
                "max_time": max_time,
                "target": target,
                "meets_target": avg_time <= target
            }
            
            if avg_time > target:
                health_status["warnings"].append(
                    f"{operation} average time {avg_time:.2f}ms exceeds target {target}ms"
                )
        
        if health_status["warnings"]:
            health_status["status"] = "degraded"
        
        return health_status