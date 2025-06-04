"""
LayerInterface - Agent間統一API呼び出しインターフェース
レイヤー間の統一通信インターフェースとサービス管理
"""
import time
from typing import Any, Dict, Optional, Callable, List
import logging

from .communication_protocol import CommunicationProtocol, CommunicationResult, CommunicationError
from .api_registry import ApiRegistry, get_global_api_registry
from ..message_queue.queue_manager import QueueManager, get_global_queue_manager
from ..event_bus.event_dispatcher import EventDispatcher, get_global_dispatcher


class LayerInterface:
    """
    Agent間統一API呼び出しインターフェース
    
    使用例:
    result = layer_interface.call_service(
        "cache_layer", "get_frame", frame_id="000001"
    )
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        
        # 依存コンポーネント
        self._queue_manager = get_global_queue_manager()
        self._event_dispatcher = get_global_dispatcher()
        self._api_registry = get_global_api_registry()
        
        # 通信プロトコル
        self._protocol = CommunicationProtocol(
            agent_name=agent_name,
            queue_manager=self._queue_manager,
            event_dispatcher=self._event_dispatcher
        )
        
        # Agent登録
        self._queue_manager.register_agent(agent_name, use_fast_queue=True)
        
        # 統計
        self._call_stats = {
            'successful_calls': 0,
            'failed_calls': 0,
            'avg_response_time': 0.0,
            'max_response_time': 0.0,
            'calls_by_layer': {},
            'calls_by_service': {}
        }
        
        self._logger = logging.getLogger(f"{__name__}.{agent_name}")
        self._logger.info(f"LayerInterface initialized for agent: {agent_name}")
    
    def call_service(self, layer_name: str, service_name: str, 
                    timeout: int = None, **kwargs) -> Any:
        """
        レイヤー間API呼び出し
        
        Args:
            layer_name: presentation, application, domain等
            service_name: get_frame, create_bb等
            timeout: タイムアウト（ms）
            **kwargs: サービス引数
            
        Returns:
            Any: サービス実行結果
            
        Raises:
            CommunicationError: 通信エラー
        """
        start_time = time.perf_counter()
        
        try:
            # サービス発見
            service_def = self._api_registry.lookup_service(layer_name, service_name)
            if not service_def:
                raise CommunicationError(f"Service not found: {layer_name}.{service_name}")
            
            # タイムアウト設定
            if timeout is None:
                timeout = service_def.timeout
            
            # サービス呼び出し
            result = self._protocol.call_service(
                target_agent=layer_name,
                service_name=service_name,
                timeout=timeout,
                **kwargs
            )
            
            if result.success:
                self._update_call_stats(layer_name, service_name, result.execution_time, True)
                return result.result
            else:
                self._update_call_stats(layer_name, service_name, result.execution_time, False)
                raise CommunicationError(result.error)
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self._update_call_stats(layer_name, service_name, execution_time, False)
            raise e
    
    def call_service_async(self, layer_name: str, service_name: str,
                          callback: Optional[Callable] = None, **kwargs) -> bool:
        """
        非同期レイヤー間API呼び出し
        
        Args:
            layer_name: 対象レイヤー名
            service_name: サービス名
            callback: 完了時コールバック
            **kwargs: サービス引数
            
        Returns:
            bool: 送信成功フラグ
        """
        try:
            success = self._protocol.call_service_async(
                target_agent=layer_name,
                service_name=service_name,
                callback=callback,
                **kwargs
            )
            
            if success:
                self._update_async_stats(layer_name, service_name)
            
            return success
            
        except Exception as e:
            self._logger.error(f"Async service call failed: {e}")
            return False
    
    def register_service(self, service_name: str, handler: Callable,
                        timeout: int = 1000, description: str = "",
                        version: str = "1.0") -> bool:
        """
        サービス登録
        
        Args:
            service_name: サービス名
            handler: ハンドラー関数
            timeout: タイムアウト（ms）
            description: サービス説明
            version: バージョン
            
        Returns:
            bool: 登録成功フラグ
        """
        try:
            # API Registry登録
            success = self._api_registry.register_service(
                agent_name=self.agent_name,
                service_name=service_name,
                handler=handler,
                timeout=timeout,
                description=description,
                version=version
            )
            
            if success:
                # Queue Manager登録
                self._queue_manager.register_handler(
                    agent_name=self.agent_name,
                    service_name=service_name,
                    handler=handler
                )
                
                self._logger.info(f"Registered service: {service_name}")
            
            return success
            
        except Exception as e:
            self._logger.error(f"Service registration failed: {e}")
            return False
    
    def unregister_service(self, service_name: str) -> bool:
        """サービス登録解除"""
        try:
            # API Registry解除
            api_success = self._api_registry.unregister_service(self.agent_name, service_name)
            
            # Queue Manager解除
            queue_success = self._queue_manager.unregister_handler(self.agent_name, service_name)
            
            if api_success:
                self._logger.info(f"Unregistered service: {service_name}")
            
            return api_success
            
        except Exception as e:
            self._logger.error(f"Service unregistration failed: {e}")
            return False
    
    def publish_event(self, event_type: str, data: dict = None) -> bool:
        """イベント発行"""
        return self._protocol.publish_event(event_type, data)
    
    def subscribe_event(self, event_type: str, 
                       callback: Callable[[Any], None]) -> Optional[str]:
        """イベント購読"""
        return self._protocol.subscribe_event(event_type, callback)
    
    def unsubscribe_event(self, subscription_id: str) -> bool:
        """イベント購読解除"""
        return self._protocol.unsubscribe_event(subscription_id)
    
    def heartbeat(self, metadata: Dict[str, Any] = None) -> bool:
        """生存確認送信"""
        return self._api_registry.heartbeat(self.agent_name, metadata)
    
    def ping_agent(self, target_agent: str, timeout: int = 100) -> float:
        """Agent疎通確認"""
        return self._protocol.ping(target_agent, timeout)
    
    def get_available_services(self, layer_name: str = None) -> List[dict]:
        """利用可能サービス一覧取得"""
        if layer_name:
            services = self._api_registry.find_services_by_agent(layer_name)
            return [service.to_dict() for service in services]
        else:
            return list(self._api_registry.get_all_services().values())
    
    def get_available_agents(self) -> List[str]:
        """利用可能Agent一覧取得"""
        return list(self._api_registry.get_available_agents())
    
    def get_service_health(self) -> Dict[str, dict]:
        """サービス健全性取得"""
        return self._api_registry.get_service_health()
    
    def get_call_stats(self) -> dict:
        """呼び出し統計取得"""
        stats = self._call_stats.copy()
        stats.update({
            'protocol_stats': self._protocol.get_stats(),
            'queue_stats': self._queue_manager.get_global_stats(),
            'event_stats': self._event_dispatcher.get_stats(),
            'registry_stats': self._api_registry.get_service_stats()
        })
        return stats
    
    def reset_stats(self):
        """統計リセット"""
        self._call_stats = {
            'successful_calls': 0,
            'failed_calls': 0,
            'avg_response_time': 0.0,
            'max_response_time': 0.0,
            'calls_by_layer': {},
            'calls_by_service': {}
        }
        self._protocol.reset_stats()
    
    def shutdown(self):
        """リソース解放"""
        try:
            # 登録解除
            self._queue_manager.unregister_agent(self.agent_name)
            
            # サービス全解除
            agent_info = self._api_registry.get_agent_info(self.agent_name)
            if agent_info:
                for service_name in list(agent_info.services):
                    self.unregister_service(service_name)
            
            self._logger.info(f"LayerInterface shutdown for agent: {self.agent_name}")
            
        except Exception as e:
            self._logger.error(f"Shutdown error: {e}")
    
    def _update_call_stats(self, layer_name: str, service_name: str, 
                          execution_time: float, success: bool):
        """呼び出し統計更新"""
        if success:
            self._call_stats['successful_calls'] += 1
            
            # 平均応答時間更新
            total_calls = self._call_stats['successful_calls']
            if total_calls == 1:
                self._call_stats['avg_response_time'] = execution_time
            else:
                current_avg = self._call_stats['avg_response_time']
                self._call_stats['avg_response_time'] = (
                    current_avg * (total_calls - 1) + execution_time) / total_calls
            
            # 最大応答時間更新
            self._call_stats['max_response_time'] = max(
                self._call_stats['max_response_time'], execution_time)
        else:
            self._call_stats['failed_calls'] += 1
        
        # レイヤー別統計
        if layer_name not in self._call_stats['calls_by_layer']:
            self._call_stats['calls_by_layer'][layer_name] = {'success': 0, 'failure': 0}
        
        if success:
            self._call_stats['calls_by_layer'][layer_name]['success'] += 1
        else:
            self._call_stats['calls_by_layer'][layer_name]['failure'] += 1
        
        # サービス別統計
        service_key = f"{layer_name}.{service_name}"
        if service_key not in self._call_stats['calls_by_service']:
            self._call_stats['calls_by_service'][service_key] = {'success': 0, 'failure': 0}
        
        if success:
            self._call_stats['calls_by_service'][service_key]['success'] += 1
        else:
            self._call_stats['calls_by_service'][service_key]['failure'] += 1
    
    def _update_async_stats(self, layer_name: str, service_name: str):
        """非同期呼び出し統計更新"""
        # TODO: 非同期統計実装
        pass


# 特化したインターフェース

class CacheLayerInterface:
    """Cache Layer専用インターフェース（フレーム切り替え50ms以下）"""
    
    def __init__(self, layer_interface: LayerInterface):
        self._interface = layer_interface
        self._cache_agent = "cache_layer"
    
    def get_frame(self, frame_id: str, timeout: int = 50) -> Any:
        """フレーム取得（50ms以下保証）"""
        return self._interface.call_service(
            self._cache_agent, "get_frame", timeout=timeout, frame_id=frame_id)
    
    def preload_frames(self, frame_ids: List[str]) -> bool:
        """フレーム先読み"""
        return self._interface.call_service_async(
            self._cache_agent, "preload_frames", frame_ids=frame_ids)


class PresentationLayerInterface:
    """Presentation Layer専用インターフェース"""
    
    def __init__(self, layer_interface: LayerInterface):
        self._interface = layer_interface
        self._presentation_agent = "presentation"
    
    def update_bb_display(self, bb_list: List[dict]) -> bool:
        """BB表示更新"""
        return self._interface.call_service_async(
            self._presentation_agent, "update_bb_display", bb_list=bb_list)
    
    def refresh_canvas(self) -> bool:
        """キャンバス再描画"""
        return self._interface.call_service_async(
            self._presentation_agent, "refresh_canvas")


def create_layer_interface(agent_name: str) -> LayerInterface:
    """LayerInterface作成ヘルパー"""
    return LayerInterface(agent_name)