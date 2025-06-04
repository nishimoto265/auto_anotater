"""
プロジェクトリポジトリインターフェース - Agent3専用
プロジェクトエンティティ永続化抽象化・実装はPersistence層で提供
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict

from ..entities.project_entity import ProjectEntity


class ProjectRepository(ABC):
    """
    プロジェクトリポジトリインターフェース
    
    実装はPersistence層（Agent7）で提供
    Domain層は永続化の詳細を知らない
    """
    
    @abstractmethod
    def save_project(self, project: ProjectEntity) -> bool:
        """
        プロジェクト保存
        
        Args:
            project: 保存するプロジェクトエンティティ
            
        Returns:
            bool: 保存成功フラグ
        """
        pass
    
    @abstractmethod
    def load_project_by_id(self, project_id: str) -> Optional[ProjectEntity]:
        """
        プロジェクトID指定読み込み
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            Optional[ProjectEntity]: プロジェクトエンティティ（存在しない場合はNone）
        """
        pass
    
    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """
        プロジェクト削除
        
        Args:
            project_id: 削除するプロジェクトID
            
        Returns:
            bool: 削除成功フラグ
        """
        pass
    
    @abstractmethod
    def exists_project(self, project_id: str) -> bool:
        """
        プロジェクト存在確認
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            bool: 存在フラグ
        """
        pass
    
    @abstractmethod
    def get_all_projects(self) -> List[ProjectEntity]:
        """
        全プロジェクト取得
        
        Returns:
            List[ProjectEntity]: プロジェクトエンティティリスト
        """
        pass
    
    @abstractmethod
    def get_project_list(self) -> List[Dict]:
        """
        プロジェクト一覧取得（概要のみ）
        
        Returns:
            List[Dict]: プロジェクト概要リスト
        """
        pass
    
    @abstractmethod
    def find_projects_by_name(self, name_pattern: str) -> List[ProjectEntity]:
        """
        プロジェクト名検索
        
        Args:
            name_pattern: 名前検索パターン
            
        Returns:
            List[ProjectEntity]: マッチしたプロジェクトエンティティリスト
        """
        pass
    
    @abstractmethod
    def update_project(self, project: ProjectEntity) -> bool:
        """
        プロジェクト更新
        
        Args:
            project: 更新するプロジェクトエンティティ
            
        Returns:
            bool: 更新成功フラグ
        """
        pass
    
    @abstractmethod
    def update_project_settings(self, project_id: str, settings: Dict) -> bool:
        """
        プロジェクト設定更新
        
        Args:
            project_id: プロジェクトID
            settings: 更新する設定辞書
            
        Returns:
            bool: 更新成功フラグ
        """
        pass
    
    @abstractmethod
    def backup_project(self, project_id: str, backup_path: str) -> bool:
        """
        プロジェクトバックアップ
        
        Args:
            project_id: プロジェクトID
            backup_path: バックアップ先パス
            
        Returns:
            bool: バックアップ成功フラグ
        """
        pass
    
    @abstractmethod
    def restore_project(self, backup_path: str) -> Optional[ProjectEntity]:
        """
        プロジェクト復元
        
        Args:
            backup_path: バックアップファイルパス
            
        Returns:
            Optional[ProjectEntity]: 復元されたプロジェクトエンティティ
        """
        pass