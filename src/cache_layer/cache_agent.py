"""
Agent6 Cache Layer: Main Cache Agent

프레임 전환 50ms 이하 절대 달성을 위한 통합 캐시 에이전트
"""
import time
import threading
import numpy as np
from typing import Optional, Dict, Any, Callable

from .frame_cache.lru_cache import LRUFrameCache
from .frame_cache.memory_monitor import MemoryMonitor
from .frame_cache.cache_optimizer import CacheOptimizer
from .frame_cache.preloader import AsyncPreloader
from .interfaces.infrastructure_interface import InfrastructureInterface, MockInfrastructureInterface
from .interfaces.data_bus_interface import DataBusInterface, MockDataBusInterface, CacheEventPublisher


class CacheAgent:
    """
    Agent6 메인 캐시 에이전트
    
    프레임 전환 50ms 이하 절대 달성을 위한 통합 캐시 시스템
    """
    
    def __init__(self, 
                 max_cache_size: int = 100,
                 memory_limit_gb: float = 20.0,
                 infrastructure_interface: Optional[InfrastructureInterface] = None,
                 data_bus_interface: Optional[DataBusInterface] = None):
        """
        Args:
            max_cache_size: 최대 캐시 크기 (프레임 수)
            memory_limit_gb: 메모리 한도 (GB)
            infrastructure_interface: Infrastructure 층 인터페이스
            data_bus_interface: Data Bus 인터페이스
        """
        self.max_cache_size = max_cache_size
        self.memory_limit = int(memory_limit_gb * 1024**3)
        
        # 인터페이스 설정
        self.infrastructure = infrastructure_interface or MockInfrastructureInterface()
        self.data_bus = data_bus_interface or MockDataBusInterface()
        
        # 핵심 컴포넌트 초기화
        self._initialize_components()
        
        # 이벤트 발행자
        self.event_publisher = CacheEventPublisher(self.data_bus)
        
        # 에이전트 상태
        self._running = False
        self._lock = threading.Lock()
        
        # 성능 메트릭
        self._frame_switch_count = 0
        self._total_switch_time = 0.0
        self._last_frame_id = None
    
    def _initialize_components(self):
        """핵심 컴포넌트 초기화"""
        # LRU 캐시
        self.cache = LRUFrameCache(
            max_size=self.max_cache_size,
            memory_limit=self.memory_limit
        )
        
        # 메모리 모니터
        self.memory_monitor = MemoryMonitor(
            cache_instance=self.cache,
            monitoring_interval=1.0
        )
        
        # 캐시 최적화기
        self.cache_optimizer = CacheOptimizer(
            cache_instance=self.cache,
            memory_monitor=self.memory_monitor
        )
        
        # 비동기 프리로더
        self.preloader = AsyncPreloader(
            cache_instance=self.cache,
            preload_range=50,
            max_concurrent=3
        )
        
        # 프리로더에 Infrastructure 인터페이스 연결
        self.preloader.set_frame_loader(self.infrastructure.load_frame)
        
        # 메모리 경고 콜백 설정
        from .frame_cache.memory_monitor import MemoryWarningLevel
        self.memory_monitor.register_warning_callback(
            level=MemoryWarningLevel.WARNING,
            callback=self._on_memory_warning
        )
    
    def start(self):
        """캐시 에이전트 시작"""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            
            # 각 컴포넌트 시작
            self.memory_monitor.start_monitoring()
            self.cache_optimizer.start_optimization()
            
            print("Agent6 Cache Layer started successfully")
    
    def stop(self):
        """캐시 에이전트 정지"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            # 각 컴포넌트 정지
            self.memory_monitor.stop_monitoring()
            self.cache_optimizer.stop_optimization()
            self.preloader.stop_preloader()
            
            print("Agent6 Cache Layer stopped")
    
    def get_frame(self, frame_id: str) -> Optional[np.ndarray]:
        """
        프레임 조회 (50ms 이하 보장)
        
        Args:
            frame_id: 프레임 ID
            
        Returns:
            프레임 데이터
        """
        start_time = time.perf_counter()
        
        # 캐시에서 조회
        frame_data = self.cache.get(frame_id)
        
        if frame_data is not None:
            # 캐시 히트
            access_time = (time.perf_counter() - start_time) * 1000
            self.event_publisher.publish_cache_hit(frame_id, access_time)
            self.preloader.record_frame_access(frame_id)
            
            # 다음 프레임 선읽기 트리거
            self._trigger_preload(frame_id)
            
        else:
            # 캐시 미스 - Infrastructure에서 로드
            frame_data = self.infrastructure.load_frame(frame_id)
            if frame_data is not None:
                # 캐시에 저장
                self.cache.put(frame_id, frame_data)
                
                load_time = (time.perf_counter() - start_time) * 1000
                self.event_publisher.publish_cache_miss(frame_id, load_time)
                
                # 선읽기 트리거
                self._trigger_preload(frame_id)
        
        # 프레임 전환 성능 기록
        self._record_frame_switch(frame_id, start_time)
        
        return frame_data
    
    def preload_frames(self, current_frame: str, direction: str = "both") -> bool:
        """
        수동 프레임 선읽기
        
        Args:
            current_frame: 현재 프레임
            direction: 선읽기 방향 ("forward", "backward", "both")
            
        Returns:
            선읽기 시작 성공 여부
        """
        return self.preloader.start_preload(current_frame, direction)
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        cache_stats = self.cache.get_performance_stats()
        memory_stats = self.memory_monitor.get_memory_statistics()
        optimizer_stats = self.cache_optimizer.get_optimization_statistics()
        preloader_stats = self.preloader.get_preload_statistics()
        
        # 프레임 전환 평균 시간
        avg_switch_time = 0.0
        if self._frame_switch_count > 0:
            avg_switch_time = self._total_switch_time / self._frame_switch_count
        
        return {
            'cache': cache_stats,
            'memory': memory_stats,
            'optimizer': optimizer_stats,
            'preloader': preloader_stats,
            'performance': {
                'avg_frame_switch_time_ms': avg_switch_time,
                'total_frame_switches': self._frame_switch_count,
                'running': self._running
            }
        }
    
    def optimize_cache(self) -> bool:
        """수동 캐시 최적화 트리거"""
        return self.cache_optimizer.emergency_optimization()
    
    def clear_cache(self):
        """캐시 클리어"""
        self.cache.clear()
        self._frame_switch_count = 0
        self._total_switch_time = 0.0
    
    # Private methods
    
    def _trigger_preload(self, current_frame: str):
        """선읽기 트리거"""
        # 백그라운드에서 선읽기 시작
        self.preloader.start_preload(current_frame, direction="both")
    
    def _record_frame_switch(self, frame_id: str, start_time: float):
        """프레임 전환 성능 기록"""
        switch_time = (time.perf_counter() - start_time) * 1000
        
        with self._lock:
            self._frame_switch_count += 1
            self._total_switch_time += switch_time
        
        # 최적화기에 기록
        self.cache_optimizer.record_frame_switch_time(switch_time, frame_id)
        
        # 성능 경고 체크
        if switch_time > 45.0:  # 45ms 경고 임계치
            self.event_publisher.publish_performance_warning(
                "frame_switch_time", switch_time, 45.0
            )
        
        # 프레임 변경 이벤트 발행
        if self._last_frame_id:
            self.event_publisher.publish_frame_changed(
                frame_id, self._last_frame_id, switch_time
            )
        
        self._last_frame_id = frame_id
    
    def _on_memory_warning(self, memory_status):
        """메모리 경고 콜백"""
        self.event_publisher.publish_memory_warning(
            memory_status.cache_memory_gb,
            20.0  # 20GB 한도
        )
        
        # 긴급 메모리 정리
        if memory_status.cache_memory_gb > 19.0:
            self.memory_monitor.force_memory_cleanup(target_memory_gb=15.0)
    
    def __enter__(self):
        """Context manager 진입"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.stop()


# Factory function for easy instantiation
def create_cache_agent(memory_limit_gb: float = 20.0, 
                      cache_size: int = 100) -> CacheAgent:
    """
    캐시 에이전트 생성 팩토리 함수
    
    Args:
        memory_limit_gb: 메모리 한도 (GB)
        cache_size: 캐시 크기 (프레임 수)
        
    Returns:
        설정된 캐시 에이전트
    """
    return CacheAgent(
        max_cache_size=cache_size,
        memory_limit_gb=memory_limit_gb
    )