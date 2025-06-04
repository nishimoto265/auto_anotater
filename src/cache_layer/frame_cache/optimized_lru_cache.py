"""
Agent6 Cache Layer: 超高性能LRUキャッシュ実装

フレーム切り替え50ms以下絶対達成のためのゼロコピー・メモリプール最適化
"""
import time
import threading
import mmap
import ctypes
import numpy as np
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass


@dataclass
class HighPerformanceCacheNode:
    """高性能キャッシュノード - メモリプール使用"""
    key: str
    data_ptr: int  # メモリプールポインタ
    size: int
    shape: tuple
    dtype: np.dtype
    prev: Optional['HighPerformanceCacheNode'] = None
    next: Optional['HighPerformanceCacheNode'] = None
    access_time: float = 0.0


class MemoryPool:
    """高速メモリプール - 事前割り当てによる高速化"""
    
    def __init__(self, pool_size_gb: int = 20):
        """
        Args:
            pool_size_gb: プールサイズ（GB）
        """
        self.pool_size = pool_size_gb * 1024**3
        self.block_size = 50 * 1024 * 1024  # 50MB per block
        self.max_blocks = self.pool_size // self.block_size
        
        # 事前割り当てメモリ
        self._memory_pool = bytearray(self.pool_size)
        self._available_blocks = list(range(self.max_blocks))
        self._used_blocks: Dict[int, int] = {}  # ptr -> block_id
        self._lock = threading.Lock()
    
    def allocate(self, size: int) -> Optional[int]:
        """メモリ割り当て（マイクロ秒オーダー）"""
        blocks_needed = (size + self.block_size - 1) // self.block_size
        
        with self._lock:
            if len(self._available_blocks) < blocks_needed:
                return None
            
            # 連続ブロック取得
            allocated_blocks = self._available_blocks[:blocks_needed]
            self._available_blocks = self._available_blocks[blocks_needed:]
            
            start_block = allocated_blocks[0]
            memory_ptr = id(self._memory_pool) + start_block * self.block_size
            
            for block in allocated_blocks:
                self._used_blocks[memory_ptr] = block
            
            return memory_ptr
    
    def deallocate(self, memory_ptr: int):
        """メモリ解放（マイクロ秒オーダー）"""
        with self._lock:
            if memory_ptr in self._used_blocks:
                block_id = self._used_blocks.pop(memory_ptr)
                self._available_blocks.append(block_id)
                self._available_blocks.sort()
    
    def get_memory_view(self, memory_ptr: int, size: int, shape: tuple, dtype: np.dtype) -> np.ndarray:
        """ゼロコピーメモリビュー取得"""
        buffer_offset = memory_ptr - id(self._memory_pool)
        buffer = memoryview(self._memory_pool)[buffer_offset:buffer_offset + size]
        return np.frombuffer(buffer, dtype=dtype).reshape(shape)


