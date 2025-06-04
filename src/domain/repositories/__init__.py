# リポジトリインターフェース - Agent3専用
# ドメイン層からの永続化抽象化インターフェース

from .bb_repository import BBRepository
from .frame_repository import FrameRepository
from .project_repository import ProjectRepository

__all__ = [
    'BBRepository',
    'FrameRepository',
    'ProjectRepository'
]