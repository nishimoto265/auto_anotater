"""
BBリポジトリインターフェース - Agent3専用
BBエンティティ永続化抽象化・実装はPersistence層で提供
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.bb_entity import BBEntity
from ..entities.id_entity import IndividualID


class BBRepository(ABC):
    """
    BBリポジトリインターフェース
    
    実装はPersistence層（Agent7）で提供
    Domain層は永続化の詳細を知らない
    """
    
    @abstractmethod
    def save_bb(self, bb: BBEntity) -> bool:
        """
        BB保存
        
        Args:
            bb: 保存するBBエンティティ
            
        Returns:
            bool: 保存成功フラグ
        """
        pass
    
    @abstractmethod
    def save_bbs(self, bb_list: List[BBEntity]) -> bool:
        """
        BBリスト一括保存
        
        Args:
            bb_list: 保存するBBエンティティリスト
            
        Returns:
            bool: 保存成功フラグ
        """
        pass
    
    @abstractmethod
    def load_bb_by_id(self, bb_id: str) -> Optional[BBEntity]:
        """
        BB ID指定読み込み
        
        Args:
            bb_id: BB ID
            
        Returns:
            Optional[BBEntity]: BBエンティティ（存在しない場合はNone）
        """
        pass
    
    @abstractmethod
    def load_bbs_by_frame(self, frame_id: str) -> List[BBEntity]:
        """
        フレーム別BB読み込み
        
        Args:
            frame_id: フレームID
            
        Returns:
            List[BBEntity]: BBエンティティリスト
        """
        pass
    
    @abstractmethod
    def delete_bb(self, bb_id: str) -> bool:
        """
        BB削除
        
        Args:
            bb_id: 削除するBB ID
            
        Returns:
            bool: 削除成功フラグ
        """
        pass
    
    @abstractmethod
    def delete_bbs_by_frame(self, frame_id: str) -> int:
        """
        フレーム内全BB削除
        
        Args:
            frame_id: フレームID
            
        Returns:
            int: 削除されたBB数
        """
        pass
    
    @abstractmethod
    def find_bbs_by_individual(self, individual_id: IndividualID) -> List[BBEntity]:
        """
        個体別BB検索
        
        Args:
            individual_id: 個体ID
            
        Returns:
            List[BBEntity]: BBエンティティリスト
        """
        pass
    
    @abstractmethod
    def find_bbs_by_confidence_range(self, min_confidence: float, 
                                   max_confidence: float) -> List[BBEntity]:
        """
        信頼度範囲でBB検索
        
        Args:
            min_confidence: 最小信頼度
            max_confidence: 最大信頼度
            
        Returns:
            List[BBEntity]: BBエンティティリスト
        """
        pass
    
    @abstractmethod
    def count_bbs_by_frame(self, frame_id: str) -> int:
        """
        フレーム内BB数カウント
        
        Args:
            frame_id: フレームID
            
        Returns:
            int: BB数
        """
        pass
    
    @abstractmethod
    def exists_bb(self, bb_id: str) -> bool:
        """
        BB存在確認
        
        Args:
            bb_id: BB ID
            
        Returns:
            bool: 存在フラグ
        """
        pass
    
    @abstractmethod
    def update_bb(self, bb: BBEntity) -> bool:
        """
        BB更新
        
        Args:
            bb: 更新するBBエンティティ
            
        Returns:
            bool: 更新成功フラグ
        """
        pass