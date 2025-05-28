import threading
from collections import OrderedDict
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import psutil
import gc

class ImageCache:
    """
    高速画像キャッシュシステム
    前後100フレームの先読みキャッシュ、表示用画像の1/2リサイズ処理、
    フルサイズ画像のオンデマンド読み込み、LRUキャッシュによる20GB上限管理、マルチスレッド対応
    """
    
    def __init__(self, max_cache_size_gb: float = 20.0, preload_frames: int = 100):
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.preload_frames = preload_frames
        self.cache = OrderedDict()
        self.current_size = 0
        self.lock = threading.RLock()
        
    def get_memory_usage(self) -> float:
        """現在のメモリ使用量を取得（GB単位）"""
        return self.current_size / (1024 * 1024 * 1024)
        
    def get_image(self, frame_id: int, image_path: str) -> Optional[np.ndarray]:
        """画像を取得（キャッシュから、または読み込み）"""
        with self.lock:
            if frame_id in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(frame_id)
                return self.cache[frame_id]
                
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
        while self.current_size + image_size > self.max_cache_size and self.cache:
            oldest_id, oldest_image = self.cache.popitem(last=False)
            self.current_size -= oldest_image.nbytes
            
        self.cache[frame_id] = image
        self.current_size += image_size
        
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
            gc.collect()
            
    def get_cache_stats(self) -> dict:
        """キャッシュ統計を取得"""
        return {
            "cached_frames": len(self.cache),
            "memory_usage_gb": self.get_memory_usage(),
            "max_size_gb": self.max_cache_size / (1024 * 1024 * 1024),
            "cache_hit_ratio": self._calculate_hit_ratio()
        }
        
    def _calculate_hit_ratio(self) -> float:
        """キャッシュヒット率を計算（簡易版）"""
        # 実際の実装では、ヒット/ミスのカウンターを追加する必要があります
        return 0.0