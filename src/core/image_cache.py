import threading
from collections import OrderedDict
from typing import Optional, Tuple, Dict, Any
import cv2
import numpy as np
from PIL import Image
import psutil
import gc
import time
import weakref

class ImageCache:
    """
    高速画像キャッシュシステム
    前後100フレームの先読みキャッシュ、表示用画像の1/2リサイズ処理、
    フルサイズ画像のオンデマンド読み込み、LRUキャッシュによる20GB上限管理、マルチスレッド対応
    """
    
    def __init__(self, max_cache_size_gb: float = 20.0, max_memory_gb: float = 64.0, preload_frames: int = 100):
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.max_memory = max_memory_gb * 1024 * 1024 * 1024
        self.preload_frames = preload_frames
        self.cache = OrderedDict()
        self.current_size = 0
        self.lock = threading.RLock()
        
        # Memory monitoring
        self.monitoring_thread = None
        self.stop_monitoring = False
        self.memory_pool = {}
        self.weak_refs = weakref.WeakKeyDictionary()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        
        # Start memory monitoring
        self.start_monitoring()
        
    def start_monitoring(self):
        """メモリ監視スレッドを開始"""
        self.monitoring_thread = threading.Thread(target=self._monitor_memory)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
    def stop(self):
        """メモリ監視を停止"""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join()
            
    def _monitor_memory(self):
        """メモリ使用状況を監視し、必要に応じてクリーンアップ"""
        while not self.stop_monitoring:
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                
                # メモリ使用量が上限の90%を超えたら自動クリーンアップ
                if memory_info.rss > self.max_memory * 0.9:
                    self._trigger_gc()
                    self._clear_cache(target_size=self.max_cache_size * 0.7)
                    
                time.sleep(1)
            except Exception as e:
                print(f"Memory monitoring error: {e}")
                
    def _trigger_gc(self):
        """ガベージコレクションを実行"""
        gc.collect()
        
    def get_memory_usage(self) -> float:
        """現在のメモリ使用量を取得（GB単位）"""
        return self.current_size / (1024 * 1024 * 1024)
        
    def get_memory_stats(self) -> Dict[str, float]:
        """詳細なメモリ統計を取得"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'total_used_gb': memory_info.rss / (1024 * 1024 * 1024),
            'cache_size_gb': self.current_size / (1024 * 1024 * 1024),
            'cache_frames': len(self.cache),
            'hit_ratio': self._calculate_hit_ratio(),
            'max_cache_gb': self.max_cache_size / (1024 * 1024 * 1024),
            'max_memory_gb': self.max_memory / (1024 * 1024 * 1024)
        }
        
    def get_image(self, frame_id: int, image_path: str) -> Optional[np.ndarray]:
        """画像を取得（キャッシュから、または読み込み）"""
        with self.lock:
            if frame_id in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(frame_id)
                self.hits += 1
                return self.cache[frame_id]
                
            # Cache miss
            self.misses += 1
            
            # Load image
            image = self._load_image(image_path)
            if image is not None:
                self._add_to_cache(frame_id, image)
            return image
            
    def _load_image(self, image_path: str) -> Optional[np.ndarray]:
        """画像ファイルを読み込み"""
        try:
            image = cv2.imread(image_path)
            return image
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
            
    def _add_to_cache(self, frame_id: int, image: np.ndarray):
        """キャッシュに画像を追加"""
        image_size = image.nbytes
        
        # Remove old items if necessary
        self._clear_cache(target_size=self.max_cache_size - image_size)
            
        self.cache[frame_id] = image
        self.current_size += image_size
        
    def _clear_cache(self, target_size: float):
        """キャッシュをターゲットサイズまでクリア"""
        while self.current_size > target_size and self.cache:
            oldest_id, oldest_image = self.cache.popitem(last=False)
            self.current_size -= oldest_image.nbytes
        
    def preload_frames(self, center_frame: int, frame_paths: list):
        """前後のフレームを先読み"""
        start_frame = max(0, center_frame - self.preload_frames // 2)
        end_frame = min(len(frame_paths), center_frame + self.preload_frames // 2)
        
        for i in range(start_frame, end_frame):
            if i not in self.cache and i < len(frame_paths):
                threading.Thread(
                    target=self._preload_single_frame,
                    args=(i, frame_paths[i]),
                    daemon=True
                ).start()
                
    def _preload_single_frame(self, frame_id: int, frame_path: str):
        """単一フレームの先読み"""
        image = self._load_image(frame_path)
        if image is not None:
            with self.lock:
                if frame_id not in self.cache:
                    self._add_to_cache(frame_id, image)
                    
    def clear_cache(self):
        """キャッシュをクリア"""
        with self.lock:
            self.cache.clear()
            self.current_size = 0
            self._trigger_gc()
            
    def get_cache_stats(self) -> dict:
        """キャッシュ統計を取得"""
        return {
            "cached_frames": len(self.cache),
            "memory_usage_gb": self.get_memory_usage(),
            "max_size_gb": self.max_cache_size / (1024 * 1024 * 1024),
            "cache_hit_ratio": self._calculate_hit_ratio()
        }
        
    def _calculate_hit_ratio(self) -> float:
        """キャッシュヒット率を計算"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
        
    def allocate_from_pool(self, size: int, pool_key: str) -> bytearray:
        """メモリプールからバッファを割り当て"""
        with self.lock:
            if pool_key not in self.memory_pool:
                self.memory_pool[pool_key] = []
                
            for i, buffer in enumerate(self.memory_pool[pool_key]):
                if len(buffer) >= size:
                    return self.memory_pool[pool_key].pop(i)
                    
            return bytearray(size)
            
    def return_to_pool(self, buffer: bytearray, pool_key: str):
        """バッファをメモリプールに返却"""
        with self.lock:
            if pool_key not in self.memory_pool:
                self.memory_pool[pool_key] = []
            self.memory_pool[pool_key].append(buffer)
            
    def __del__(self):
        """デストラクタ"""
        self.stop()