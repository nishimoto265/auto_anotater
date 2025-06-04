"""
フレームリポジトリインターフェース - Agent3専用
フレームエンティティ永続化抽象化・実装はPersistence層で提供
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.frame_entity import FrameEntity


class FrameRepository(ABC):
    """
    フレームリポジトリインターフェース
    
    実装はPersistence層（Agent7）で提供
    Domain層は永続化の詳細を知らない
    """
    
    @abstractmethod
    def save_frame(self, frame: FrameEntity) -> bool:
        """
        フレーム保存
        
        Args:
            frame: 保存するフレームエンティティ
            
        Returns:
            bool: 保存成功フラグ
        """
        pass
    
    @abstractmethod
    def load_frame_by_id(self, frame_id: str) -> Optional[FrameEntity]:
        """
        フレームID指定読み込み
        
        Args:
            frame_id: フレームID
            
        Returns:
            Optional[FrameEntity]: フレームエンティティ（存在しない場合はNone）
        """
        pass
    
    @abstractmethod
    def load_frames_by_range(self, start_frame_id: str, 
                           end_frame_id: str) -> List[FrameEntity]:
        """
        フレーム範囲指定読み込み
        
        Args:
            start_frame_id: 開始フレームID
            end_frame_id: 終了フレームID
            
        Returns:
            List[FrameEntity]: フレームエンティティリスト
        """
        pass
    
    @abstractmethod
    def delete_frame(self, frame_id: str) -> bool:
        """
        フレーム削除
        
        Args:
            frame_id: 削除するフレームID
            
        Returns:
            bool: 削除成功フラグ
        """
        pass
    
    @abstractmethod
    def exists_frame(self, frame_id: str) -> bool:
        """
        フレーム存在確認
        
        Args:
            frame_id: フレームID
            
        Returns:
            bool: 存在フラグ
        """
        pass
    
    @abstractmethod
    def get_frame_count(self) -> int:
        """
        総フレーム数取得
        
        Returns:
            int: フレーム数
        """
        pass
    
    @abstractmethod
    def get_frame_ids(self) -> List[str]:
        """
        全フレームID一覧取得
        
        Returns:
            List[str]: フレームIDリスト（ソート済み）
        """
        pass
    
    @abstractmethod
    def get_next_frame_id(self, current_frame_id: str) -> Optional[str]:
        """
        次フレームID取得
        
        Args:
            current_frame_id: 現在のフレームID
            
        Returns:
            Optional[str]: 次フレームID（存在しない場合はNone）
        """
        pass
    
    @abstractmethod
    def get_previous_frame_id(self, current_frame_id: str) -> Optional[str]:
        """
        前フレームID取得
        
        Args:
            current_frame_id: 現在のフレームID
            
        Returns:
            Optional[str]: 前フレームID（存在しない場合はNone）
        """
        pass
    
    @abstractmethod
    def find_frames_with_individual(self, individual_id: int) -> List[FrameEntity]:
        """
        指定個体が存在するフレーム検索
        
        Args:
            individual_id: 個体ID
            
        Returns:
            List[FrameEntity]: フレームエンティティリスト
        """
        pass
    
    @abstractmethod
    def find_empty_frames(self) -> List[FrameEntity]:
        """
        空フレーム（BBなし）検索
        
        Returns:
            List[FrameEntity]: 空フレームエンティティリスト
        """
        pass
    
    @abstractmethod
    def update_frame(self, frame: FrameEntity) -> bool:
        """
        フレーム更新
        
        Args:
            frame: 更新するフレームエンティティ
            
        Returns:
            bool: 更新成功フラグ
        """
        pass