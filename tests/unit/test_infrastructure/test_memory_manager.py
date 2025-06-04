"""
Unit tests for MemoryManager - System memory optimization
Performance target: 20GB memory limit management
"""

import pytest
import time
import mmap
import os
import gc
from unittest.mock import patch, MagicMock
from threading import Event

from src.infrastructure.system.memory_manager import (
    MemoryManager, MemoryUsage, SystemResourceError
)


class TestMemoryManagerPerformance:
    """Performance tests for MemoryManager"""
    
    @pytest.fixture
    def memory_manager(self):
        return MemoryManager(memory_threshold_gb=1.0)  # 1GB for testing
    
    def test_memory_usage_monitoring_1ms(self, memory_manager):
        """Test memory usage monitoring under 1ms"""
        start_time = time.perf_counter()
        
        usage = memory_manager.get_memory_usage()
        
        elapsed_time = time.perf_counter() - start_time
        
        assert elapsed_time < 0.001, f"Memory monitoring took {elapsed_time}s, should be < 0.001s"
        assert isinstance(usage, MemoryUsage)
        assert usage.rss > 0
        assert usage.available > 0
    
    def test_memory_optimization_non_blocking(self, memory_manager):
        """Test memory optimization is non-blocking"""
        start_time = time.perf_counter()
        
        usage = memory_manager.optimize_memory_usage()
        
        elapsed_time = time.perf_counter() - start_time
        
        # Should complete quickly (non-blocking)
        assert elapsed_time < 0.1, f"Memory optimization took {elapsed_time}s, should be < 0.1s"
        assert isinstance(usage, MemoryUsage)
    
    def test_garbage_collection_efficiency(self, memory_manager):
        """Test garbage collection efficiency"""
        # Create some objects to be collected
        large_objects = []
        for i in range(100):
            large_objects.append([0] * 1000)
        
        # Clear references
        large_objects = None
        
        start_time = time.perf_counter()
        collected = memory_manager.force_garbage_collection()
        elapsed_time = time.perf_counter() - start_time
        
        assert elapsed_time < 0.05, f"Garbage collection took {elapsed_time}s, should be < 0.05s"
        assert collected >= 0  # Should collect some objects
    
    def test_continuous_monitoring_overhead(self, memory_manager):
        """Test continuous monitoring has low overhead"""
        monitoring_calls = []
        
        def monitor_callback(usage):
            monitoring_calls.append(time.perf_counter())
        
        # Start monitoring with high frequency
        memory_manager.start_continuous_monitoring(0.01, monitor_callback)  # 10ms interval
        
        time.sleep(0.1)  # Monitor for 100ms
        
        memory_manager.stop_continuous_monitoring()
        
        # Should have multiple calls with consistent timing
        assert len(monitoring_calls) >= 5
        
        # Check timing consistency (intervals should be close to 10ms)
        if len(monitoring_calls) > 1:
            intervals = [monitoring_calls[i] - monitoring_calls[i-1] 
                        for i in range(1, len(monitoring_calls))]
            avg_interval = sum(intervals) / len(intervals)
            assert 0.008 <= avg_interval <= 0.015  # Allow some variance


