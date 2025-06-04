"""
Agent6 Cache Layer: Infrastructure Layer Interface

Infrastructure Agent와의 통신 인터페이스
"""
import time
import numpy as np
from typing import Optional, List, Callable
from abc import ABC, abstractmethod


class InfrastructureInterface(ABC):
    """Infrastructure 층 통신 인터페이스"""
    
    @abstractmethod
    def load_frame(self, frame_id: str) -> Optional[np.ndarray]:
        """
        프레임 로드 (Infrastructure → Cache)
        
        Args:
            frame_id: 프레임 ID
            
        Returns:
            프레임 데이터 (45ms 이하)
        """
        pass
    
    @abstractmethod
    def preload_frames(self, frame_ids: List[str]) -> bool:
        """
        프레임 일괄 선읽기 요청
        
        Args:
            frame_ids: 선읽기 대상 프레임 ID 목록
            
        Returns:
            요청 성공 여부
        """
        pass
    
    @abstractmethod
    def get_frame_info(self, frame_id: str) -> Optional[dict]:
        """
        프레임 정보 조회
        
        Args:
            frame_id: 프레임 ID
            
        Returns:
            프레임 메타데이터
        """
        pass


class MockInfrastructureInterface(InfrastructureInterface):
    """Mock Infrastructure Interface (테스트용)"""
    
    def __init__(self, load_delay_ms: float = 30.0):
        self.load_delay_ms = load_delay_ms
        self._frame_cache = {}
    
    def load_frame(self, frame_id: str) -> Optional[np.ndarray]:
        """모의 프레임 로드"""
        # 로딩 지연 시뮬레이션
        time.sleep(self.load_delay_ms / 1000.0)
        
        # 작은 프레임 데이터 생성 (테스트용)
        frame_data = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        return frame_data
    
    def preload_frames(self, frame_ids: List[str]) -> bool:
        """모의 일괄 선읽기"""
        # 비동기 처리 시뮬레이션
        return True
    
    def get_frame_info(self, frame_id: str) -> Optional[dict]:
        """모의 프레임 정보"""
        return {
            'frame_id': frame_id,
            'width': 3840,
            'height': 2160,
            'channels': 3,
            'format': 'RGB',
            'size_bytes': 3840 * 2160 * 3
        }