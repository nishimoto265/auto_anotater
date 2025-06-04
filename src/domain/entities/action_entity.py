"""
行動エンティティ - Agent3専用
動物行動カテゴリ管理・検証
"""

from enum import IntEnum
from dataclasses import dataclass
from ..exceptions import ValidationError


class ActionType(IntEnum):
    """
    行動タイプ列挙型
    
    YOLO形式での行動ID対応:
    - 0: sit (座る)
    - 1: stand (立つ)  
    - 2: milk (授乳)
    - 3: water (飲水)
    - 4: food (摂食)
    """
    
    SIT = 0     # 座る
    STAND = 1   # 立つ
    MILK = 2    # 授乳
    WATER = 3   # 飲水
    FOOD = 4    # 摂食
    
    @classmethod
    def from_id(cls, action_id: int) -> 'ActionType':
        """行動IDから列挙型生成"""
        if not 0 <= action_id <= 4:
            raise ValidationError("action_id", action_id, "0-4")
        return cls(action_id)
    
    @classmethod
    def get_all_actions(cls) -> list['ActionType']:
        """全行動タイプ取得"""
        return list(cls)
    
    def get_display_name(self) -> str:
        """表示用名称取得"""
        display_names = {
            ActionType.SIT: "座る",
            ActionType.STAND: "立つ", 
            ActionType.MILK: "授乳",
            ActionType.WATER: "飲水",
            ActionType.FOOD: "摂食"
        }
        return display_names[self]
    
    def get_english_name(self) -> str:
        """英語名称取得"""
        return self.name.lower()


@dataclass
class ActionEntity:
    """
    行動エンティティ
    
    行動タイプの詳細情報管理
    """
    
    action_type: ActionType
    description: str = ""
    
    def __post_init__(self):
        """行動検証"""
        if not isinstance(self.action_type, ActionType):
            raise ValidationError("action_type", self.action_type, "ActionType enum")
    
    def get_id(self) -> int:
        """行動ID取得"""
        return int(self.action_type)
    
    def get_name(self) -> str:
        """行動名取得"""
        return self.action_type.get_display_name()
    
    def is_active_behavior(self) -> bool:
        """活動的行動判定"""
        return self.action_type in [ActionType.STAND, ActionType.MILK, ActionType.WATER, ActionType.FOOD]
    
    def is_passive_behavior(self) -> bool:
        """受動的行動判定"""
        return self.action_type == ActionType.SIT