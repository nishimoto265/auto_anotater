"""
QueueManager - Agent間メッセージキュー管理
性能要件: メッセージ転送1ms以下、優先度制御、容量制限
"""
import threading
import time
import uuid
from typing import Dict, Callable, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
import logging

from .priority_queue import PriorityQueue, FastQueue
from .message_serializer import Message, create_message, create_request_message, create_response_message


class QueueManager:
    """
    Agent間メッセージキュー管理
    
    性能要件:
    - メッセージ転送: 1ms以下
    - 優先度制御: 高/通常/低
    - 容量制限: メモリ効率運用
    """
    
    def __init__(self, max_workers: int = 8, default_timeout: int = 1000):
        # メッセージキュー（Agent別）
        self._queues: Dict[str, PriorityQueue] = {}
        self._fast_queues: Dict[str, FastQueue] = {}  # 高速処理用
        
        # メッセージハンドラー（Agent別、サービス別）
        self._handlers: Dict[str, Dict[str, Callable]] = {}
        
        # 同期通信用（request-response）
        self._pending_requests: Dict[str, Future] = {}
        
        # 設定
        self._default_timeout = default_timeout
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="QueueManager")
        
        # 統計
        self._stats = {
            'total_sent': 0,
            'total_received': 0,
            'avg_transfer_time': 0.0,
            'max_transfer_time': 0.0,
            'timeout_count': 0,
            'error_count': 0
        }
        
        # スレッドセーフティ
        self._lock = threading.RLock()
        self._running = True
        
        # ログ
        self._logger = logging.getLogger(__name__)
        
        # メッセージ処理ワーカー開始
        self._start_workers()
    
    def send_message(self, target_agent: str, message: dict, 
                    priority: str = "normal", timeout: int = None) -> Any:
        """
        同期メッセージ送信（1ms以下必達）
        
        Args:
            target_agent: 送信先Agent名
            message: メッセージデータ
            priority: high/normal/low
            timeout: タイムアウト（ms）
            
        Returns:
            Any: レスポンスデータ
        """
        start_time = time.perf_counter()
        
        if timeout is None:
            timeout = self._default_timeout
        
        try:
            # リクエストメッセージ作成
            request_msg = create_request_message(
                source="current_agent",  # TODO: 実際のAgent名取得
                target=target_agent,
                service_name=message.get('service', 'unknown'),
                params=message.get('params', {}),
                timeout=timeout
            )
            request_msg.priority = priority
            
            # 応答待機用Future作成
            future = self._executor.submit(self._wait_for_response, request_msg.id, timeout)
            
            with self._lock:
                self._pending_requests[request_msg.id] = future
            
            # メッセージ送信
            success = self._enqueue_message(target_agent, request_msg)
            if not success:
                raise Exception(f"Failed to enqueue message to {target_agent}")
            
            # 応答待機
            try:
                response = future.result(timeout=timeout/1000.0)  # ms to seconds
                
                # 転送時間統計更新
                transfer_time = (time.perf_counter() - start_time) * 1000  # ms
                self._update_stats_send(transfer_time)
                
                # 1ms以下チェック
                if transfer_time > 1.0:
                    self._logger.warning(f"Message transfer exceeded 1ms: {transfer_time:.3f}ms")
                
                return response.data.get('result')
                
            except TimeoutError:
                self._stats['timeout_count'] += 1
                raise Exception(f"Message timeout after {timeout}ms")
            
        except Exception as e:
            self._stats['error_count'] += 1
            self._logger.error(f"Message send failed: {e}")
            raise
        
        finally:
            # クリーンアップ
            with self._lock:
                self._pending_requests.pop(request_msg.id, None)
    
    def send_message_async(self, target_agent: str, message: dict, 
                          priority: str = "normal") -> bool:
        """
        非同期メッセージ送信
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            msg = create_message(
                source="current_agent",
                target=target_agent,
                message_type="async",
                data=message,
                priority=priority
            )
            
            return self._enqueue_message(target_agent, msg)
            
        except Exception as e:
            self._logger.error(f"Async message send failed: {e}")
            return False
    
    def register_handler(self, agent_name: str, service_name: str, 
                        handler: Callable[[dict], Any]):
        """
        メッセージハンドラー登録
        
        Args:
            agent_name: Agent名
            service_name: サービス名
            handler: ハンドラー関数
        """
        with self._lock:
            if agent_name not in self._handlers:
                self._handlers[agent_name] = {}
            self._handlers[agent_name][service_name] = handler
        
        self._logger.info(f"Registered handler: {agent_name}.{service_name}")
    
    def unregister_handler(self, agent_name: str, service_name: str) -> bool:
        """ハンドラー登録解除"""
        with self._lock:
            if agent_name in self._handlers and service_name in self._handlers[agent_name]:
                del self._handlers[agent_name][service_name]
                return True
        return False
    
    def register_agent(self, agent_name: str, use_fast_queue: bool = False):
        """Agent登録（キュー作成）"""
        with self._lock:
            if agent_name not in self._queues:
                self._queues[agent_name] = PriorityQueue()
                if use_fast_queue:
                    self._fast_queues[agent_name] = FastQueue()
                self._handlers[agent_name] = {}
        
        self._logger.info(f"Registered agent: {agent_name}")
    
    def unregister_agent(self, agent_name: str) -> bool:
        """Agent登録解除"""
        with self._lock:
            removed = False
            if agent_name in self._queues:
                del self._queues[agent_name]
                removed = True
            if agent_name in self._fast_queues:
                del self._fast_queues[agent_name]
            if agent_name in self._handlers:
                del self._handlers[agent_name]
        
        if removed:
            self._logger.info(f"Unregistered agent: {agent_name}")
        
        return removed
    
    def get_registered_agents(self) -> Set[str]:
        """登録済みAgent一覧取得"""
        with self._lock:
            return set(self._queues.keys())
    
    def get_queue_stats(self, agent_name: str) -> Optional[dict]:
        """Agent別キュー統計取得"""
        with self._lock:
            if agent_name in self._queues:
                return self._queues[agent_name].get_stats()
        return None
    
    def get_global_stats(self) -> dict:
        """グローバル統計取得"""
        with self._lock:
            return self._stats.copy()
    
    def reset_stats(self):
        """統計リセット"""
        with self._lock:
            self._stats = {
                'total_sent': 0,
                'total_received': 0,
                'avg_transfer_time': 0.0,
                'max_transfer_time': 0.0,
                'timeout_count': 0,
                'error_count': 0
            }
    
    def _enqueue_message(self, target_agent: str, message: Message) -> bool:
        """メッセージをキューに追加"""
        with self._lock:
            # 高速キューを優先使用
            if target_agent in self._fast_queues and message.priority == "high":
                return self._fast_queues[target_agent].put_nowait(message)
            
            # 通常キュー使用
            if target_agent in self._queues:
                return self._queues[target_agent].put(message, block=False)
        
        return False
    
    def _dequeue_message(self, agent_name: str) -> Optional[Message]:
        """メッセージをキューから取得"""
        with self._lock:
            # 高速キューを優先確認
            if agent_name in self._fast_queues:
                fast_msg = self._fast_queues[agent_name].get_nowait()
                if fast_msg:
                    return fast_msg
            
            # 通常キュー確認
            if agent_name in self._queues and not self._queues[agent_name].empty():
                return self._queues[agent_name].get(block=False)
        
        return None
    
    def _process_message(self, message: Message):
        """メッセージ処理"""
        try:
            target_agent = message.target
            
            # ハンドラー取得
            with self._lock:
                handlers = self._handlers.get(target_agent, {})
            
            if message.type == "request":
                # リクエスト処理
                service_name = message.data.get('service', 'unknown')
                handler = handlers.get(service_name)
                
                if handler:
                    # ハンドラー実行
                    params = message.data.get('params', {})
                    result = handler(params)
                    
                    # レスポンス送信
                    response = create_response_message(message, result, success=True)
                    self._send_response(response)
                else:
                    # ハンドラー未登録エラー
                    error_msg = f"Handler not found: {target_agent}.{service_name}"
                    response = create_response_message(message, None, success=False, error=error_msg)
                    self._send_response(response)
            
            elif message.type == "response":
                # レスポンス処理
                self._handle_response(message)
            
            elif message.type == "async":
                # 非同期メッセージ処理
                # TODO: 非同期ハンドラー実装
                pass
            
            self._stats['total_received'] += 1
            
        except Exception as e:
            self._logger.error(f"Message processing failed: {e}")
            if message.type == "request":
                response = create_response_message(message, None, success=False, error=str(e))
                self._send_response(response)
    
    def _send_response(self, response: Message):
        """レスポンス送信"""
        source_agent = response.target
        with self._lock:
            if source_agent in self._pending_requests:
                request_id = response.data.get('request_id')
                if request_id in self._pending_requests:
                    future = self._pending_requests[request_id]
                    if not future.done():
                        future.set_result(response)
    
    def _handle_response(self, response: Message):
        """レスポンス処理"""
        request_id = response.data.get('request_id')
        with self._lock:
            if request_id in self._pending_requests:
                future = self._pending_requests[request_id]
                if not future.done():
                    future.set_result(response)
    
    def _wait_for_response(self, request_id: str, timeout: int) -> Message:
        """レスポンス待機"""
        start_time = time.perf_counter()
        timeout_seconds = timeout / 1000.0
        
        while time.perf_counter() - start_time < timeout_seconds:
            with self._lock:
                if request_id in self._pending_requests:
                    future = self._pending_requests[request_id]
                    try:
                        return future.result(timeout=0.001)  # 1ms poll
                    except TimeoutError:
                        continue
            time.sleep(0.0001)  # 0.1ms sleep
        
        raise TimeoutError(f"Response timeout for request {request_id}")
    
    def _start_workers(self):
        """メッセージ処理ワーカー開始"""
        for i in range(4):  # 4つのワーカー
            self._executor.submit(self._worker_loop, f"worker-{i}")
    
    def _worker_loop(self, worker_name: str):
        """ワーカーループ"""
        self._logger.info(f"Started worker: {worker_name}")
        
        while self._running:
            try:
                # 全Agentのキューをポーリング
                with self._lock:
                    agent_names = list(self._queues.keys())
                
                message_processed = False
                for agent_name in agent_names:
                    message = self._dequeue_message(agent_name)
                    if message:
                        self._process_message(message)
                        message_processed = True
                        break
                
                if not message_processed:
                    time.sleep(0.001)  # 1ms休憩
                
            except Exception as e:
                self._logger.error(f"Worker {worker_name} error: {e}")
                time.sleep(0.01)  # エラー時は10ms休憩
    
    def _update_stats_send(self, transfer_time: float):
        """送信統計更新"""
        with self._lock:
            self._stats['total_sent'] += 1
            
            # 平均転送時間更新
            sent = self._stats['total_sent']
            if sent == 1:
                self._stats['avg_transfer_time'] = transfer_time
            else:
                current_avg = self._stats['avg_transfer_time']
                self._stats['avg_transfer_time'] = (current_avg * (sent - 1) + transfer_time) / sent
            
            # 最大転送時間更新
            self._stats['max_transfer_time'] = max(self._stats['max_transfer_time'], transfer_time)
    
    def shutdown(self):
        """リソース解放"""
        self._running = False
        self._executor.shutdown(wait=True)
        
        with self._lock:
            for queue in self._queues.values():
                queue.clear()
            for fast_queue in self._fast_queues.values():
                fast_queue.clear()
            
            self._queues.clear()
            self._fast_queues.clear()
            self._handlers.clear()
            self._pending_requests.clear()


# グローバルQueueManagerインスタンス
_global_queue_manager: Optional[QueueManager] = None


def get_global_queue_manager() -> QueueManager:
    """グローバルQueueManager取得"""
    global _global_queue_manager
    if _global_queue_manager is None:
        _global_queue_manager = QueueManager()
    return _global_queue_manager