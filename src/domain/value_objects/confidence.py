"""
信頼度値オブジェクト - Agent3専用
アノテーション信頼度管理・検証
"""

from dataclasses import dataclass
from ..exceptions import ValidationError


@dataclass(frozen=True)
class Confidence:
    """
    信頼度値オブジェクト
    
    範囲: 0.0-1.0
    用途: BBアノテーション品質評価・自動アノテーション信頼度
    """
    
    value: float
    
    def __post_init__(self):
        """信頼度検証"""
        if not 0.0 <= self.value <= 1.0:
            raise ValidationError("confidence", self.value, "0.0-1.0")
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """高信頼度判定"""
        return self.value >= threshold
    
    def is_low_confidence(self, threshold: float = 0.3) -> bool:
        """低信頼度判定"""
        return self.value <= threshold
    
    def get_percentage(self) -> int:
        """パーセント表示用"""
        return int(self.value * 100)
    
    @classmethod
    def from_percentage(cls, percentage: int) -> 'Confidence':
        """パーセントから信頼度生成"""
        if not 0 <= percentage <= 100:
            raise ValidationError("percentage", percentage, "0-100")
        return cls(percentage / 100.0)
    
    @classmethod
    def high(cls) -> 'Confidence':
        """高信頼度(0.9)"""
        return cls(0.9)
    
    @classmethod
    def medium(cls) -> 'Confidence':
        """中信頼度(0.6)"""
        return cls(0.6)
    
    @classmethod
    def low(cls) -> 'Confidence':
        """低信頼度(0.3)"""
        return cls(0.3)