"""
Agent6 Cache Layer: メモリ監視機能

20GB上限制御・18GB早期警告・リアルタイム監視
"""
import time
import threading
import psutil
import gc
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class MemoryWarningLevel(Enum):
    """メモリ警告レベル"""
    NORMAL = "normal"      # < 15GB
    CAUTION = "caution"    # 15-18GB  
    WARNING = "warning"    # 18-19GB
    CRITICAL = "critical"  # 19-20GB
    EMERGENCY = "emergency" # > 20GB


@dataclass
class MemoryUsageSnapshot:
    """メモリ使用量スナップショット"""
    timestamp: float
    cache_memory_gb: float
    system_memory_gb: float
    cache_items_count: int
    warning_level: MemoryWarningLevel


class MemoryMonitor:
    """
    リアルタイムメモリ監視・制御システム
    
    機能:
    - 20GB上限制御
    - 18GB早期警告
    - システムメモリ監視
    - 自動ガベージコレクション
    """
    
    def __init__(self, cache_instance, monitoring_interval: float = 1.0):
        """
        Args:
            cache_instance: 監視対象キャッシュ
            monitoring_interval: 監視間隔（秒）
        """
        self.cache = cache_instance
        self.monitoring_interval = monitoring_interval
        
        # Memory thresholds (GB)
        self.memory_limit_gb = 20.0
        self.warning_threshold_gb = 18.0
        self.caution_threshold_gb = 15.0
        
        # Monitoring state
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Statistics
        self._memory_history = []
        self._warning_callbacks: Dict[MemoryWarningLevel, Callable] = {}
        self._last_cleanup_time = 0
        self._cleanup_interval = 60  # seconds
        
        # Performance tracking
        self._memory_pressure_events = 0
        self._emergency_cleanups = 0
    
    def start_monitoring(self):
        """メモリ監視開始"""
        with self._lock:
            if self._monitoring_active:
                return
            
            self._monitoring_active = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="MemoryMonitor"
            )
            self._monitor_thread.start()
    
    def stop_monitoring(self):
        """メモリ監視停止"""
        with self._lock:
            self._monitoring_active = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=2.0)
                self._monitor_thread = None
    
    def register_warning_callback(self, level: MemoryWarningLevel, callback: Callable):
        """警告レベル別コールバック登録"""
        self._warning_callbacks[level] = callback
    
    def get_current_memory_status(self) -> MemoryUsageSnapshot:
        """現在のメモリ状況取得"""
        cache_memory_gb = self.cache.get_memory_usage() / (1024**3)
        system_memory = psutil.virtual_memory()
        system_memory_gb = system_memory.used / (1024**3)
        
        warning_level = self._calculate_warning_level(cache_memory_gb)
        
        return MemoryUsageSnapshot(
            timestamp=time.time(),
            cache_memory_gb=cache_memory_gb,
            system_memory_gb=system_memory_gb,
            cache_items_count=self.cache.size(),
            warning_level=warning_level
        )
    
    def force_memory_cleanup(self, target_memory_gb: float = 15.0):
        """強制メモリクリーンアップ"""
        current_memory_gb = self.cache.get_memory_usage() / (1024**3)
        
        if current_memory_gb <= target_memory_gb:
            return True
        
        # Calculate items to remove
        items_to_remove = int((current_memory_gb - target_memory_gb) / current_memory_gb * self.cache.size())
        items_to_remove = max(1, min(items_to_remove, self.cache.size() // 2))
        
        # Force LRU eviction
        for _ in range(items_to_remove):
            if self.cache.size() == 0:
                break
            self.cache._evict_lru()
        
        # Force garbage collection
        gc.collect()
        
        self._emergency_cleanups += 1
        
        final_memory_gb = self.cache.get_memory_usage() / (1024**3)
        return final_memory_gb <= target_memory_gb
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """メモリ統計取得"""
        current_status = self.get_current_memory_status()
        
        return {
            'current_cache_memory_gb': current_status.cache_memory_gb,
            'current_system_memory_gb': current_status.system_memory_gb,
            'memory_limit_gb': self.memory_limit_gb,
            'warning_threshold_gb': self.warning_threshold_gb,
            'memory_usage_percent': (current_status.cache_memory_gb / self.memory_limit_gb) * 100,
            'current_warning_level': current_status.warning_level.value,
            'cache_items_count': current_status.cache_items_count,
            'memory_pressure_events': self._memory_pressure_events,
            'emergency_cleanups': self._emergency_cleanups,
            'monitoring_active': self._monitoring_active
        }
    
    def predict_memory_trend(self, minutes: int = 5) -> Dict[str, float]:
        """メモリ使用量傾向予測"""
        if len(self._memory_history) < 10:
            return {'predicted_memory_gb': 0.0, 'confidence': 0.0}
        
        # Simple linear regression on recent history
        recent_history = self._memory_history[-60:]  # Last 60 measurements
        times = [snapshot.timestamp for snapshot in recent_history]
        memories = [snapshot.cache_memory_gb for snapshot in recent_history]
        
        if len(recent_history) < 2:
            return {'predicted_memory_gb': memories[-1], 'confidence': 0.5}
        
        # Calculate trend
        time_diff = times[-1] - times[0]
        memory_diff = memories[-1] - memories[0]
        
        if time_diff == 0:
            return {'predicted_memory_gb': memories[-1], 'confidence': 0.5}
        
        trend_per_second = memory_diff / time_diff
        predicted_memory = memories[-1] + trend_per_second * (minutes * 60)
        
        # Confidence based on trend consistency
        confidence = min(1.0, len(recent_history) / 60.0)
        
        return {
            'predicted_memory_gb': max(0, predicted_memory),
            'trend_per_minute_gb': trend_per_second * 60,
            'confidence': confidence
        }
    
    def _monitoring_loop(self):
        """メモリ監視ループ"""
        while self._monitoring_active:
            try:
                # Get current memory status
                current_status = self.get_current_memory_status()
                
                # Record in history
                self._memory_history.append(current_status)
                
                # Keep only recent 1 hour of history
                if len(self._memory_history) > 3600:
                    self._memory_history = self._memory_history[-3600:]
                
                # Check warning levels
                self._check_warning_triggers(current_status)
                
                # Automatic cleanup if needed
                self._auto_cleanup_if_needed(current_status)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"Memory monitoring error: {e}")
                time.sleep(self.monitoring_interval)
    
    def _calculate_warning_level(self, memory_gb: float) -> MemoryWarningLevel:
        """警告レベル計算"""
        if memory_gb > self.memory_limit_gb:
            return MemoryWarningLevel.EMERGENCY
        elif memory_gb > 19.0:
            return MemoryWarningLevel.CRITICAL
        elif memory_gb > self.warning_threshold_gb:
            return MemoryWarningLevel.WARNING
        elif memory_gb > self.caution_threshold_gb:
            return MemoryWarningLevel.CAUTION
        else:
            return MemoryWarningLevel.NORMAL
    
    def _check_warning_triggers(self, status: MemoryUsageSnapshot):
        """警告トリガーチェック"""
        callback = self._warning_callbacks.get(status.warning_level)
        if callback:
            try:
                callback(status)
            except Exception as e:
                print(f"Warning callback error: {e}")
        
        # Count pressure events
        if status.warning_level.value in ["warning", "critical", "emergency"]:
            self._memory_pressure_events += 1
    
    def _auto_cleanup_if_needed(self, status: MemoryUsageSnapshot):
        """必要時自動クリーンアップ"""
        current_time = time.time()
        
        # Emergency cleanup
        if status.warning_level == MemoryWarningLevel.EMERGENCY:
            self.force_memory_cleanup(target_memory_gb=15.0)
            return
        
        # Critical cleanup
        if status.warning_level == MemoryWarningLevel.CRITICAL:
            self.force_memory_cleanup(target_memory_gb=17.0)
            return
        
        # Regular periodic cleanup
        if (current_time - self._last_cleanup_time > self._cleanup_interval and
            status.warning_level.value in ["warning", "critical", "emergency"]):
            gc.collect()  # Light cleanup
            self._last_cleanup_time = current_time
    
    def __enter__(self):
        """Context manager entry"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()