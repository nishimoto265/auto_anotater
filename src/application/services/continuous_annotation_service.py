"""
連続アノテーションサービス
連続BB生成と追跡機能を提供
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from ...domain.entities.bb_entity import BBEntity
from ...domain.value_objects.bb_request import BBCreationRequest
from ..exceptions import ServiceError
from .annotation_service import AnnotationService
from .tracking_service import TrackingService


@dataclass
class ContinuousBBTemplate:
    """連続BB生成用テンプレート"""
    x: float
    y: float
    w: float
    h: float
    individual_id: int
    action_id: int
    confidence: float = 0.95
    frame_range: Optional[Tuple[int, int]] = None  # (start, end)


class ContinuousAnnotationService:
    """
    連続アノテーションサービス
    
    機能:
    - 連続BB生成モード
    - 最後に作成したBBの位置記憶
    - 範囲指定BBコピー
    - 前方追跡
    """
    
    def __init__(self, 
                 annotation_service: AnnotationService,
                 tracking_service: TrackingService):
        self.annotation_service = annotation_service
        self.tracking_service = tracking_service
        
        # 連続モード状態
        self.continuous_mode = False
        self.last_bb_template: Optional[ContinuousBBTemplate] = None
        
        # 追跡中のBB
        self.tracking_bbs: Dict[str, BBEntity] = {}
        
    def set_continuous_mode(self, enabled: bool):
        """連続モード設定"""
        self.continuous_mode = enabled
        if not enabled:
            self.last_bb_template = None
            
    def is_continuous_mode(self) -> bool:
        """連続モード状態取得"""
        return self.continuous_mode
        
    def record_bb_creation(self, bb: BBEntity):
        """BB作成を記録（連続生成用）"""
        if self.continuous_mode:
            self.last_bb_template = ContinuousBBTemplate(
                x=bb.x,
                y=bb.y,
                w=bb.w,
                h=bb.h,
                individual_id=bb.individual_id,
                action_id=bb.action_id,
                confidence=bb.confidence
            )
            
    def create_continuous_bb(self, frame_id: str) -> Optional[BBEntity]:
        """
        連続BBを作成
        
        Args:
            frame_id: 対象フレームID
            
        Returns:
            作成されたBBエンティティ（作成しない場合はNone）
        """
        if not self.continuous_mode or not self.last_bb_template:
            return None
            
        try:
            # テンプレートからBB作成要求を生成
            request = BBCreationRequest(
                x=self.last_bb_template.x,
                y=self.last_bb_template.y,
                w=self.last_bb_template.w,
                h=self.last_bb_template.h,
                individual_id=self.last_bb_template.individual_id,
                action_id=self.last_bb_template.action_id,
                confidence=self.last_bb_template.confidence,
                frame_id=frame_id
            )
            
            # BB作成
            bb = self.annotation_service.create_bounding_box(request)
            return bb
            
        except Exception as e:
            print(f"Failed to create continuous BB: {e}")
            return None
            
    def copy_bb_to_range(self, bb: BBEntity, start_frame: int, end_frame: int) -> List[BBEntity]:
        """
        BBを指定範囲にコピー
        
        Args:
            bb: コピー元BB
            start_frame: 開始フレーム番号
            end_frame: 終了フレーム番号（含む）
            
        Returns:
            作成されたBBのリスト
        """
        if start_frame > end_frame:
            raise ServiceError("Invalid frame range")
            
        created_bbs = []
        
        for frame_num in range(start_frame, end_frame + 1):
            frame_id = f"{frame_num:06d}"
            
            try:
                request = BBCreationRequest(
                    x=bb.x,
                    y=bb.y,
                    w=bb.w,
                    h=bb.h,
                    individual_id=bb.individual_id,
                    action_id=bb.action_id,
                    confidence=bb.confidence,
                    frame_id=frame_id
                )
                
                new_bb = self.annotation_service.create_bounding_box(request)
                created_bbs.append(new_bb)
                
            except Exception as e:
                print(f"Failed to copy BB to frame {frame_id}: {e}")
                
        return created_bbs
        
    def track_bb_forward(self, bb: BBEntity, num_frames: int = 30) -> List[BBEntity]:
        """
        BBを前方追跡
        
        Args:
            bb: 追跡開始BB
            num_frames: 追跡フレーム数
            
        Returns:
            追跡されたBBのリスト
        """
        tracked_bbs = []
        current_bb = bb
        
        # 開始フレーム番号を取得
        try:
            start_frame = int(bb.frame_id)
        except ValueError:
            print(f"Invalid frame ID format: {bb.frame_id}")
            return tracked_bbs
            
        for i in range(1, num_frames + 1):
            next_frame_id = f"{start_frame + i:06d}"
            
            # 次フレームで追跡
            tracking_result = self.tracking_service.track_bb_to_next_frame(
                current_bb, next_frame_id
            )
            
            if tracking_result:
                # 追跡成功 - 新しいBBを作成
                try:
                    request = BBCreationRequest(
                        x=tracking_result['x'],
                        y=tracking_result['y'],
                        w=tracking_result['w'],
                        h=tracking_result['h'],
                        individual_id=current_bb.individual_id,
                        action_id=current_bb.action_id,
                        confidence=tracking_result.get('confidence', 0.8),
                        frame_id=next_frame_id
                    )
                    
                    new_bb = self.annotation_service.create_bounding_box(request)
                    tracked_bbs.append(new_bb)
                    current_bb = new_bb
                    
                except Exception as e:
                    print(f"Failed to create tracked BB: {e}")
                    break
            else:
                # 追跡失敗
                print(f"Tracking lost at frame {next_frame_id}")
                break
                
        return tracked_bbs
        
    def clear_templates(self):
        """テンプレートをクリア"""
        self.last_bb_template = None
        self.tracking_bbs.clear()
        
    def get_status(self) -> Dict[str, Any]:
        """サービス状態取得"""
        return {
            "continuous_mode": self.continuous_mode,
            "has_template": self.last_bb_template is not None,
            "template": self.last_bb_template.__dict__ if self.last_bb_template else None,
            "tracking_count": len(self.tracking_bbs)
        }