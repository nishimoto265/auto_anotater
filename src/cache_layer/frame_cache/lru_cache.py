"""
Agent6 Cache Layer: 高性能LRUキャッシュ実装

フレーム切り替え50ms以下絶対達成のためのHashMap + DoubleLinkedList実装
O(1)時間複雑度保証・5ms以下操作時間
"""
import time
import threading
import psutil
import numpy as np
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass


@dataclass
class CacheNode:
    """LRU双方向リンクリストノード"""
    key: str
    data: np.ndarray
    size: int
    prev: Optional['CacheNode'] = None
    next: Optional['CacheNode'] = None
    access_time: float = 0.0


class LRUFrameCache:
    """
    高性能LRUフレームキャッシュ
    
    性能要件:
    - get(): 5ms以下
    - put(): 5ms以下  
    - キャッシュヒット率: 95%以上
    - メモリ上限: 20GB
    """
    
    def __init__(self, max_size: int = 100, memory_limit: int = 20 * 1024**3):
        """
        Args:
            max_size: 最大フレーム数（前後100フレーム推奨）
            memory_limit: メモリ上限（バイト）
        """
        self.max_size = max_size
        self.memory_limit = memory_limit
        
        # HashMap for O(1) access
        self._cache: Dict[str, CacheNode] = {}
        
        # DoubleLinkedList for O(1) eviction
        self._head = CacheNode("", np.array([]), 0)
        self._tail = CacheNode("", np.array([]), 0)
        self._head.next = self._tail
        self._tail.prev = self._head
        
        # Statistics and monitoring
        self._current_memory_usage = 0
        self._hits = 0
        self._misses = 0
        self._lock = threading.RLock()  # Thread-safe operations
        
        # Memory warning callback
        self._memory_warning_callback: Optional[Callable[[float], None]] = None
        
        # Performance monitoring
        self._operation_times = []
        self._last_cleanup_time = time.time()
    
    def get(self, frame_id: str) -> Optional[np.ndarray]:
        """
        フレーム取得（5ms以下必達）
        
        Args:
            frame_id: フレームID
            
        Returns:
            フレーム画像データ、None if miss
        """
        start_time = time.perf_counter()
        
        with self._lock:
            node = self._cache.get(frame_id)
            
            if node is None:
                self._misses += 1
                operation_time = (time.perf_counter() - start_time) * 1000
                self._record_operation_time(operation_time, "get_miss")
                return None
            
            # Move to head (most recently used)
            self._move_to_head(node)
            node.access_time = time.time()
            
            self._hits += 1
            
            operation_time = (time.perf_counter() - start_time) * 1000
            self._record_operation_time(operation_time, "get_hit")
            
            # Performance assertion for development
            if operation_time > 5.0:
                print(f"WARNING: get() operation exceeded 5ms: {operation_time:.3f}ms")
            
            # 최적화: view 반환으로 복사 시간 제거 (읽기 전용)
            return node.data
    
    def put(self, frame_id: str, frame_data: np.ndarray) -> bool:
        """
        フレーム格納（5ms以下必達）
        
        Args:
            frame_id: フレームID
            frame_data: フレーム画像データ
            
        Returns:
            格納成功フラグ
        """
        start_time = time.perf_counter()
        
        if not isinstance(frame_data, np.ndarray):
            return False
        
        frame_size = frame_data.nbytes
        
        with self._lock:
            # Check if key already exists
            existing_node = self._cache.get(frame_id)
            if existing_node is not None:
                # Update existing node (최적화: 직접 참조)
                old_size = existing_node.size
                existing_node.data = frame_data
                existing_node.size = frame_size
                existing_node.access_time = time.time()
                
                self._current_memory_usage += frame_size - old_size
                self._move_to_head(existing_node)
                
                operation_time = (time.perf_counter() - start_time) * 1000
                self._record_operation_time(operation_time, "put_update")
                return True
            
            # Create new node (최적화: 직접 참조로 복사 시간 제거)
            new_node = CacheNode(
                key=frame_id,
                data=frame_data,
                size=frame_size,
                access_time=time.time()
            )
            
            # Check memory limit before adding
            if self._current_memory_usage + frame_size > self.memory_limit:
                self._evict_until_memory_available(frame_size)
            
            # Check size limit
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # Add to cache
            self._cache[frame_id] = new_node
            self._add_to_head(new_node)
            self._current_memory_usage += frame_size
            
            # Memory warning check
            self._check_memory_warning()
            
            operation_time = (time.perf_counter() - start_time) * 1000
            self._record_operation_time(operation_time, "put_new")
            
            # Performance assertion for development
            if operation_time > 5.0:
                print(f"WARNING: put() operation exceeded 5ms: {operation_time:.3f}ms")
            
            return True
    
    def size(self) -> int:
        """キャッシュサイズ取得"""
        return len(self._cache)
    
    def get_memory_usage(self) -> int:
        """現在メモリ使用量取得（バイト）"""
        return self._current_memory_usage
    
    def get_hit_rate(self) -> float:
        """キャッシュヒット率取得"""
        total_accesses = self._hits + self._misses
        if total_accesses == 0:
            return 0.0
        return self._hits / total_accesses
    
    def clear(self):
        """キャッシュクリア"""
        with self._lock:
            self._cache.clear()
            self._head.next = self._tail
            self._tail.prev = self._head
            self._current_memory_usage = 0
            self._hits = 0
            self._misses = 0
    
    def set_memory_warning_callback(self, callback: Callable[[float], None]):
        """メモリ警告コールバック設定"""
        self._memory_warning_callback = callback
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """性能統計取得"""
        return {
            'hit_rate': self.get_hit_rate(),
            'memory_usage_gb': self._current_memory_usage / (1024**3),
            'memory_usage_percent': (self._current_memory_usage / self.memory_limit) * 100,
            'cache_size': len(self._cache),
            'avg_operation_time_ms': np.mean(self._operation_times) if self._operation_times else 0,
            'max_operation_time_ms': np.max(self._operation_times) if self._operation_times else 0,
            'total_hits': self._hits,
            'total_misses': self._misses
        }
    
    # Private methods for internal operations
    
    def _move_to_head(self, node: CacheNode):
        """ノードをヘッドに移動（最近使用済みにする）"""
        self._remove_node(node)
        self._add_to_head(node)
    
    def _add_to_head(self, node: CacheNode):
        """ヘッドにノード追加"""
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node
    
    def _remove_node(self, node: CacheNode):
        """ノードをリストから削除"""
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _evict_lru(self):
        """LRU（最長未使用）ノード削除"""
        lru_node = self._tail.prev
        if lru_node != self._head:
            self._remove_node(lru_node)
            del self._cache[lru_node.key]
            self._current_memory_usage -= lru_node.size
    
    def _evict_until_memory_available(self, required_size: int):
        """必要メモリ確保まで削除継続"""
        while (self._current_memory_usage + required_size > self.memory_limit and 
               len(self._cache) > 0):
            self._evict_lru()
    
    def _check_memory_warning(self):
        """メモリ警告チェック（18GB閾値）"""
        warning_threshold = 18 * 1024**3  # 18GB
        if (self._current_memory_usage >= warning_threshold and 
            self._memory_warning_callback is not None):
            usage_gb = self._current_memory_usage / (1024**3)
            self._memory_warning_callback(usage_gb)
    
    def _record_operation_time(self, operation_time: float, operation_type: str):
        """操作時間記録"""
        self._operation_times.append(operation_time)
        
        # Keep only recent 1000 operations
        if len(self._operation_times) > 1000:
            self._operation_times = self._operation_times[-1000:]
        
        # Debug output for slow operations
        if operation_time > 5.0:
            print(f"SLOW OPERATION: {operation_type} took {operation_time:.3f}ms")


# Mock infrastructure loader for testing
class MockInfrastructureLoader:
    """Infrastructure層モック（テスト用）"""
    
    @staticmethod
    def load_frame(frame_id: str) -> Optional[np.ndarray]:
        """フレーム読み込みシミュレーション"""
        import time
        time.sleep(0.03)  # 30ms読み込み時間シミュレーション
        return np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)


# Global instance for testing
infrastructure_loader = MockInfrastructureLoader()