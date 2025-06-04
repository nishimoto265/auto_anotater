"""
BBエンティティ - Agent3専用
バウンディングボックス・ドメインオブジェクト・検証・操作

パフォーマンス要件:
- エンティティ操作: 1ms以下
- 検証処理: 1ms以下
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..value_objects.coordinates import Coordinates
from ..value_objects.confidence import Confidence
from ..value_objects.color_mapping import ColorMapping
from .id_entity import IndividualID
from .action_entity import ActionType
from ..exceptions import ValidationError, PerformanceError, BusinessRuleViolationError


@dataclass
class BBEntity:
    """
    バウンディングボックスエンティティ
    
    ドメインルール:
    - 座標: YOLO正規化座標（0.0-1.0）
    - 個体ID: 0-15の範囲
    - 行動ID: 0-4の範囲（sit/stand/milk/water/food）
    - 信頼度: 0.0-1.0の範囲
    - 一意性: BB IDによる識別
    """
    
    # 必須フィールド
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    frame_id: str = ""
    individual_id: IndividualID = field(default_factory=lambda: IndividualID(0))
    action_type: ActionType = ActionType.SIT
    coordinates: Coordinates = field(default_factory=lambda: Coordinates(0.5, 0.5, 0.1, 0.1))
    confidence: Confidence = field(default_factory=lambda: Confidence(0.8))
    
    # 管理フィールド
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """
        エンティティ検証 (パフォーマンス要件: 1ms以下)
        
        Raises:
            ValidationError: 検証失敗時
            PerformanceError: 1ms超過時
        """
        start_time = time.perf_counter()
        
        self._validate_required_fields()
        self._validate_business_rules()
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1.0:
            raise PerformanceError("bb_entity_validation", elapsed, 1.0)
    
    def _validate_required_fields(self):
        """必須フィールド検証"""
        if not self.id:
            raise ValidationError("bb_id", self.id, "non-empty string")
        
        if not self.frame_id:
            raise ValidationError("frame_id", self.frame_id, "non-empty string")
        
        if not isinstance(self.individual_id, IndividualID):
            raise ValidationError("individual_id", self.individual_id, "IndividualID instance")
        
        if not isinstance(self.action_type, ActionType):
            raise ValidationError("action_type", self.action_type, "ActionType enum")
        
        if not isinstance(self.coordinates, Coordinates):
            raise ValidationError("coordinates", self.coordinates, "Coordinates instance")
        
        if not isinstance(self.confidence, Confidence):
            raise ValidationError("confidence", self.confidence, "Confidence instance")
    
    def _validate_business_rules(self):
        """ビジネスルール検証"""
        # BB最小サイズチェック (0.01以上)
        if self.coordinates.get_area() < 0.0001:  # 1% x 1%
            raise BusinessRuleViolationError(
                "minimum_bb_size",
                f"BB area too small: {self.coordinates.get_area()} (minimum: 0.0001)"
            )
    
    def get_area(self) -> float:
        """BB面積取得（YOLO座標）"""
        return self.coordinates.get_area()
    
    def get_center(self) -> tuple[float, float]:
        """BB中心座標取得"""
        return self.coordinates.get_center()
    
    def get_color(self) -> ColorMapping:
        """個体色取得"""
        return ColorMapping(self.individual_id.value)
    
    def overlaps_with(self, other: 'BBEntity', threshold: float = 0.1) -> bool:
        """
        他BBとの重複判定
        
        Args:
            other: 比較対象BB
            threshold: 重複判定閾値
            
        Returns:
            bool: 重複判定結果
        """
        return self.coordinates.overlaps_with(other.coordinates, threshold)
    
    def calculate_iou_with(self, other: 'BBEntity') -> float:
        """
        他BBとのIOU計算
        
        Args:
            other: 比較対象BB
            
        Returns:
            float: IOU値（0.0-1.0）
        """
        return self.coordinates.iou_with(other.coordinates)
    
    def is_same_individual(self, other: 'BBEntity') -> bool:
        """同一個体判定"""
        return self.individual_id == other.individual_id
    
    def is_high_confidence(self) -> bool:
        """高信頼度判定"""
        return self.confidence.is_high_confidence()
    
    def is_low_confidence(self) -> bool:
        """低信頼度判定"""
        return self.confidence.is_low_confidence()
    
    def update_coordinates(self, new_coordinates: Coordinates) -> 'BBEntity':
        """
        座標更新 (新インスタンス生成)
        
        Args:
            new_coordinates: 新座標
            
        Returns:
            BBEntity: 更新されたBBエンティティ
        """
        return BBEntity(
            id=self.id,
            frame_id=self.frame_id,
            individual_id=self.individual_id,
            action_type=self.action_type,
            coordinates=new_coordinates,
            confidence=self.confidence,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def update_individual_id(self, new_individual_id: IndividualID) -> 'BBEntity':
        """個体ID更新 (新インスタンス生成)"""
        return BBEntity(
            id=self.id,
            frame_id=self.frame_id,
            individual_id=new_individual_id,
            action_type=self.action_type,
            coordinates=self.coordinates,
            confidence=self.confidence,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def update_action_type(self, new_action_type: ActionType) -> 'BBEntity':
        """行動タイプ更新 (新インスタンス生成)"""
        return BBEntity(
            id=self.id,
            frame_id=self.frame_id,
            individual_id=self.individual_id,
            action_type=new_action_type,
            coordinates=self.coordinates,
            confidence=self.confidence,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def update_confidence(self, new_confidence: Confidence) -> 'BBEntity':
        """信頼度更新 (新インスタンス生成)"""
        return BBEntity(
            id=self.id,
            frame_id=self.frame_id,
            individual_id=self.individual_id,
            action_type=self.action_type,
            coordinates=self.coordinates,
            confidence=new_confidence,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def to_yolo_format(self) -> str:
        """
        YOLO形式文字列生成
        
        Format: "個体ID YOLO_X YOLO_Y YOLO_W YOLO_H 行動ID 信頼度"
        
        Returns:
            str: YOLO形式文字列
        """
        return (f"{self.individual_id.value} "
                f"{self.coordinates.x:.4f} {self.coordinates.y:.4f} "
                f"{self.coordinates.w:.4f} {self.coordinates.h:.4f} "
                f"{int(self.action_type)} {self.confidence.value:.4f}")
    
    @classmethod
    def from_yolo_format(cls, yolo_line: str, frame_id: str, bb_id: str = None) -> 'BBEntity':
        """
        YOLO形式文字列からBBエンティティ生成
        
        Args:
            yolo_line: YOLO形式文字列
            frame_id: フレームID
            bb_id: BB ID (Noneの場合は自動生成)
            
        Returns:
            BBEntity: 生成されたBBエンティティ
            
        Raises:
            ValidationError: YOLO形式解析失敗時
        """
        try:
            parts = yolo_line.strip().split()
            if len(parts) != 7:
                raise ValidationError("yolo_format", yolo_line, "7 space-separated values")
            
            individual_id = IndividualID(int(parts[0]))
            coordinates = Coordinates(float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]))
            action_type = ActionType.from_id(int(parts[5]))
            confidence = Confidence(float(parts[6]))
            
            return cls(
                id=bb_id or str(uuid.uuid4()),
                frame_id=frame_id,
                individual_id=individual_id,
                action_type=action_type,
                coordinates=coordinates,
                confidence=confidence
            )
            
        except (ValueError, IndexError) as e:
            raise ValidationError("yolo_format_parsing", yolo_line, f"valid YOLO format: {str(e)}")
    
    def clone(self, **kwargs) -> 'BBEntity':
        """
        BBエンティティ複製 (指定フィールドのみ更新)
        
        Args:
            **kwargs: 更新するフィールド
            
        Returns:
            BBEntity: 複製されたBBエンティティ
        """
        return BBEntity(
            id=kwargs.get('id', self.id),
            frame_id=kwargs.get('frame_id', self.frame_id),
            individual_id=kwargs.get('individual_id', self.individual_id),
            action_type=kwargs.get('action_type', self.action_type),
            coordinates=kwargs.get('coordinates', self.coordinates),
            confidence=kwargs.get('confidence', self.confidence),
            created_at=kwargs.get('created_at', self.created_at),
            updated_at=kwargs.get('updated_at', datetime.now())
        )