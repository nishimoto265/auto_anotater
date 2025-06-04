"""
Agent6 Cache Layer: Data Bus Interface

Data Bus Agent와의 이벤트 통신 인터페이스
"""
import time
import threading
from typing import Dict, Any, Callable, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """이벤트 타입"""
    FRAME_CHANGED = "frame_changed"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    MEMORY_WARNING = "memory_warning"
    PERFORMANCE_WARNING = "performance_warning"


@dataclass
class CacheEvent:
    """캐시 이벤트"""
    event_type: EventType
    timestamp: float
    data: Dict[str, Any]
    source: str = "agent6_cache"


class DataBusInterface(ABC):
    """Data Bus 통신 인터페이스"""
    
    @abstractmethod
    def publish_event(self, event: CacheEvent) -> bool:
        """
        이벤트 발행 (1ms 이하)
        
        Args:
            event: 발행할 이벤트
            
        Returns:
            발행 성공 여부
        """
        pass
    
    @abstractmethod
    def subscribe_event(self, event_type: EventType, callback: Callable[[CacheEvent], None]):
        """
        이벤트 구독
        
        Args:
            event_type: 구독할 이벤트 타입
            callback: 이벤트 핸들러
        """
        pass
    
    @abstractmethod
    def unsubscribe_event(self, event_type: EventType, callback: Callable[[CacheEvent], None]):
        """
        이벤트 구독 해제
        
        Args:
            event_type: 구독 해제할 이벤트 타입
            callback: 이벤트 핸들러
        """
        pass


class MockDataBusInterface(DataBusInterface):
    """Mock Data Bus Interface (테스트용)"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[CacheEvent] = []
        self._lock = threading.Lock()
    
    def publish_event(self, event: CacheEvent) -> bool:
        """모의 이벤트 발행"""
        start_time = time.perf_counter()
        
        with self._lock:
            # 이벤트 히스토리에 저장
            self._event_history.append(event)
            
            # 구독자들에게 이벤트 전달
            subscribers = self._subscribers.get(event.event_type, [])
            for callback in subscribers:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Event callback error: {e}")
        
        # 1ms 이하 보장 확인
        elapsed_time = (time.perf_counter() - start_time) * 1000
        return elapsed_time <= 1.0
    
    def subscribe_event(self, event_type: EventType, callback: Callable[[CacheEvent], None]):
        """모의 이벤트 구독"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
    
    def unsubscribe_event(self, event_type: EventType, callback: Callable[[CacheEvent], None]):
        """모의 이벤트 구독 해제"""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                except ValueError:
                    pass  # 콜백이 목록에 없음
    
    def get_event_history(self) -> List[CacheEvent]:
        """이벤트 히스토리 조회 (테스트용)"""
        with self._lock:
            return self._event_history.copy()
    
    def clear_history(self):
        """이벤트 히스토리 클리어 (테스트용)"""
        with self._lock:
            self._event_history.clear()


class CacheEventPublisher:
    """캐시 이벤트 발행자"""
    
    def __init__(self, data_bus: DataBusInterface):
        self.data_bus = data_bus
    
    def publish_cache_hit(self, frame_id: str, access_time_ms: float):
        """캐시 히트 이벤트 발행"""
        event = CacheEvent(
            event_type=EventType.CACHE_HIT,
            timestamp=time.time(),
            data={
                'frame_id': frame_id,
                'access_time_ms': access_time_ms
            }
        )
        self.data_bus.publish_event(event)
    
    def publish_cache_miss(self, frame_id: str, load_time_ms: float):
        """캐시 미스 이벤트 발행"""
        event = CacheEvent(
            event_type=EventType.CACHE_MISS,
            timestamp=time.time(),
            data={
                'frame_id': frame_id,
                'load_time_ms': load_time_ms
            }
        )
        self.data_bus.publish_event(event)
    
    def publish_memory_warning(self, usage_gb: float, limit_gb: float):
        """메모리 경고 이벤트 발행"""
        event = CacheEvent(
            event_type=EventType.MEMORY_WARNING,
            timestamp=time.time(),
            data={
                'usage_gb': usage_gb,
                'limit_gb': limit_gb,
                'usage_percent': (usage_gb / limit_gb) * 100
            }
        )
        self.data_bus.publish_event(event)
    
    def publish_performance_warning(self, metric_name: str, value: float, threshold: float):
        """성능 경고 이벤트 발행"""
        event = CacheEvent(
            event_type=EventType.PERFORMANCE_WARNING,
            timestamp=time.time(),
            data={
                'metric_name': metric_name,
                'value': value,
                'threshold': threshold,
                'severity': 'warning' if value > threshold else 'info'
            }
        )
        self.data_bus.publish_event(event)
    
    def publish_frame_changed(self, current_frame: str, previous_frame: str, switch_time_ms: float):
        """프레임 변경 이벤트 발행"""
        event = CacheEvent(
            event_type=EventType.FRAME_CHANGED,
            timestamp=time.time(),
            data={
                'current_frame_id': current_frame,
                'previous_frame_id': previous_frame,
                'switch_time_ms': switch_time_ms
            }
        )
        self.data_bus.publish_event(event)