class OptimizedLRUFrameCache:
    """
    超高性能LRUフレームキャッシュ
    
    最適化技術:
    - ゼロコピー操作
    - 事前割り当てメモリプール
    - インライン関数
    - キャッシュライン最適化
    """
    
    def __init__(self, max_size: int = 100, memory_limit: int = 20 * 1024**3):
        """
        Args:
            max_size: 最大フレーム数
            memory_limit: メモリ上限（バイト）
        """
        self.max_size = max_size
        self.memory_limit = memory_limit
        
        # メモリプール初期化
        self._memory_pool = MemoryPool(memory_limit // (1024**3))
        
        # HashMap for O(1) access
        self._cache: Dict[str, HighPerformanceCacheNode] = {}
        
        # DoubleLinkedList for O(1) eviction
        self._head = HighPerformanceCacheNode("", 0, 0, (), np.uint8)
        self._tail = HighPerformanceCacheNode("", 0, 0, (), np.uint8)
        self._head.next = self._tail
        self._tail.prev = self._head
        
        # Statistics
        self._current_memory_usage = 0
        self._hits = 0
        self._misses = 0
        self._lock = threading.RLock()
        
        # Performance monitoring
        self._operation_times = []
    
    def get(self, frame_id: str) -> Optional[np.ndarray]:
        """
        超高速フレーム取得（1ms以下目標）
        """
        start_time = time.perf_counter()
        
        with self._lock:
            node = self._cache.get(frame_id)
            
            if node is None:
                self._misses += 1
                operation_time = (time.perf_counter() - start_time) * 1000
                self._record_operation_time(operation_time, "get_miss")
                return None
            
            # Move to head (most recently used) - インライン最適化
            self._move_to_head_inline(node)
            node.access_time = time.time()
            
            self._hits += 1
            
            # ゼロコピーメモリビュー取得
            frame_data = self._memory_pool.get_memory_view(
                node.data_ptr, node.size, node.shape, node.dtype
            )
            
            operation_time = (time.perf_counter() - start_time) * 1000
            self._record_operation_time(operation_time, "get_hit")
            
            return frame_data
    
    def put(self, frame_id: str, frame_data: np.ndarray) -> bool:
        """
        超高速フレーム格納（2ms以下目標）
        """
        start_time = time.perf_counter()
        
        if not isinstance(frame_data, np.ndarray):
            return False
        
        frame_size = frame_data.nbytes
        frame_shape = frame_data.shape
        frame_dtype = frame_data.dtype
        
        with self._lock:
            # Check if key already exists
            existing_node = self._cache.get(frame_id)
            if existing_node is not None:
                # Update existing node - ゼロコピー更新
                if existing_node.size == frame_size:
                    # Same size - direct memory update
                    memory_view = self._memory_pool.get_memory_view(
                        existing_node.data_ptr, frame_size, frame_shape, frame_dtype
                    )
                    memory_view[:] = frame_data
                    existing_node.access_time = time.time()
                    self._move_to_head_inline(existing_node)
                    
                    operation_time = (time.perf_counter() - start_time) * 1000
                    self._record_operation_time(operation_time, "put_update_same_size")
                    return True
                else:
                    # Different size - reallocate
                    self._memory_pool.deallocate(existing_node.data_ptr)
                    self._current_memory_usage -= existing_node.size
            
            # メモリプールから高速割り当て
            memory_ptr = self._memory_pool.allocate(frame_size)
            if memory_ptr is None:
                # メモリ不足 - 緊急削除
                self._emergency_eviction(frame_size)
                memory_ptr = self._memory_pool.allocate(frame_size)
                if memory_ptr is None:
                    return False
            
            # ゼロコピーでデータ転送
            memory_view = self._memory_pool.get_memory_view(
                memory_ptr, frame_size, frame_shape, frame_dtype
            )
            memory_view[:] = frame_data
            
            # Create new node
            if existing_node is not None:
                # Update existing
                existing_node.data_ptr = memory_ptr
                existing_node.size = frame_size
                existing_node.shape = frame_shape
                existing_node.dtype = frame_dtype
                existing_node.access_time = time.time()
                self._move_to_head_inline(existing_node)
            else:
                # Create new
                new_node = HighPerformanceCacheNode(
                    key=frame_id,
                    data_ptr=memory_ptr,
                    size=frame_size,
                    shape=frame_shape,
                    dtype=frame_dtype,
                    access_time=time.time()
                )
                
                # Check size limit
                if len(self._cache) >= self.max_size:
                    self._evict_lru_inline()
                
                # Add to cache
                self._cache[frame_id] = new_node
                self._add_to_head_inline(new_node)
            
            self._current_memory_usage += frame_size
            
            operation_time = (time.perf_counter() - start_time) * 1000
            self._record_operation_time(operation_time, "put_new")
            
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
            # すべてのメモリ解放
            for node in self._cache.values():
                self._memory_pool.deallocate(node.data_ptr)
            
            self._cache.clear()
            self._head.next = self._tail
            self._tail.prev = self._head
            self._current_memory_usage = 0
            self._hits = 0
            self._misses = 0
    
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
    
    # インライン最適化された内部メソッド
    
    def _move_to_head_inline(self, node: HighPerformanceCacheNode):
        """ノードをヘッドに移動（インライン最適化）"""
        # Remove from current position
        node.prev.next = node.next
        node.next.prev = node.prev
        
        # Add to head
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node
    
    def _add_to_head_inline(self, node: HighPerformanceCacheNode):
        """ヘッドにノード追加（インライン最適化）"""
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node
    
    def _evict_lru_inline(self):
        """LRU削除（インライン最適化）"""
        lru_node = self._tail.prev
        if lru_node != self._head:
            # Remove from list
            lru_node.prev.next = lru_node.next
            lru_node.next.prev = lru_node.prev
            
            # Remove from cache and deallocate memory
            del self._cache[lru_node.key]
            self._memory_pool.deallocate(lru_node.data_ptr)
            self._current_memory_usage -= lru_node.size
    
    def _emergency_eviction(self, required_size: int):
        """緊急削除（必要サイズ確保まで）"""
        while (self._current_memory_usage + required_size > self.memory_limit and 
               len(self._cache) > 0):
            self._evict_lru_inline()
    
    def _record_operation_time(self, operation_time: float, operation_type: str):
        """操作時間記録"""
        self._operation_times.append(operation_time)
        
        # Keep only recent 100 operations for memory efficiency
        if len(self._operation_times) > 100:
            self._operation_times = self._operation_times[-100:]
        
        # Critical performance alert
        if operation_time > 5.0:
            print(f"PERFORMANCE ALERT: {operation_type} took {operation_time:.3f}ms")


# Alias for backward compatibility
LRUFrameCache = OptimizedLRUFrameCache
CacheNode = HighPerformanceCacheNode