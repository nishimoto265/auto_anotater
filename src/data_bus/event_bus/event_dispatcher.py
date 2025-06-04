"""
EventDispatcher - 非同期イベント配信エンジン
性能要件: イベント配信1ms以下、同時購読者8Agent対応
"""
import asyncio
import time
import threading
import uuid
from typing import Callable, Dict, List, Set, Any, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import logging

from .event_types import EventData, create_event


class EventDispatcher:
    """
    非同期イベント配信エンジン
    
    性能要件:
    - イベント配信: 1ms以下
    - 同時購読者: 8Agent対応
    - 配信保証: best effort
    """
    
    def __init__(self, max_workers: int = 8):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._subscription_ids: Dict[str, tuple] = {}  # subscription_id -> (event_type, callback)
        self._stats = {
            'total_published': 0,
            'total_delivered': 0,
            'avg_delivery_time': 0.0,
            'max_delivery_time': 0.0
        }
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="EventDispatcher")
        self._logger = logging.getLogger(__name__)
        
    def publish(self, event_type: str, data: dict = None, source_agent: str = "") -> bool:
        """
        イベント発行（1ms以下必達）
        
        Args:
            event_type: frame_changed, bb_created等
            data: イベントデータ
            source_agent: 発行元Agent名
            
        Returns:
            bool: 発行成功フラグ
        """
        start_time = time.perf_counter()
        
        try:
            # イベントデータ準備
            if data is None:
                data = {}
            
            event_data = create_event(event_type, source_agent=source_agent, **data)
            
            # 購読者一覧取得（コピーでスレッドセーフ化）
            with self._lock:
                subscribers = self._subscribers[event_type].copy()
                self._stats['total_published'] += 1
            
            if not subscribers:
                return True
            
            # 非同期配信（並列実行）
            futures = []
            for callback in subscribers:
                future = self._executor.submit(self._safe_callback, callback, event_data)
                futures.append(future)
            
            # 配信統計更新
            delivery_time = (time.perf_counter() - start_time) * 1000  # ms
            self._update_stats(delivery_time, len(subscribers))
            
            # 1ms以下チェック
            if delivery_time > 1.0:
                self._logger.warning(f"Event delivery exceeded 1ms: {delivery_time:.3f}ms for {event_type}")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Event publish failed: {e}")
            return False
    
    def subscribe(self, event_type: str, callback: Callable[[EventData], None]) -> str:
        """
        イベント購読登録
        
        Args:
            event_type: 購読するイベント型
            callback: コールバック関数
            
        Returns:
            str: 購読ID
        """
        subscription_id = str(uuid.uuid4())
        
        with self._lock:
            self._subscribers[event_type].append(callback)
            self._subscription_ids[subscription_id] = (event_type, callback)
        
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        購読解除
        
        Args:
            subscription_id: 購読ID
            
        Returns:
            bool: 解除成功フラグ
        """
        try:
            with self._lock:
                if subscription_id not in self._subscription_ids:
                    return False
                
                event_type, callback = self._subscription_ids[subscription_id]
                self._subscribers[event_type].remove(callback)
                del self._subscription_ids[subscription_id]
            
            return True
            
        except Exception as e:
            self._logger.error(f"Unsubscribe failed: {e}")
            return False
    
    def unsubscribe_all(self, event_type: str) -> int:
        """
        特定イベント型の全購読解除
        
        Returns:
            int: 解除した購読数
        """
        with self._lock:
            count = len(self._subscribers[event_type])
            
            # 該当購読IDを削除
            to_remove = []
            for sub_id, (evt_type, _) in self._subscription_ids.items():
                if evt_type == event_type:
                    to_remove.append(sub_id)
            
            for sub_id in to_remove:
                del self._subscription_ids[sub_id]
            
            # 購読者リストクリア
            self._subscribers[event_type].clear()
            
        return count
    
    def get_subscriber_count(self, event_type: str) -> int:
        """購読者数取得"""
        with self._lock:
            return len(self._subscribers[event_type])
    
    def get_all_event_types(self) -> Set[str]:
        """購読中の全イベント型取得"""
        with self._lock:
            return set(self._subscribers.keys())
    
    def get_stats(self) -> dict:
        """配信統計取得"""
        with self._lock:
            return self._stats.copy()
    
    def reset_stats(self):
        """統計リセット"""
        with self._lock:
            self._stats = {
                'total_published': 0,
                'total_delivered': 0,
                'avg_delivery_time': 0.0,
                'max_delivery_time': 0.0
            }
    
    def _safe_callback(self, callback: Callable, event_data: EventData) -> bool:
        """安全なコールバック実行"""
        try:
            callback(event_data)
            return True
        except Exception as e:
            self._logger.error(f"Callback execution failed: {e}")
            return False
    
    def _update_stats(self, delivery_time: float, subscriber_count: int):
        """配信統計更新"""
        with self._lock:
            delivered = subscriber_count
            total_delivered = self._stats['total_delivered'] + delivered
            
            # 平均配信時間更新
            if self._stats['total_delivered'] > 0:
                current_avg = self._stats['avg_delivery_time']
                new_avg = (current_avg * self._stats['total_delivered'] + delivery_time * delivered) / total_delivered
                self._stats['avg_delivery_time'] = new_avg
            else:
                self._stats['avg_delivery_time'] = delivery_time
            
            # 最大配信時間更新
            self._stats['max_delivery_time'] = max(self._stats['max_delivery_time'], delivery_time)
            self._stats['total_delivered'] = total_delivered
    
    def shutdown(self):
        """リソース解放"""
        self._executor.shutdown(wait=True)
        with self._lock:
            self._subscribers.clear()
            self._subscription_ids.clear()


# グローバルEventDispatcherインスタンス
_global_dispatcher: Optional[EventDispatcher] = None


def get_global_dispatcher() -> EventDispatcher:
    """グローバルEventDispatcher取得"""
    global _global_dispatcher
    if _global_dispatcher is None:
        _global_dispatcher = EventDispatcher()
    return _global_dispatcher


def publish_event(event_type: str, data: dict = None, source_agent: str = "") -> bool:
    """グローバルイベント発行"""
    return get_global_dispatcher().publish(event_type, data, source_agent)


def subscribe_event(event_type: str, callback: Callable[[EventData], None]) -> str:
    """グローバルイベント購読"""
    return get_global_dispatcher().subscribe(event_type, callback)