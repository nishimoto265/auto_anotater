"""
追跡アルゴリズム - Agent3専用
シンプルIOU追跡・フレーム間ID継承・追跡断絶検知

パフォーマンス要件:
- 追跡処理: 5ms以下
- 精度: 一般的使用で90%以上
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum

from ..entities.bb_entity import BBEntity
from ..entities.frame_entity import FrameEntity
from ..entities.id_entity import IndividualID
from .iou_calculator import IOUCalculator
from ..exceptions import PerformanceError, ValidationError


class TrackingStatus(Enum):
    """追跡ステータス"""
    MATCHED = "matched"           # マッチング成功
    NEW_OBJECT = "new_object"     # 新規オブジェクト
    LOST_OBJECT = "lost_object"   # 追跡断絶


@dataclass
class TrackingMatch:
    """
    追跡マッチング結果
    """
    source_bb_id: str              # 追跡元BB ID
    target_bb_id: str              # 追跡先BB ID
    iou_score: float              # IOU値
    individual_id: int            # 個体ID
    status: TrackingStatus        # 追跡ステータス
    confidence: float             # マッチング信頼度


@dataclass
class TrackingResult:
    """
    追跡処理結果
    """
    source_frame_id: str                    # 追跡元フレームID
    target_frame_id: str                    # 追跡先フレームID
    matches: List[TrackingMatch]            # マッチング結果リスト
    new_objects: List[BBEntity]             # 新規オブジェクトリスト
    lost_objects: List[BBEntity]            # 追跡断絶オブジェクトリスト
    processing_time_ms: float              # 処理時間（ms）
    match_accuracy: float                   # マッチング精度


class SimpleIOUTracker:
    """
    シンプルIOU追跡アルゴリズム
    
    アルゴリズム:
    1. フレーム間IOU計算
    2. 閾値以上の最高IOUペアを対応付け
    3. 対応なしBBは新規ID割り当て
    4. 消失BBは追跡断絶記録
    
    特徴:
    - 軽量・高速（5ms以下）
    - 実装シンプル
    - 一般的な動物行動で90%以上の精度
    """
    
    def __init__(self, iou_threshold: float = 0.5, 
                 confidence_threshold: float = 0.3):
        """
        追跡アルゴリズム初期化
        
        Args:
            iou_threshold: IOU閾値（デフォルト: 0.5）
            confidence_threshold: 信頼度閾値（デフォルト: 0.3）
        """
        if not 0.0 <= iou_threshold <= 1.0:
            raise ValidationError("iou_threshold", iou_threshold, "0.0-1.0")
        
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValidationError("confidence_threshold", confidence_threshold, "0.0-1.0")
        
        self.iou_threshold = iou_threshold
        self.confidence_threshold = confidence_threshold
    
    def track_between_frames(self, source_frame: FrameEntity,
                           target_frame: FrameEntity) -> TrackingResult:
        """
        フレーム間追跡 (パフォーマンス要件: 5ms以下)
        
        Args:
            source_frame: 追跡元フレーム
            target_frame: 追跡先フレーム
            
        Returns:
            TrackingResult: 追跡結果
            
        Raises:
            PerformanceError: 5ms超過時
        """
        start_time = time.perf_counter()
        
        source_bbs = source_frame.bounding_boxes
        target_bbs = target_frame.bounding_boxes
        
        if not source_bbs:
            # 追跡元がない場合は全て新規オブジェクト
            result = TrackingResult(
                source_frame_id=source_frame.id,
                target_frame_id=target_frame.id,
                matches=[],
                new_objects=target_bbs.copy(),
                lost_objects=[],
                processing_time_ms=0.0,
                match_accuracy=1.0 if not target_bbs else 0.0
            )
        elif not target_bbs:
            # 追跡先がない場合は全て追跡断絶
            result = TrackingResult(
                source_frame_id=source_frame.id,
                target_frame_id=target_frame.id,
                matches=[],
                new_objects=[],
                lost_objects=source_bbs.copy(),
                processing_time_ms=0.0,
                match_accuracy=0.0
            )
        else:
            # 通常追跡処理
            result = self._perform_tracking(source_frame, target_frame, source_bbs, target_bbs)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        result.processing_time_ms = elapsed
        
        if elapsed > 5.0:
            raise PerformanceError("frame_tracking", elapsed, 5.0)
        
        return result
    
    def _perform_tracking(self, source_frame: FrameEntity, target_frame: FrameEntity,
                         source_bbs: List[BBEntity], target_bbs: List[BBEntity]) -> TrackingResult:
        """追跡処理実行"""
        # 信頼度フィルタリング
        filtered_source_bbs = [bb for bb in source_bbs 
                              if bb.confidence.value >= self.confidence_threshold]
        filtered_target_bbs = [bb for bb in target_bbs 
                              if bb.confidence.value >= self.confidence_threshold]
        
        # マッチング検索
        matches = self._find_optimal_matching(filtered_source_bbs, filtered_target_bbs)
        
        # 新規・消失オブジェクト検出
        matched_source_ids = set(match.source_bb_id for match in matches)
        matched_target_ids = set(match.target_bb_id for match in matches)
        
        new_objects = [bb for bb in filtered_target_bbs if bb.id not in matched_target_ids]
        lost_objects = [bb for bb in filtered_source_bbs if bb.id not in matched_source_ids]
        
        # 精度計算
        total_objects = max(len(filtered_source_bbs), len(filtered_target_bbs))
        match_accuracy = len(matches) / total_objects if total_objects > 0 else 1.0
        
        return TrackingResult(
            source_frame_id=source_frame.id,
            target_frame_id=target_frame.id,
            matches=matches,
            new_objects=new_objects,
            lost_objects=lost_objects,
            processing_time_ms=0.0,  # 後で設定
            match_accuracy=match_accuracy
        )
    
    def _find_optimal_matching(self, source_bbs: List[BBEntity],
                             target_bbs: List[BBEntity]) -> List[TrackingMatch]:
        """
        最適マッチング検索 (貪欲アルゴリズム)
        
        Args:
            source_bbs: 追跡元BBリスト
            target_bbs: 追跡先BBリスト
            
        Returns:
            List[TrackingMatch]: マッチング結果リスト
        """
        if not source_bbs or not target_bbs:
            return []
        
        # 個体ID別グループ化
        source_by_individual = self._group_by_individual_id(source_bbs)
        target_by_individual = self._group_by_individual_id(target_bbs)
        
        matches = []
        used_target_ids = set()
        
        # 個体ID別マッチング（同一個体優先）
        for individual_id in source_by_individual.keys():
            if individual_id in target_by_individual:
                # 同一個体内でのマッチング
                individual_matches = self._match_same_individual(
                    source_by_individual[individual_id],
                    target_by_individual[individual_id],
                    used_target_ids
                )
                matches.extend(individual_matches)
                used_target_ids.update(match.target_bb_id for match in individual_matches)
        
        # 残りのソースBBに対する異個体マッチング
        unmatched_source_bbs = [
            bb for bb in source_bbs 
            if bb.id not in set(match.source_bb_id for match in matches)
        ]
        unmatched_target_bbs = [
            bb for bb in target_bbs 
            if bb.id not in used_target_ids
        ]
        
        if unmatched_source_bbs and unmatched_target_bbs:
            cross_matches = self._match_cross_individual(
                unmatched_source_bbs, unmatched_target_bbs
            )
            matches.extend(cross_matches)
        
        return matches
    
    def _group_by_individual_id(self, bb_list: List[BBEntity]) -> Dict[int, List[BBEntity]]:
        """個体ID別グループ化"""
        groups = {}
        for bb in bb_list:
            individual_id = bb.individual_id.value
            if individual_id not in groups:
                groups[individual_id] = []
            groups[individual_id].append(bb)
        return groups
    
    def _match_same_individual(self, source_bbs: List[BBEntity],
                             target_bbs: List[BBEntity],
                             used_target_ids: set) -> List[TrackingMatch]:
        """同一個体内マッチング"""
        matches = []
        available_targets = [bb for bb in target_bbs if bb.id not in used_target_ids]
        
        if not available_targets:
            return matches
        
        # IOU行列計算
        iou_matrix = IOUCalculator.calculate_iou_matrix(source_bbs, available_targets)
        
        # 貪欲マッチング
        used_indices = set()
        for i, source_bb in enumerate(source_bbs):
            best_j = -1
            best_iou = self.iou_threshold
            
            for j, target_bb in enumerate(available_targets):
                if j in used_indices:
                    continue
                
                iou_score = iou_matrix[i, j]
                if iou_score > best_iou:
                    best_iou = iou_score
                    best_j = j
            
            if best_j >= 0:
                target_bb = available_targets[best_j]
                matches.append(TrackingMatch(
                    source_bb_id=source_bb.id,
                    target_bb_id=target_bb.id,
                    iou_score=best_iou,
                    individual_id=source_bb.individual_id.value,
                    status=TrackingStatus.MATCHED,
                    confidence=min(source_bb.confidence.value, target_bb.confidence.value)
                ))
                used_indices.add(best_j)
        
        return matches
    
    def _match_cross_individual(self, source_bbs: List[BBEntity],
                              target_bbs: List[BBEntity]) -> List[TrackingMatch]:
        """異個体マッチング（ID変更対応）"""
        matches = []
        
        if not source_bbs or not target_bbs:
            return matches
        
        # IOU行列計算
        iou_matrix = IOUCalculator.calculate_iou_matrix(source_bbs, target_bbs)
        
        # 貪欲マッチング（高IOU優先）
        used_target_indices = set()
        for i, source_bb in enumerate(source_bbs):
            best_j = -1
            best_iou = self.iou_threshold
            
            for j, target_bb in enumerate(target_bbs):
                if j in used_target_indices:
                    continue
                
                iou_score = iou_matrix[i, j]
                if iou_score > best_iou:
                    best_iou = iou_score
                    best_j = j
            
            if best_j >= 0:
                target_bb = target_bbs[best_j]
                matches.append(TrackingMatch(
                    source_bb_id=source_bb.id,
                    target_bb_id=target_bb.id,
                    iou_score=best_iou,
                    individual_id=source_bb.individual_id.value,  # ソース個体IDを維持
                    status=TrackingStatus.MATCHED,
                    confidence=min(source_bb.confidence.value, target_bb.confidence.value)
                ))
                used_target_indices.add(best_j)
        
        return matches
    
    def apply_tracking_result(self, target_frame: FrameEntity, 
                             tracking_result: TrackingResult) -> FrameEntity:
        """
        追跡結果をフレームに適用
        
        Args:
            target_frame: 適用対象フレーム
            tracking_result: 追跡結果
            
        Returns:
            FrameEntity: 更新されたフレーム
        """
        updated_bbs = []
        
        # マッチしたBBのID更新
        for match in tracking_result.matches:
            target_bb = target_frame.get_bounding_box_by_id(match.target_bb_id)
            if target_bb:
                # 個体ID継承
                updated_bb = target_bb.update_individual_id(IndividualID(match.individual_id))
                updated_bbs.append(updated_bb)
        
        # 新規オブジェクトはそのまま追加
        updated_bbs.extend(tracking_result.new_objects)
        
        # フレーム更新
        updated_frame = FrameEntity(
            id=target_frame.id,
            image_path=target_frame.image_path,
            annotation_path=target_frame.annotation_path,
            width=target_frame.width,
            height=target_frame.height,
            created_at=target_frame.created_at
        )
        
        for bb in updated_bbs:
            updated_frame.add_bounding_box(bb)
        
        return updated_frame
    
    def get_tracking_statistics(self, tracking_result: TrackingResult) -> Dict:
        """追跡統計取得"""
        total_matches = len(tracking_result.matches)
        total_new = len(tracking_result.new_objects)
        total_lost = len(tracking_result.lost_objects)
        total_objects = total_matches + total_new + total_lost
        
        avg_iou = (sum(match.iou_score for match in tracking_result.matches) / total_matches 
                  if total_matches > 0 else 0.0)
        
        avg_confidence = (sum(match.confidence for match in tracking_result.matches) / total_matches 
                         if total_matches > 0 else 0.0)
        
        return {
            "total_objects": total_objects,
            "matched_objects": total_matches,
            "new_objects": total_new,
            "lost_objects": total_lost,
            "match_ratio": total_matches / total_objects if total_objects > 0 else 0.0,
            "average_iou": avg_iou,
            "average_confidence": avg_confidence,
            "processing_time_ms": tracking_result.processing_time_ms,
            "match_accuracy": tracking_result.match_accuracy
        }