"""
CommunicationProtocol - 通信プロトコル統一実装
Agent間通信の標準化とエラーハンドリング
"""
import time
import asyncio
from typing import Any, Dict, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import logging

from ..message_queue.message_serializer import Message, create_message


class CommunicationError(Exception):
    """通信エラー基底クラス"""
    pass


class TimeoutError(CommunicationError):
    """タイムアウトエラー"""
    pass


class AgentNotFoundError(CommunicationError):
    """Agent未発見エラー"""
    pass


class ServiceNotFoundError(CommunicationError):
    """サービス未発見エラー"""
    pass


class ProtocolError(CommunicationError):
    """プロトコルエラー"""
    pass


class CommunicationType(Enum):
    """通信種別"""
    SYNCHRONOUS = "sync"
    ASYNCHRONOUS = "async"
    EVENT = "event"
    BROADCAST = "broadcast"


@dataclass
class CommunicationResult:
    """通信結果"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    communication_type: CommunicationType = CommunicationType.SYNCHRONOUS


class CommunicationProtocol:
    """
    通信プロトコル統一実装
    Agent間通信の標準化とパフォーマンス最適化
    """
    
    def __init__(self, agent_name: str, queue_manager, event_dispatcher):
        self.agent_name = agent_name
        self._queue_manager = queue_manager
        self._event_dispatcher = event_dispatcher
        self._logger = logging.getLogger(f"{__name__}.{agent_name}")
        
        # 通信統計
        self._stats = {
            'sync_calls': 0,
            'async_calls': 0,
            'events_published': 0,
            'events_received': 0,
            'avg_response_time': 0.0,
            'max_response_time': 0.0,
            'timeout_count': 0,
            'error_count': 0
        }
    
    def call_service(self, target_agent: str, service_name: str, 
                    timeout: int = 1000, **kwargs) -> CommunicationResult:
        """
        同期サービス呼び出し
        
        Args:
            target_agent: 対象Agent名
            service_name: サービス名
            timeout: タイムアウト（ms）
            **kwargs: サービス引数
            
        Returns:
            CommunicationResult: 実行結果
        """
        start_time = time.perf_counter()
        
        try:
            # メッセージ構築
            message = {
                'service': service_name,
                'params': kwargs
            }
            
            # 同期呼び出し
            result = self._queue_manager.send_message(
                target_agent=target_agent,
                message=message,
                priority="normal",
                timeout=timeout
            )
            
            execution_time = (time.perf_counter() - start_time) * 1000  # ms
            self._update_sync_stats(execution_time, success=True)
            
            return CommunicationResult(
                success=True,
                result=result,
                execution_time=execution_time,
                communication_type=CommunicationType.SYNCHRONOUS
            )
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self._update_sync_stats(execution_time, success=False)
            
            # エラー種別判定
            if "timeout" in str(e).lower():
                error_type = TimeoutError(f"Service call timeout: {target_agent}.{service_name}")
                self._stats['timeout_count'] += 1
            elif "not found" in str(e).lower():
                error_type = ServiceNotFoundError(f"Service not found: {target_agent}.{service_name}")
            else:
                error_type = CommunicationError(f"Service call failed: {e}")
            
            self._stats['error_count'] += 1
            
            return CommunicationResult(
                success=False,
                error=str(error_type),
                execution_time=execution_time,
                communication_type=CommunicationType.SYNCHRONOUS
            )
    
    def call_service_async(self, target_agent: str, service_name: str, 
                          callback: Optional[Callable] = None, **kwargs) -> bool:
        """
        非同期サービス呼び出し
        
        Args:
            target_agent: 対象Agent名
            service_name: サービス名
            callback: 完了時コールバック
            **kwargs: サービス引数
            
        Returns:
            bool: 送信成功フラグ
        """
        try:
            message = {
                'service': service_name,
                'params': kwargs,
                'callback': callback
            }
            
            success = self._queue_manager.send_message_async(
                target_agent=target_agent,
                message=message,
                priority="normal"
            )
            
            if success:
                self._stats['async_calls'] += 1
            else:
                self._stats['error_count'] += 1
            
            return success
            
        except Exception as e:
            self._logger.error(f"Async service call failed: {e}")
            self._stats['error_count'] += 1
            return False
    
    def publish_event(self, event_type: str, data: dict = None) -> bool:
        """
        イベント発行
        
        Args:
            event_type: イベント型
            data: イベントデータ
            
        Returns:
            bool: 発行成功フラグ
        """
        try:
            success = self._event_dispatcher.publish(
                event_type=event_type,
                data=data or {},
                source_agent=self.agent_name
            )
            
            if success:
                self._stats['events_published'] += 1
            else:
                self._stats['error_count'] += 1
            
            return success
            
        except Exception as e:
            self._logger.error(f"Event publish failed: {e}")
            self._stats['error_count'] += 1
            return False
    
    def subscribe_event(self, event_type: str, 
                       callback: Callable[[Any], None]) -> Optional[str]:
        """
        イベント購読
        
        Args:
            event_type: イベント型
            callback: コールバック関数
            
        Returns:
            str: 購読ID
        """
        try:
            subscription_id = self._event_dispatcher.subscribe(event_type, callback)
            self._stats['events_received'] += 1
            return subscription_id
            
        except Exception as e:
            self._logger.error(f"Event subscription failed: {e}")
            return None
    
    def unsubscribe_event(self, subscription_id: str) -> bool:
        """イベント購読解除"""
        try:
            return self._event_dispatcher.unsubscribe(subscription_id)
        except Exception as e:
            self._logger.error(f"Event unsubscription failed: {e}")
            return False
    
    def broadcast_message(self, message: dict, target_agents: list = None) -> Dict[str, bool]:
        """
        ブロードキャストメッセージ送信
        
        Args:
            message: 送信メッセージ
            target_agents: 対象Agent一覧（None=全Agent）
            
        Returns:
            Dict[str, bool]: Agent別送信結果
        """
        results = {}
        
        if target_agents is None:
            target_agents = list(self._queue_manager.get_registered_agents())
        
        for agent in target_agents:
            if agent != self.agent_name:  # 自分以外
                try:
                    success = self._queue_manager.send_message_async(
                        target_agent=agent,
                        message=message,
                        priority="low"
                    )
                    results[agent] = success
                except Exception as e:
                    self._logger.error(f"Broadcast to {agent} failed: {e}")
                    results[agent] = False
        
        return results
    
    def ping(self, target_agent: str, timeout: int = 100) -> float:
        """
        Agent疎通確認（ping）
        
        Args:
            target_agent: 対象Agent名
            timeout: タイムアウト（ms）
            
        Returns:
            float: 応答時間（ms）、失敗時は-1
        """
        try:
            result = self.call_service(
                target_agent=target_agent,
                service_name="ping",
                timeout=timeout
            )
            
            if result.success:
                return result.execution_time
            else:
                return -1.0
                
        except Exception:
            return -1.0
    
    def get_stats(self) -> dict:
        """通信統計取得"""
        return self._stats.copy()
    
    def reset_stats(self):
        """統計リセット"""
        self._stats = {
            'sync_calls': 0,
            'async_calls': 0,
            'events_published': 0,
            'events_received': 0,
            'avg_response_time': 0.0,
            'max_response_time': 0.0,
            'timeout_count': 0,
            'error_count': 0
        }
    
    def _update_sync_stats(self, execution_time: float, success: bool):
        """同期通信統計更新"""
        if success:
            self._stats['sync_calls'] += 1
            
            # 平均応答時間更新
            calls = self._stats['sync_calls']
            if calls == 1:
                self._stats['avg_response_time'] = execution_time
            else:
                current_avg = self._stats['avg_response_time']
                self._stats['avg_response_time'] = (current_avg * (calls - 1) + execution_time) / calls
            
            # 最大応答時間更新
            self._stats['max_response_time'] = max(self._stats['max_response_time'], execution_time)


def with_timeout(timeout_ms: int):
    """タイムアウト付きデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.perf_counter() - start_time) * 1000
                
                if execution_time > timeout_ms:
                    raise TimeoutError(f"Function exceeded timeout: {execution_time:.2f}ms > {timeout_ms}ms")
                
                return result
                
            except Exception as e:
                execution_time = (time.perf_counter() - start_time) * 1000
                if execution_time > timeout_ms:
                    raise TimeoutError(f"Function timeout: {timeout_ms}ms")
                raise e
        
        return wrapper
    return decorator


def with_retry(max_retries: int = 3, delay_ms: int = 10):
    """リトライ付きデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay_ms / 1000.0)
                    else:
                        break
            
            raise last_exception
        
        return wrapper
    return decorator