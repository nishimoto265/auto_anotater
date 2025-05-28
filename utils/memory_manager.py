import psutil
import gc
import weakref
from collections import OrderedDict
from typing import Any, Dict, Optional
import threading
import time

class MemoryManager:
    def __init__(self, max_cache_size_gb: float = 20.0, max_memory_gb: float = 64.0):
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  
        self.max_memory = max_memory_gb * 1024 * 1024 * 1024
        self.cache = OrderedDict()
        self.memory_pool = {}
        self.weak_refs = weakref.WeakKeyDictionary()
        self.lock = threading.Lock()
        self.monitoring_thread = None
        self.stop_monitoring = False

    def start_monitoring(self):
        self.monitoring_thread = threading.Thread(target=self._monitor_memory)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def stop(self):
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join()

    def _monitor_memory(self):
        while not self.stop_monitoring:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            if memory_info.rss > self.max_memory * 0.9:
                self._trigger_gc()
                self._clear_cache(target_size=self.max_cache_size * 0.7)
            
            time.sleep(1)

    def _trigger_gc(self):
        gc.collect()

    def _clear_cache(self, target_size: float):
        with self.lock:
            current_size = sum(len(v) for v in self.cache.values())
            while current_size > target_size and self.cache:
                self.cache.popitem(last=False)
                current_size = sum(len(v) for v in self.cache.values())

    def cache_put(self, key: str, value: Any) -> None:
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            self.cache[key] = value
            self._clear_cache(self.max_cache_size)

    def cache_get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None

    def allocate_from_pool(self, size: int, pool_key: str) -> bytearray:
        with self.lock:
            if pool_key not in self.memory_pool:
                self.memory_pool[pool_key] = []
            
            for i, buffer in enumerate(self.memory_pool[pool_key]):
                if len(buffer) >= size:
                    return self.memory_pool[pool_key].pop(i)
            
            return bytearray(size)

    def return_to_pool(self, buffer: bytearray, pool_key: str):
        with self.lock:
            if pool_key not in self.memory_pool:
                self.memory_pool[pool_key] = []
            self.memory_pool[pool_key].append(buffer)

    def get_memory_stats(self) -> Dict[str, float]:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'total_used': memory_info.rss / (1024 * 1024 * 1024),
            'cache_size': sum(len(v) for v in self.cache.values()) / (1024 * 1024 * 1024),
            'pool_size': sum(sum(len(b) for b in buffers) 
                           for buffers in self.memory_pool.values()) / (1024 * 1024 * 1024)
        }

    def __del__(self):
        self.stop()