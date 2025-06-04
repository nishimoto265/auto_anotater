"""
Event Types - イベント型定義
Agent間で使用される全イベント型の定義
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# 必須イベント型定義
EVENT_FRAME_CHANGED = "frame_changed"
EVENT_BB_CREATED = "bb_created"
EVENT_BB_UPDATED = "bb_updated"
EVENT_BB_DELETED = "bb_deleted"
EVENT_TRACKING_STARTED = "tracking_started"
EVENT_TRACKING_COMPLETED = "tracking_completed"
EVENT_PERFORMANCE_WARNING = "performance_warning"
EVENT_CACHE_HIT = "cache_hit"
EVENT_CACHE_MISS = "cache_miss"
EVENT_MEMORY_USAGE = "memory_usage"
EVENT_ERROR_OCCURRED = "error_occurred"


@dataclass
class EventData:
    """イベントデータ基底クラス"""
    timestamp: float = field(default_factory=time.perf_counter)
    source_agent: str = ""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FrameChangedEvent(EventData):
    """フレーム切り替えイベント"""
    current_frame_id: str = ""
    previous_frame_id: str = ""
    switch_time: float = 0.0


@dataclass
class BBCreatedEvent(EventData):
    """BB作成イベント"""
    bb_entity: Dict[str, Any] = field(default_factory=dict)
    frame_id: str = ""
    created_at: float = field(default_factory=time.perf_counter)


@dataclass
class BBUpdatedEvent(EventData):
    """BB更新イベント"""
    bb_entity: Dict[str, Any] = field(default_factory=dict)
    previous_bb: Dict[str, Any] = field(default_factory=dict)
    frame_id: str = ""


@dataclass
class BBDeletedEvent(EventData):
    """BB削除イベント"""
    bb_id: int = 0
    frame_id: str = ""


@dataclass
class TrackingStartedEvent(EventData):
    """追跡開始イベント"""
    frame_id: str = ""
    target_ids: list = field(default_factory=list)


@dataclass
class TrackingCompletedEvent(EventData):
    """追跡完了イベント"""
    start_frame_id: str = ""
    end_frame_id: str = ""
    tracking_results: list = field(default_factory=list)
    processing_time: float = 0.0


@dataclass
class PerformanceWarningEvent(EventData):
    """パフォーマンス警告イベント"""
    metric_name: str = ""
    value: float = 0.0
    threshold: float = 0.0
    severity: str = "info"  # info/warning/error


@dataclass
class CacheHitEvent(EventData):
    """キャッシュヒットイベント"""
    frame_id: str = ""
    access_time: float = 0.0


@dataclass
class CacheMissEvent(EventData):
    """キャッシュミスイベント"""
    frame_id: str = ""
    load_time: float = 0.0


@dataclass
class MemoryUsageEvent(EventData):
    """メモリ使用量イベント"""
    current_usage: float = 0.0  # GB
    limit: float = 20.0  # GB
    usage_ratio: float = 0.0  # 0.0-1.0


@dataclass
class ErrorOccurredEvent(EventData):
    """エラー発生イベント"""
    error_type: str = ""
    error_message: str = ""
    source_agent: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


# イベント型とデータクラスのマッピング
EVENT_TYPE_MAPPING = {
    EVENT_FRAME_CHANGED: FrameChangedEvent,
    EVENT_BB_CREATED: BBCreatedEvent,
    EVENT_BB_UPDATED: BBUpdatedEvent,
    EVENT_BB_DELETED: BBDeletedEvent,
    EVENT_TRACKING_STARTED: TrackingStartedEvent,
    EVENT_TRACKING_COMPLETED: TrackingCompletedEvent,
    EVENT_PERFORMANCE_WARNING: PerformanceWarningEvent,
    EVENT_CACHE_HIT: CacheHitEvent,
    EVENT_CACHE_MISS: CacheMissEvent,
    EVENT_MEMORY_USAGE: MemoryUsageEvent,
    EVENT_ERROR_OCCURRED: ErrorOccurredEvent,
}


def create_event(event_type: str, **kwargs) -> EventData:
    """イベントインスタンス生成"""
    event_class = EVENT_TYPE_MAPPING.get(event_type, EventData)
    return event_class(**kwargs)