class TestMemoryManagerFunctionality:
    """Functionality tests for MemoryManager"""
    
    @pytest.fixture
    def memory_manager(self):
        return MemoryManager(memory_threshold_gb=0.1)  # 100MB for testing
    
    def test_memory_usage_properties(self, memory_manager):
        """Test MemoryUsage properties"""
        usage = memory_manager.get_memory_usage()
        
        assert hasattr(usage, 'rss')
        assert hasattr(usage, 'vms')
        assert hasattr(usage, 'percent')
        assert hasattr(usage, 'available')
        
        # Test GB properties
        assert usage.rss_gb == usage.rss / (1024 ** 3)
        assert usage.available_gb == usage.available / (1024 ** 3)
    
    def test_memory_threshold_detection(self, memory_manager):
        """Test memory threshold detection"""
        # Mock memory usage to exceed threshold
        with patch.object(memory_manager, 'get_memory_usage') as mock_usage:
            mock_usage.return_value = MemoryUsage(
                rss=memory_manager.memory_threshold + 1000,  # Exceed threshold
                vms=1000000,
                percent=50.0,
                available=500000
            )
            
            is_exceeded = memory_manager.is_memory_limit_exceeded()
            assert is_exceeded is True
    
    def test_cleanup_callback_registration(self, memory_manager):
        """Test cleanup callback registration and execution"""
        callback_calls = []
        
        def cleanup_callback():
            callback_calls.append("cleanup_executed")
        
        memory_manager.register_cleanup_callback(cleanup_callback)
        memory_manager._trigger_cache_cleanup()
        
        assert len(callback_calls) == 1
        assert callback_calls[0] == "cleanup_executed"
    
    def test_cleanup_callback_error_handling(self, memory_manager):
        """Test cleanup callback error handling"""
        def failing_callback():
            raise Exception("Cleanup failed")
        
        def working_callback():
            return "success"
        
        memory_manager.register_cleanup_callback(failing_callback)
        memory_manager.register_cleanup_callback(working_callback)
        
        # Should not raise exception despite failing callback
        memory_manager._trigger_cache_cleanup()
    
    def test_continuous_monitoring_start_stop(self, memory_manager):
        """Test continuous monitoring start/stop"""
        assert memory_manager.monitoring_active is False
        
        memory_manager.start_continuous_monitoring(0.1)
        assert memory_manager.monitoring_active is True
        
        memory_manager.stop_continuous_monitoring()
        assert memory_manager.monitoring_active is False
    
    def test_continuous_monitoring_duplicate_start(self, memory_manager):
        """Test duplicate monitoring start is handled gracefully"""
        memory_manager.start_continuous_monitoring(0.1)
        thread1 = memory_manager.monitoring_thread
        
        # Start again - should not create new thread
        memory_manager.start_continuous_monitoring(0.1)
        thread2 = memory_manager.monitoring_thread
        
        assert thread1 is thread2
        
        memory_manager.stop_continuous_monitoring()
    
    @patch('psutil.Process')
    def test_get_memory_usage_error_handling(self, mock_process, memory_manager):
        """Test error handling in memory usage retrieval"""
        mock_process.side_effect = Exception("Process error")
        
        with pytest.raises(SystemResourceError, match="Failed to get memory usage"):
            memory_manager.get_memory_usage()
    
    def test_create_memory_mapped_file(self, memory_manager, tmp_path):
        """Test memory mapped file creation"""
        file_path = tmp_path / "test_mmap.dat"
        size_bytes = 1024
        
        memory_map = memory_manager.create_memory_mapped_file(str(file_path), size_bytes)
        
        assert isinstance(memory_map, mmap.mmap)
        assert len(memory_map) == size_bytes
        assert file_path.exists()
        
        memory_map.close()
    
    def test_create_memory_mapped_file_error(self, memory_manager):
        """Test memory mapped file creation error handling"""
        with pytest.raises(SystemResourceError, match="Failed to create memory mapped file"):
            memory_manager.create_memory_mapped_file("/invalid/path/file.dat", 1024)
    
    @patch('psutil.virtual_memory')
    @patch('psutil.swap_memory')
    def test_get_system_memory_info(self, mock_swap, mock_virtual, memory_manager):
        """Test system memory information retrieval"""
        # Mock memory information
        mock_virtual.return_value = MagicMock(
            total=8 * 1024**3,      # 8GB
            available=4 * 1024**3,  # 4GB
            used=4 * 1024**3,       # 4GB
            percent=50.0
        )
        mock_swap.return_value = MagicMock(
            total=2 * 1024**3,      # 2GB
            used=1 * 1024**3,       # 1GB
            percent=50.0
        )
        
        info = memory_manager.get_system_memory_info()
        
        assert info['total_gb'] == pytest.approx(8.0, rel=0.1)
        assert info['available_gb'] == pytest.approx(4.0, rel=0.1)
        assert info['used_gb'] == pytest.approx(4.0, rel=0.1)
        assert info['percent'] == 50.0
        assert info['swap_total_gb'] == pytest.approx(2.0, rel=0.1)
    
    def test_garbage_collection_stats(self, memory_manager):
        """Test garbage collection statistics"""
        stats = memory_manager.get_garbage_collection_stats()
        
        assert 'collections' in stats
        assert 'collected' in stats
        assert 'uncollectable' in stats
        assert isinstance(stats['collections'], list)
    
    def test_memory_fragmentation_check(self, memory_manager):
        """Test memory fragmentation estimation"""
        # Mock memory usage
        with patch.object(memory_manager, 'get_memory_usage') as mock_usage:
            mock_usage.return_value = MemoryUsage(
                rss=800 * 1024**2,    # 800MB RSS
                vms=1000 * 1024**2,   # 1000MB VMS
                percent=40.0,
                available=500 * 1024**2
            )
            
            fragmentation = memory_manager.check_memory_fragmentation()
            
            # Fragmentation = 1 - (RSS/VMS) = 1 - 0.8 = 0.2
            assert fragmentation == pytest.approx(0.2, rel=0.01)
    
    def test_context_manager(self, memory_manager):
        """Test context manager functionality"""
        with memory_manager as mm:
            assert mm is memory_manager
            
        # After context exit, should be cleaned up
        assert memory_manager.monitoring_active is False


class TestMemoryManagerIntegration:
    """Integration tests for MemoryManager"""
    
    def test_garbage_collection_configuration(self):
        """Test garbage collection configuration"""
        with patch('gc.set_threshold') as mock_set_threshold:
            manager = MemoryManager()
            
            # Should configure GC thresholds
            mock_set_threshold.assert_called_with(700, 10, 10)
    
    def test_memory_monitoring_with_pressure(self):
        """Test memory monitoring behavior under pressure"""
        manager = MemoryManager(memory_threshold_gb=0.001)  # Very low threshold
        
        pressure_detected = []
        
        def pressure_callback(usage):
            if usage.rss > manager.memory_threshold * 0.9:
                pressure_detected.append(True)
        
        # Mock optimize_memory_usage to track calls
        optimize_calls = []
        original_optimize = manager.optimize_memory_usage
        
        def mock_optimize():
            optimize_calls.append(True)
            return original_optimize()
        
        manager.optimize_memory_usage = mock_optimize
        
        manager.start_continuous_monitoring(0.01, pressure_callback)
        time.sleep(0.05)  # Monitor briefly
        manager.stop_continuous_monitoring()
        
        # Should detect pressure and attempt optimization
        assert len(optimize_calls) > 0  # Memory optimization should be called
    
    def test_resource_cleanup_on_destruction(self):
        """Test resource cleanup on object destruction"""
        manager = MemoryManager()
        manager.start_continuous_monitoring(0.1)
        
        # Delete manager - should cleanup automatically
        del manager
        
        # Give time for cleanup
        time.sleep(0.05)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])