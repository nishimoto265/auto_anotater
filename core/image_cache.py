import threading
from collections import OrderedDict
from typing import Optional, Tuple, List, Dict
import cv2
import numpy as np
from PIL import Image
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor, Future
import time
import queue

class ImageCache:
    """
    高速画像キャッシュシステム
    前後100フレームの先読みキャッシュ、表示用画像の1/2リサイズ処理、
    フルサイズ画像のオンデマンド読み込み、LRUキャッシュによる20GB上限管理、マルチスレッド対応
    """
    
    def __init__(self, max_cache_size_gb: float = 20.0, preload_frames: int = 100, num_threads: int = 8):
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.preload_frames = preload_frames
        self.cache = OrderedDict()
        self.current_size = 0
        self.lock = threading.RLock()
        
        # Thread pool for async loading
        self.num_threads = num_threads
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
        
        # Preload queue and futures tracking
        self.preload_queue = queue.PriorityQueue()
        self.loading_futures: Dict[int, Future] = {}
        self.is_preloading = False
        
        # Performance tracking
        self.hit_count = 0
        self.miss_count = 0
        self.load_times: List[float] = []
        
        # Frame paths storage
        self.frame_paths: List[str] = []
        
    def set_frame_paths(self, frame_paths: List[str]) -> None:
        """フレームパスを設定"""
        self.frame_paths = frame_paths
        
    def get_memory_usage(self) -> float:
        """現在のメモリ使用量を取得（GB単位）"""
        return self.current_size / (1024 * 1024 * 1024)
        
    def get_image(self, frame_id: int, image_path: Optional[str] = None) -> Optional[np.ndarray]:
        """画像を取得（キャッシュから、または読み込み）"""
        start_time = time.time()
        
        # Check cache first with minimal locking
        with self.lock:
            if frame_id in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(frame_id)
                self.hit_count += 1
                return self.cache[frame_id]
        
        # Cache miss
        self.miss_count += 1
        
        # Check if already loading
        if frame_id in self.loading_futures and not self.loading_futures[frame_id].done():
            # Wait for the existing loading task
            future = self.loading_futures[frame_id]
            try:
                image = future.result(timeout=0.5)  # 500ms timeout
                load_time = time.time() - start_time
                self.load_times.append(load_time)
                return image
            except:
                pass
        
        # Load image synchronously if not already loading
        if image_path is None and frame_id < len(self.frame_paths):
            image_path = self.frame_paths[frame_id]
            
        if image_path:
            image = self._load_image(image_path)
            if image is not None:
                self._add_to_cache(frame_id, image)
            
            load_time = time.time() - start_time
            self.load_times.append(load_time)
            return image
        
        return None
            
    def _load_image(self, image_path: str) -> Optional[np.ndarray]:
        """画像ファイルを読み込み"""
        try:
            # Load with OpenCV for speed
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            
            # Optional: Resize for display (1/2 size for faster rendering)
            # This can be toggled based on requirements
            # display_image = cv2.resize(image, (image.shape[1]//2, image.shape[0]//2))
            
            return image
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
            
    def _add_to_cache(self, frame_id: int, image: np.ndarray):
        """キャッシュに画像を追加"""
        with self.lock:
            image_size = image.nbytes
            
            # Remove old items if necessary (LRU eviction)
            while self.current_size + image_size > self.max_cache_size and self.cache:
                oldest_id, oldest_image = self.cache.popitem(last=False)
                self.current_size -= oldest_image.nbytes
                
                # Cancel any pending load for evicted frame
                if oldest_id in self.loading_futures:
                    self.loading_futures[oldest_id].cancel()
                    del self.loading_futures[oldest_id]
                    
            self.cache[frame_id] = image
            self.current_size += image_size
        
    def preload_range(self, center_frame: int, priority_radius: int = 10) -> None:
        """前後のフレームを優先度付きで先読み"""
        if not self.frame_paths:
            return
            
        # Clear old preload queue
        while not self.preload_queue.empty():
            try:
                self.preload_queue.get_nowait()
            except:
                break
                
        # Add frames to preload queue with priority
        # Closer frames have higher priority (lower number)
        for distance in range(self.preload_frames + 1):
            for direction in [1, -1]:
                if distance == 0 and direction == -1:
                    continue
                    
                frame_id = center_frame + (distance * direction)
                
                if 0 <= frame_id < len(self.frame_paths):
                    with self.lock:
                        # Skip if already cached or loading
                        if frame_id in self.cache:
                            continue
                        if frame_id in self.loading_futures and not self.loading_futures[frame_id].done():
                            continue
                            
                    # Priority based on distance (closer = higher priority = lower number)
                    priority = abs(distance) if distance <= priority_radius else priority_radius + 1
                    self.preload_queue.put((priority, frame_id))
                    
        # Start preloading if not already running
        if not self.is_preloading:
            self.is_preloading = True
            self.executor.submit(self._preload_worker)
                
    def _preload_worker(self) -> None:
        """先読みワーカースレッド"""
        while not self.preload_queue.empty():
            try:
                priority, frame_id = self.preload_queue.get(timeout=0.1)
                
                # Skip if already cached
                with self.lock:
                    if frame_id in self.cache:
                        continue
                        
                # Submit loading task
                if frame_id < len(self.frame_paths):
                    future = self.executor.submit(
                        self._load_and_cache_frame,
                        frame_id,
                        self.frame_paths[frame_id]
                    )
                    
                    with self.lock:
                        self.loading_futures[frame_id] = future
                        
            except queue.Empty:
                break
            except Exception as e:
                print(f"Preload worker error: {e}")
                
        self.is_preloading = False
        
    def _load_and_cache_frame(self, frame_id: int, frame_path: str) -> Optional[np.ndarray]:
        """フレームを読み込んでキャッシュに追加"""
        try:
            image = self._load_image(frame_path)
            if image is not None:
                self._add_to_cache(frame_id, image)
                
            # Clean up future reference
            with self.lock:
                if frame_id in self.loading_futures:
                    del self.loading_futures[frame_id]
                    
            return image
        except Exception as e:
            print(f"Error loading frame {frame_id}: {e}")
            return None
                    
    def is_loaded(self, frame_id: int) -> bool:
        """フレームがキャッシュに存在するか確認"""
        with self.lock:
            return frame_id in self.cache
            
    def clear(self):
        """キャッシュをクリア"""
        with self.lock:
            # Cancel all pending loads
            for future in self.loading_futures.values():
                future.cancel()
            self.loading_futures.clear()
            
            # Clear cache
            self.cache.clear()
            self.current_size = 0
            
            # Clear stats
            self.hit_count = 0
            self.miss_count = 0
            self.load_times.clear()
            
            gc.collect()
            
    def get_cache_stats(self) -> dict:
        """キャッシュ統計を取得"""
        total_requests = self.hit_count + self.miss_count
        hit_ratio = self.hit_count / total_requests if total_requests > 0 else 0.0
        
        avg_load_time = sum(self.load_times) / len(self.load_times) if self.load_times else 0.0
        
        with self.lock:
            pending_loads = len([f for f in self.loading_futures.values() if not f.done()])
            
        return {
            "cached_frames": len(self.cache),
            "memory_usage_gb": self.get_memory_usage(),
            "max_size_gb": self.max_cache_size / (1024 * 1024 * 1024),
            "cache_hit_ratio": hit_ratio,
            "total_requests": total_requests,
            "hits": self.hit_count,
            "misses": self.miss_count,
            "avg_load_time_ms": avg_load_time * 1000,
            "pending_loads": pending_loads
        }
        
    def shutdown(self) -> None:
        """スレッドプールをシャットダウン"""
        self.executor.shutdown(wait=True)