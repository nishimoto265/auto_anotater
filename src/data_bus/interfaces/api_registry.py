"""
ApiRegistry - API登録・発見サービス
Agent間のサービス発見と動的登録管理
"""
import threading
import time
from typing import Dict, List, Optional, Callable, Set, Any
from dataclasses import dataclass, field
import logging


@dataclass
class ServiceDefinition:
    """サービス定義"""
    agent_name: str
    service_name: str
    handler: Callable
    timeout: int = 1000  # ms
    description: str = ""
    version: str = "1.0"
    registered_at: float = field(default_factory=time.perf_counter)
    last_accessed: float = field(default_factory=time.perf_counter)
    access_count: int = 0
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'agent_name': self.agent_name,
            'service_name': self.service_name,
            'timeout': self.timeout,
            'description': self.description,
            'version': self.version,
            'registered_at': self.registered_at,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count
        }


@dataclass
class AgentInfo:
    """Agent情報"""
    name: str
    services: Set[str] = field(default_factory=set)
    registered_at: float = field(default_factory=time.perf_counter)
    last_heartbeat: float = field(default_factory=time.perf_counter)
    status: str = "active"  # active, inactive, error
    metadata: Dict[str, Any] = field(default_factory=dict)


class ApiRegistry:
    """
    API登録・発見サービス
    Agent間のサービス発見と動的登録を管理
    """
    
    def __init__(self, heartbeat_interval: int = 30):
        # サービス登録（agent_name.service_name -> ServiceDefinition）
        self._services: Dict[str, ServiceDefinition] = {}
        
        # Agent登録（agent_name -> AgentInfo）
        self._agents: Dict[str, AgentInfo] = {}
        
        # サービス統計
        self._stats = {
            'total_services': 0,
            'total_agents': 0,
            'total_lookups': 0,
            'successful_lookups': 0,
            'failed_lookups': 0
        }
        
        # 設定
        self._heartbeat_interval = heartbeat_interval
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # ヘルスチェック開始
        self._start_health_monitor()
    
    def register_service(self, agent_name: str, service_name: str, 
                        handler: Callable, timeout: int = 1000,
                        description: str = "", version: str = "1.0") -> bool:
        """
        サービス登録
        
        Args:
            agent_name: Agent名
            service_name: サービス名
            handler: ハンドラー関数
            timeout: タイムアウト（ms）
            description: サービス説明
            version: バージョン
            
        Returns:
            bool: 登録成功フラグ
        """
        try:
            service_key = f"{agent_name}.{service_name}"
            
            service_def = ServiceDefinition(
                agent_name=agent_name,
                service_name=service_name,
                handler=handler,
                timeout=timeout,
                description=description,
                version=version
            )
            
            with self._lock:
                # サービス登録
                self._services[service_key] = service_def
                
                # Agent情報更新
                if agent_name not in self._agents:
                    self._agents[agent_name] = AgentInfo(name=agent_name)
                
                self._agents[agent_name].services.add(service_name)
                self._agents[agent_name].last_heartbeat = time.perf_counter()
                
                # 統計更新
                self._stats['total_services'] = len(self._services)
                self._stats['total_agents'] = len(self._agents)
            
            self._logger.info(f"Registered service: {service_key}")
            return True
            
        except Exception as e:
            self._logger.error(f"Service registration failed: {e}")
            return False
    
    def unregister_service(self, agent_name: str, service_name: str) -> bool:
        """
        サービス登録解除
        
        Args:
            agent_name: Agent名
            service_name: サービス名
            
        Returns:
            bool: 解除成功フラグ
        """
        try:
            service_key = f"{agent_name}.{service_name}"
            
            with self._lock:
                # サービス削除
                if service_key in self._services:
                    del self._services[service_key]
                
                # Agent情報更新
                if agent_name in self._agents:
                    self._agents[agent_name].services.discard(service_name)
                    
                    # サービスが全て削除された場合はAgent削除
                    if not self._agents[agent_name].services:
                        del self._agents[agent_name]
                
                # 統計更新
                self._stats['total_services'] = len(self._services)
                self._stats['total_agents'] = len(self._agents)
            
            self._logger.info(f"Unregistered service: {service_key}")
            return True
            
        except Exception as e:
            self._logger.error(f"Service unregistration failed: {e}")
            return False
    
    def lookup_service(self, agent_name: str, service_name: str) -> Optional[ServiceDefinition]:
        """
        サービス検索
        
        Args:
            agent_name: Agent名
            service_name: サービス名
            
        Returns:
            ServiceDefinition: サービス定義（見つからない場合はNone）
        """
        service_key = f"{agent_name}.{service_name}"
        
        with self._lock:
            self._stats['total_lookups'] += 1
            
            if service_key in self._services:
                service_def = self._services[service_key]
                
                # アクセス統計更新
                service_def.last_accessed = time.perf_counter()
                service_def.access_count += 1
                
                self._stats['successful_lookups'] += 1
                return service_def
            else:
                self._stats['failed_lookups'] += 1
                return None
    
    def find_services_by_agent(self, agent_name: str) -> List[ServiceDefinition]:
        """Agent別サービス一覧取得"""
        services = []
        
        with self._lock:
            for service_key, service_def in self._services.items():
                if service_def.agent_name == agent_name:
                    services.append(service_def)
        
        return services
    
    def find_services_by_name(self, service_name: str) -> List[ServiceDefinition]:
        """サービス名別Agent一覧取得"""
        services = []
        
        with self._lock:
            for service_key, service_def in self._services.items():
                if service_def.service_name == service_name:
                    services.append(service_def)
        
        return services
    
    def get_all_services(self) -> Dict[str, dict]:
        """全サービス一覧取得"""
        with self._lock:
            return {key: service.to_dict() for key, service in self._services.items()}
    
    def get_agent_info(self, agent_name: str) -> Optional[AgentInfo]:
        """Agent情報取得"""
        with self._lock:
            return self._agents.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, AgentInfo]:
        """全Agent一覧取得"""
        with self._lock:
            return self._agents.copy()
    
    def update_agent_status(self, agent_name: str, status: str, 
                           metadata: Dict[str, Any] = None):
        """Agent状態更新"""
        with self._lock:
            if agent_name in self._agents:
                self._agents[agent_name].status = status
                self._agents[agent_name].last_heartbeat = time.perf_counter()
                if metadata:
                    self._agents[agent_name].metadata.update(metadata)
    
    def heartbeat(self, agent_name: str, metadata: Dict[str, Any] = None) -> bool:
        """Agent生存確認"""
        try:
            with self._lock:
                if agent_name in self._agents:
                    self._agents[agent_name].last_heartbeat = time.perf_counter()
                    self._agents[agent_name].status = "active"
                    if metadata:
                        self._agents[agent_name].metadata.update(metadata)
                    return True
            return False
            
        except Exception as e:
            self._logger.error(f"Heartbeat failed for {agent_name}: {e}")
            return False
    
    def get_available_agents(self) -> Set[str]:
        """利用可能Agent一覧取得"""
        current_time = time.perf_counter()
        available = set()
        
        with self._lock:
            for agent_name, agent_info in self._agents.items():
                if (current_time - agent_info.last_heartbeat < self._heartbeat_interval * 2 
                    and agent_info.status == "active"):
                    available.add(agent_name)
        
        return available
    
    def get_service_stats(self) -> dict:
        """サービス統計取得"""
        with self._lock:
            return self._stats.copy()
    
    def get_service_health(self) -> Dict[str, dict]:
        """サービス健全性取得"""
        current_time = time.perf_counter()
        health = {}
        
        with self._lock:
            for service_key, service_def in self._services.items():
                agent_info = self._agents.get(service_def.agent_name)
                
                if agent_info:
                    last_heartbeat = current_time - agent_info.last_heartbeat
                    is_healthy = (last_heartbeat < self._heartbeat_interval * 2 
                                and agent_info.status == "active")
                else:
                    last_heartbeat = float('inf')
                    is_healthy = False
                
                health[service_key] = {
                    'healthy': is_healthy,
                    'last_heartbeat': last_heartbeat,
                    'access_count': service_def.access_count,
                    'last_accessed': current_time - service_def.last_accessed,
                    'agent_status': agent_info.status if agent_info else "unknown"
                }
        
        return health
    
    def cleanup_inactive_agents(self, timeout: int = None) -> int:
        """非アクティブAgent削除"""
        if timeout is None:
            timeout = self._heartbeat_interval * 3
        
        current_time = time.perf_counter()
        removed_count = 0
        
        with self._lock:
            # 非アクティブAgent検出
            inactive_agents = []
            for agent_name, agent_info in self._agents.items():
                if current_time - agent_info.last_heartbeat > timeout:
                    inactive_agents.append(agent_name)
            
            # Agent削除
            for agent_name in inactive_agents:
                # 関連サービス削除
                services_to_remove = []
                for service_key, service_def in self._services.items():
                    if service_def.agent_name == agent_name:
                        services_to_remove.append(service_key)
                
                for service_key in services_to_remove:
                    del self._services[service_key]
                
                # Agent削除
                del self._agents[agent_name]
                removed_count += 1
                
                self._logger.info(f"Removed inactive agent: {agent_name}")
            
            # 統計更新
            self._stats['total_services'] = len(self._services)
            self._stats['total_agents'] = len(self._agents)
        
        return removed_count
    
    def _start_health_monitor(self):
        """ヘルスモニター開始"""
        def monitor_loop():
            while True:
                try:
                    self.cleanup_inactive_agents()
                    time.sleep(self._heartbeat_interval)
                except Exception as e:
                    self._logger.error(f"Health monitor error: {e}")
                    time.sleep(5)
        
        import threading
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()


# グローバルApiRegistryインスタンス
_global_api_registry: Optional[ApiRegistry] = None


def get_global_api_registry() -> ApiRegistry:
    """グローバルApiRegistry取得"""
    global _global_api_registry
    if _global_api_registry is None:
        _global_api_registry = ApiRegistry()
    return _global_api_registry