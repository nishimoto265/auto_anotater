"""
フレームエンティティ - Agent3専用
フレーム単位でのBB管理・検索・操作
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict

from .bb_entity import BBEntity
from .id_entity import IndividualID
from .action_entity import ActionType
from ..exceptions import ValidationError, BusinessRuleViolationError, EntityNotFoundError, PerformanceError


@dataclass
class FrameEntity:
    """
    フレームエンティティ
    
    ドメインルール:
    - フレームID: 6桁ゼロパディング（000000-999999）
    - 解像度: 4K基準（3840x2160）
    - BB数: 個体数上限16個体対応
    - BB重複: 同一個体の高重複BB禁止
    """
    
    id: str                                    # フレームID（000000形式）
    image_path: str                           # 画像ファイルパス
    annotation_path: str                      # アノテーションファイルパス
    width: int                                # 画像幅
    height: int                               # 画像高さ
    bounding_boxes: List[BBEntity] = field(default_factory=list)  # BB一覧
    created_at: datetime = field(default_factory=datetime.now)    # 作成日時
    
    def __post_init__(self):
        """フレーム検証"""
        self._validate_frame_id()
        self._validate_image_dimensions()
        self._validate_file_paths()
    
    def _validate_frame_id(self):
        """フレームID検証（6桁ゼロパディング）"""
        if not self.id or len(self.id) != 6 or not self.id.isdigit():
            raise ValidationError("frame_id", self.id, "6-digit zero-padded string (000000-999999)")
    
    def _validate_image_dimensions(self):
        """画像寸法検証"""
        if self.width <= 0 or self.height <= 0:
            raise ValidationError("image_dimensions", f"{self.width}x{self.height}", "positive integers")
        
        # 4K基準でのサイズ確認（警告レベル）
        if self.width < 1920 or self.height < 1080:
            # 1080p未満は警告のみ（エラーではない）
            pass
    
    def _validate_file_paths(self):
        """ファイルパス検証"""
        if not self.image_path:
            raise ValidationError("image_path", self.image_path, "non-empty string")
        
        if not self.annotation_path:
            raise ValidationError("annotation_path", self.annotation_path, "non-empty string")
    
    def add_bounding_box(self, bb: BBEntity) -> None:
        """
        BB追加（重複チェック付き）
        
        Args:
            bb: 追加するBBエンティティ
            
        Raises:
            BusinessRuleViolationError: BB重複・16個体上限違反時
        """
        start_time = time.perf_counter()
        
        # フレームID一致確認
        if bb.frame_id != self.id:
            raise ValidationError("frame_id_mismatch", bb.frame_id, self.id)
        
        # 重複チェック
        if self._has_duplicate_bb(bb):
            raise BusinessRuleViolationError(
                "duplicate_bb",
                f"Duplicate BB detected for individual {bb.individual_id.value} "
                f"with high overlap (>80% IOU)"
            )
        
        # 16個体上限チェック
        used_individuals = set(existing_bb.individual_id.value for existing_bb in self.bounding_boxes)
        if bb.individual_id.value not in used_individuals and len(used_individuals) >= 16:
            raise BusinessRuleViolationError(
                "max_individuals_exceeded",
                f"Cannot add BB for individual {bb.individual_id.value}: "
                f"16 individuals limit exceeded"
            )
        
        self.bounding_boxes.append(bb)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1.0:
            raise PerformanceError("add_bounding_box", elapsed, 1.0)
    
    def remove_bounding_box(self, bb_id: str) -> bool:
        """
        BB削除
        
        Args:
            bb_id: 削除するBB ID
            
        Returns:
            bool: 削除成功フラグ
        """
        original_count = len(self.bounding_boxes)
        self.bounding_boxes = [bb for bb in self.bounding_boxes if bb.id != bb_id]
        return len(self.bounding_boxes) < original_count
    
    def get_bounding_box_by_id(self, bb_id: str) -> Optional[BBEntity]:
        """BB ID指定取得"""
        for bb in self.bounding_boxes:
            if bb.id == bb_id:
                return bb
        return None
    
    def get_bounding_boxes_by_individual(self, individual_id: IndividualID) -> List[BBEntity]:
        """個体ID別BB取得"""
        return [bb for bb in self.bounding_boxes if bb.individual_id == individual_id]
    
    def get_bounding_boxes_by_action(self, action_type: ActionType) -> List[BBEntity]:
        """行動タイプ別BB取得"""
        return [bb for bb in self.bounding_boxes if bb.action_type == action_type]
    
    def get_high_confidence_bbs(self, threshold: float = 0.8) -> List[BBEntity]:
        """高信頼度BB取得"""
        return [bb for bb in self.bounding_boxes if bb.confidence.value >= threshold]
    
    def get_low_confidence_bbs(self, threshold: float = 0.3) -> List[BBEntity]:
        """低信頼度BB取得"""
        return [bb for bb in self.bounding_boxes if bb.confidence.value <= threshold]
    
    def update_bounding_box(self, bb_id: str, updated_bb: BBEntity) -> bool:
        """
        BB更新
        
        Args:
            bb_id: 更新対象BB ID
            updated_bb: 更新後BBエンティティ
            
        Returns:
            bool: 更新成功フラグ
        """
        for i, bb in enumerate(self.bounding_boxes):
            if bb.id == bb_id:
                # フレームID一致確認
                if updated_bb.frame_id != self.id:
                    raise ValidationError("frame_id_mismatch", updated_bb.frame_id, self.id)
                
                self.bounding_boxes[i] = updated_bb
                return True
        return False
    
    def get_used_individual_ids(self) -> List[IndividualID]:
        """使用中個体ID一覧取得"""
        used_ids = set(bb.individual_id for bb in self.bounding_boxes)
        return sorted(list(used_ids), key=lambda x: x.value)
    
    def get_available_individual_ids(self) -> List[IndividualID]:
        """利用可能個体ID一覧取得"""
        used_ids = set(bb.individual_id.value for bb in self.bounding_boxes)
        available_ids = [IndividualID(i) for i in range(16) if i not in used_ids]
        return available_ids
    
    def has_individual(self, individual_id: IndividualID) -> bool:
        """個体存在確認"""
        return any(bb.individual_id == individual_id for bb in self.bounding_boxes)
    
    def get_bb_count(self) -> int:
        """BB総数取得"""
        return len(self.bounding_boxes)
    
    def get_individual_count(self) -> int:
        """個体数取得"""
        return len(set(bb.individual_id.value for bb in self.bounding_boxes))
    
    def is_empty(self) -> bool:
        """空フレーム判定"""
        return len(self.bounding_boxes) == 0
    
    def get_action_statistics(self) -> Dict[ActionType, int]:
        """行動統計取得"""
        stats = {action: 0 for action in ActionType}
        for bb in self.bounding_boxes:
            stats[bb.action_type] += 1
        return stats
    
    def find_overlapping_bbs(self, target_bb: BBEntity, threshold: float = 0.1) -> List[BBEntity]:
        """重複BB検索"""
        return [bb for bb in self.bounding_boxes 
                if bb.id != target_bb.id and bb.overlaps_with(target_bb, threshold)]
    
    def _has_duplicate_bb(self, new_bb: BBEntity) -> bool:
        """
        BB重複チェック（同一個体・高重複度）
        
        Args:
            new_bb: 確認対象BB
            
        Returns:
            bool: 重複判定結果
        """
        for existing_bb in self.bounding_boxes:
            if (existing_bb.individual_id == new_bb.individual_id and
                existing_bb.calculate_iou_with(new_bb) > 0.8):
                return True
        return False
    
    def clear_all_bounding_boxes(self) -> int:
        """全BB削除"""
        count = len(self.bounding_boxes)
        self.bounding_boxes.clear()
        return count
    
    def to_yolo_format(self) -> str:
        """
        YOLO形式アノテーション文字列生成
        
        Returns:
            str: YOLO形式文字列（改行区切り）
        """
        return '\n'.join(bb.to_yolo_format() for bb in self.bounding_boxes)
    
    @classmethod
    def from_yolo_format(cls, frame_id: str, yolo_content: str, 
                        image_path: str, annotation_path: str,
                        width: int, height: int) -> 'FrameEntity':
        """
        YOLO形式からフレームエンティティ生成
        
        Args:
            frame_id: フレームID
            yolo_content: YOLO形式アノテーション内容
            image_path: 画像ファイルパス
            annotation_path: アノテーションファイルパス
            width: 画像幅
            height: 画像高さ
            
        Returns:
            FrameEntity: 生成されたフレームエンティティ
        """
        frame = cls(
            id=frame_id,
            image_path=image_path,
            annotation_path=annotation_path,
            width=width,
            height=height
        )
        
        if yolo_content.strip():
            for line in yolo_content.strip().split('\n'):
                if line.strip():
                    bb = BBEntity.from_yolo_format(line, frame_id)
                    frame.add_bounding_box(bb)
        
        return frame