"""
Memory Manager - System memory optimization for Cache layer support
Performance target: 20GB memory limit management
"""

import psutil
import gc
import mmap
import os
from typing import Optional, Callable
from dataclasses import dataclass
from threading import Thread, Event
import time

from ..video.video_loader import InfrastructureError


class SystemResourceError(InfrastructureError):
    """System resource management error"""
    pass


@dataclass
class MemoryUsage:
    """Memory usage information container"""
    rss: int  # Resident Set Size (actual physical memory)
    vms: int  # Virtual Memory Size
    percent: float  # Memory percentage
    available: int  # Available system memory
    
    @property
    def rss_gb(self) -> float:
        """RSS in GB"""
        return self.rss / (1024 ** 3)
    
    @property
    def available_gb(self) -> float:
        """Available memory in GB"""
        return self.available / (1024 ** 3)


class MemoryManager:
    """
    Memory management system for Cache layer support
    
    Features:
    - Memory usage monitoring
    - Garbage collection optimization
    - Memory mapped file management
    - System memory efficiency optimization
    
    Performance targets:
    - Memory monitoring: 1ms or less
    - Memory limit: 20GB enforcement
    - Cleanup efficiency: Non-blocking execution
    """
    
    def __init__(self, memory_threshold_gb: float = 20.0):
        self.memory_threshold = int(memory_threshold_gb * 1024 ** 3)  # Convert to bytes
        self.monitoring_active = False
        self.monitoring_thread: Optional[Thread] = None
        self.stop_event = Event()
        self.cleanup_callbacks: list = []
        
        # Configure garbage collection for better performance
        self._configure_garbage_collection()
        
    def get_memory_usage(self) -> MemoryUsage:
        """
        Get current memory usage (1ms or less required)
        
        Returns:
            MemoryUsage: Current memory usage information
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            return MemoryUsage(
                rss=memory_info.rss,
                vms=memory_info.vms,
                percent=process.memory_percent(),
                available=system_memory.available
            )
        except Exception as e:
            raise SystemResourceError(f"Failed to get memory usage: {e}")
            
    def is_memory_limit_exceeded(self) -> bool:
        """
        Check if memory limit is exceeded
        
        Returns:
            bool: True if memory limit exceeded
        """
        usage = self.get_memory_usage()
        return usage.rss > self.memory_threshold
        
    def optimize_memory_usage(self) -> MemoryUsage:
        """
        Optimize memory usage (non-blocking execution required)
        
        Returns:
            MemoryUsage: Memory usage after optimization
        """
        # Force garbage collection
        collected = gc.collect()
        
        # Check memory usage after GC
        current_usage = self.get_memory_usage()
        
        # If still over threshold, trigger cache cleanup
        if current_usage.rss > self.memory_threshold:
            self._trigger_cache_cleanup()
            
        return current_usage
        
    def register_cleanup_callback(self, callback: Callable[[], None]):
        """
        Register cleanup callback for memory pressure situations
        
        Args:
            callback: Function to call when memory cleanup needed
        """
        self.cleanup_callbacks.append(callback)
        
    def _trigger_cache_cleanup(self):
        """
        Trigger Cache layer cleanup via registered callbacks
        """
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Cleanup callback failed: {e}")
                
    def start_continuous_monitoring(self, 
                                   interval_seconds: float = 1.0,
                                   callback: Optional[Callable[[MemoryUsage], None]] = None):
        """
        Start continuous memory monitoring
        
        Args:
            interval_seconds: Monitoring interval
            callback: Callback for memory usage reports
        """
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.stop_event.clear()
        
        def monitor_loop():
            while not self.stop_event.wait(interval_seconds):
                try:
                    usage = self.get_memory_usage()
                    
                    # Check for memory pressure
                    if usage.rss > self.memory_threshold * 0.9:  # 90% threshold
                        self.optimize_memory_usage()
                        
                    # Call user callback if provided
                    if callback:
                        callback(usage)
                        
                except Exception as e:
                    print(f"Memory monitoring error: {e}")
                    
        self.monitoring_thread = Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
    def stop_continuous_monitoring(self):
        """
        Stop continuous memory monitoring
        """
        if self.monitoring_active:
            self.monitoring_active = False
            self.stop_event.set()
            
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=2.0)
                self.monitoring_thread = None
                
    def create_memory_mapped_file(self, 
                                 file_path: str, 
                                 size_bytes: int,
                                 mode: str = 'w+b') -> mmap.mmap:
        """
        Create memory mapped file for large image handling
        
        Args:
            file_path: Path to file
            size_bytes: Size in bytes
            mode: File open mode
            
        Returns:
            mmap.mmap: Memory mapped file object
        """
        try:
            # Create file if it doesn't exist
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    f.write(b'\0' * size_bytes)
                    
            # Open file and create memory map
            file_obj = open(file_path, mode)
            memory_map = mmap.mmap(file_obj.fileno(), size_bytes)
            
            return memory_map
            
        except Exception as e:
            raise SystemResourceError(f"Failed to create memory mapped file: {e}")
            
    def get_system_memory_info(self) -> dict:
        """
        Get comprehensive system memory information
        
        Returns:
            dict: System memory information
        """
        try:
            virtual = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total_gb': virtual.total / (1024 ** 3),
                'available_gb': virtual.available / (1024 ** 3),
                'used_gb': virtual.used / (1024 ** 3),
                'percent': virtual.percent,
                'swap_total_gb': swap.total / (1024 ** 3),
                'swap_used_gb': swap.used / (1024 ** 3),
                'swap_percent': swap.percent
            }
        except Exception as e:
            raise SystemResourceError(f"Failed to get system memory info: {e}")
            
    def _configure_garbage_collection(self):
        """
        Configure garbage collection for optimal performance
        """
        # Set GC thresholds for better performance with large objects
        gc.set_threshold(700, 10, 10)
        
        # Enable garbage collection debugging if needed
        # gc.set_debug(gc.DEBUG_STATS)
        
    def force_garbage_collection(self) -> int:
        """
        Force garbage collection and return number of collected objects
        
        Returns:
            int: Number of objects collected
        """
        return gc.collect()
        
    def get_garbage_collection_stats(self) -> dict:
        """
        Get garbage collection statistics
        
        Returns:
            dict: GC statistics
        """
        stats = gc.get_stats()
        return {
            'collections': [stat['collections'] for stat in stats],
            'collected': [stat['collected'] for stat in stats],
            'uncollectable': [stat['uncollectable'] for stat in stats]
        }
        
    def check_memory_fragmentation(self) -> float:
        """
        Estimate memory fragmentation level
        
        Returns:
            float: Fragmentation ratio (0.0 = no fragmentation, 1.0 = high fragmentation)
        """
        usage = self.get_memory_usage()
        
        # Simple fragmentation estimation based on RSS vs VMS
        if usage.vms > 0:
            fragmentation_ratio = 1.0 - (usage.rss / usage.vms)
            return max(0.0, min(1.0, fragmentation_ratio))
        return 0.0
        
    def cleanup(self):
        """
        Cleanup memory manager resources
        """
        self.stop_continuous_monitoring()
        self.cleanup_callbacks.clear()
        
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
        
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass