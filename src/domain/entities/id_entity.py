"""
個体IDエンティティ - Agent3専用
16個体上限管理・検証
"""

from dataclasses import dataclass
from ..exceptions import ValidationError, BusinessRuleViolationError


@dataclass(frozen=True)
class IndividualID:
    """
    個体ID値オブジェクト
    
    制約:
    - 範囲: 0-15 (16個体上限)
    - 一意性: プロジェクト内で個体IDは一意
    """
    
    value: int
    
    def __post_init__(self):
        """個体ID検証"""
        if not 0 <= self.value <= 15:
            raise ValidationError("individual_id", self.value, "0-15")
    
    def __str__(self) -> str:
        return f"ID{self.value:02d}"
    
    def __int__(self) -> int:
        return self.value
    
    @classmethod
    def from_int(cls, id_value: int) -> 'IndividualID':
        """整数から個体ID生成"""
        return cls(id_value)
    
    @classmethod
    def get_all_valid_ids(cls) -> list['IndividualID']:
        """全有効個体ID取得"""
        return [cls(i) for i in range(16)]
    
    @classmethod
    def get_max_individuals(cls) -> int:
        """最大個体数取得"""
        return 16
    
    def get_next_id(self) -> 'IndividualID':
        """次の個体ID取得"""
        if self.value >= 15:
            raise BusinessRuleViolationError(
                "individual_id_limit", 
                f"Cannot create ID after {self.value} (max 15)"
            )
        return IndividualID(self.value + 1)
    
    def get_previous_id(self) -> 'IndividualID':
        """前の個体ID取得"""
        if self.value <= 0:
            raise BusinessRuleViolationError(
                "individual_id_limit",
                f"Cannot create ID before {self.value} (min 0)"
            )
        return IndividualID(self.value - 1)


class IndividualManager:
    """
    個体管理クラス
    
    16個体上限の管理・使用中ID追跡
    """
    
    def __init__(self):
        self._used_ids: set[int] = set()
    
    def assign_id(self, preferred_id: int = None) -> IndividualID:
        """
        個体ID割り当て
        
        Args:
            preferred_id: 希望ID (Noneの場合は最小の空きIDを割り当て)
            
        Returns:
            IndividualID: 割り当てられた個体ID
            
        Raises:
            BusinessRuleViolationError: 16個体上限超過時
        """
        if len(self._used_ids) >= 16:
            raise BusinessRuleViolationError(
                "max_individuals_exceeded",
                f"Cannot assign more than 16 individuals (current: {len(self._used_ids)})"
            )
        
        if preferred_id is not None:
            if preferred_id in self._used_ids:
                raise BusinessRuleViolationError(
                    "individual_id_duplicate",
                    f"Individual ID {preferred_id} is already in use"
                )
            individual_id = IndividualID(preferred_id)
            self._used_ids.add(preferred_id)
            return individual_id
        
        # 最小の空きIDを検索
        for id_value in range(16):
            if id_value not in self._used_ids:
                self._used_ids.add(id_value)
                return IndividualID(id_value)
        
        raise BusinessRuleViolationError(
            "no_available_id",
            "No available individual ID (all 16 IDs are in use)"
        )
    
    def release_id(self, individual_id: IndividualID) -> bool:
        """個体ID解放"""
        if individual_id.value in self._used_ids:
            self._used_ids.remove(individual_id.value)
            return True
        return False
    
    def is_id_available(self, id_value: int) -> bool:
        """個体ID利用可能性確認"""
        if not 0 <= id_value <= 15:
            return False
        return id_value not in self._used_ids
    
    def get_used_ids(self) -> list[IndividualID]:
        """使用中個体ID一覧取得"""
        return [IndividualID(id_val) for id_val in sorted(self._used_ids)]
    
    def get_available_ids(self) -> list[IndividualID]:
        """利用可能個体ID一覧取得"""
        available = [i for i in range(16) if i not in self._used_ids]
        return [IndividualID(id_val) for id_val in available]
    
    def get_usage_count(self) -> int:
        """使用中個体数取得"""
        return len(self._used_ids)
    
    def is_at_capacity(self) -> bool:
        """16個体上限到達確認"""
        return len(self._used_ids) >= 16