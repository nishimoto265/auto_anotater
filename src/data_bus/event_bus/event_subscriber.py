"""
EventSubscriber - イベント購読管理
Agent側でのイベント購読を簡単にするためのヘルパークラス
"""
from typing import Callable, Dict, List, Optional
import logging

from .event_dispatcher import get_global_dispatcher
from .event_types import EventData, EVENT_FRAME_CHANGED, EVENT_BB_CREATED, EVENT_BB_UPDATED


class EventSubscriber:
    """
    イベント購読管理クラス
    Agent側でのイベント購読を簡単にする
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._subscriptions: Dict[str, str] = {}  # event_type -> subscription_id
        self._dispatcher = get_global_dispatcher()
        self._logger = logging.getLogger(f"{__name__}.{agent_name}")
    
    def subscribe_frame_changed(self, callback: Callable[[EventData], None]) -> bool:
        """フレーム切り替えイベント購読"""
        return self._subscribe(EVENT_FRAME_CHANGED, callback)
    
    def subscribe_bb_created(self, callback: Callable[[EventData], None]) -> bool:
        """BB作成イベント購読"""
        return self._subscribe(EVENT_BB_CREATED, callback)
    
    def subscribe_bb_updated(self, callback: Callable[[EventData], None]) -> bool:
        """BB更新イベント購読"""
        return self._subscribe(EVENT_BB_UPDATED, callback)
    
    def subscribe(self, event_type: str, callback: Callable[[EventData], None]) -> bool:
        """汎用イベント購読"""
        return self._subscribe(event_type, callback)
    
    def unsubscribe(self, event_type: str) -> bool:
        """イベント購読解除"""
        if event_type not in self._subscriptions:
            return False
        
        subscription_id = self._subscriptions[event_type]
        success = self._dispatcher.unsubscribe(subscription_id)
        
        if success:
            del self._subscriptions[event_type]
            self._logger.info(f"Unsubscribed from {event_type}")
        
        return success
    
    def unsubscribe_all(self) -> int:
        """全イベント購読解除"""
        count = 0
        for event_type in list(self._subscriptions.keys()):
            if self.unsubscribe(event_type):
                count += 1
        return count
    
    def get_subscribed_events(self) -> List[str]:
        """購読中のイベント型一覧取得"""
        return list(self._subscriptions.keys())
    
    def is_subscribed(self, event_type: str) -> bool:
        """イベント購読状態確認"""
        return event_type in self._subscriptions
    
    def _subscribe(self, event_type: str, callback: Callable[[EventData], None]) -> bool:
        """内部購読処理"""
        try:
            # 既存購読解除
            if event_type in self._subscriptions:
                self.unsubscribe(event_type)
            
            # 新規購読登録
            subscription_id = self._dispatcher.subscribe(event_type, callback)
            self._subscriptions[event_type] = subscription_id
            
            self._logger.info(f"Subscribed to {event_type}")
            return True
            
        except Exception as e:
            self._logger.error(f"Subscription failed for {event_type}: {e}")
            return False


class AgentEventHandler:
    """
    Agent用イベントハンドラーベースクラス
    継承してAgent固有のイベント処理を実装
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.subscriber = EventSubscriber(agent_name)
        self._setup_subscriptions()
    
    def _setup_subscriptions(self):
        """購読設定（サブクラスでオーバーライド）"""
        pass
    
    def on_frame_changed(self, event: EventData):
        """フレーム切り替えイベント処理"""
        pass
    
    def on_bb_created(self, event: EventData):
        """BB作成イベント処理"""
        pass
    
    def on_bb_updated(self, event: EventData):
        """BB更新イベント処理"""
        pass
    
    def on_bb_deleted(self, event: EventData):
        """BB削除イベント処理"""
        pass
    
    def on_performance_warning(self, event: EventData):
        """パフォーマンス警告イベント処理"""
        pass
    
    def on_error_occurred(self, event: EventData):
        """エラー発生イベント処理"""
        pass
    
    def shutdown(self):
        """リソース解放"""
        self.subscriber.unsubscribe_all()