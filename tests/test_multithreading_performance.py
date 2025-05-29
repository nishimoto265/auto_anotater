import unittest
import time
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import os
import cv2

# Import from src directory structure
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.image_cache import ImageCache
from src.core.frame_manager import FrameManager

class MockAnnotationManager:
    """Mock annotation manager for testing"""
    def get_annotations(self, frame_number):
        # Return some dummy annotations
        if frame_number % 10 == 0:
            return [{'id': 1, 'x': 0.1, 'y': 0.1, 'w': 0.2, 'h': 0.2}]
        return []

class MultithreadingPerformanceTest(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.num_frames = 200
        self.frame_paths = []
        
        # Create test images
        for i in range(self.num_frames):
            frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
            path = os.path.join(self.test_dir, f"frame_{i:04d}.jpg")
            cv2.imwrite(path, frame)
            self.frame_paths.append(path)
            
        # Initialize components
        self.image_cache = ImageCache(max_cache_size_gb=2.0, preload_frames=100, num_threads=8)
        self.image_cache.set_frame_paths(self.frame_paths)
        
        self.annotation_manager = MockAnnotationManager()
        self.frame_manager = FrameManager(self.image_cache, self.annotation_manager)
        self.frame_manager.initialize(self.num_frames)
        
    def tearDown(self):
        """Clean up test environment"""
        # Shutdown thread pools
        self.frame_manager.shutdown()
        
        # Remove test images
        for path in self.frame_paths:
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(self.test_dir)
        
    def test_frame_switch_performance(self):
        """Test that frame switching meets <50ms requirement"""
        print("\n=== Frame Switch Performance Test ===")
        
        # Warm up cache
        for i in range(10):
            self.frame_manager.move_to_frame(i)
            
        # Test frame switching
        switch_times = []
        for i in range(10, 50):
            start_time = time.time()
            success = self.frame_manager.move_to_frame(i)
            switch_time = (time.time() - start_time) * 1000  # Convert to ms
            
            self.assertTrue(success)
            switch_times.append(switch_time)
            
        avg_switch_time = sum(switch_times) / len(switch_times)
        max_switch_time = max(switch_times)
        
        print(f"Average frame switch time: {avg_switch_time:.2f}ms")
        print(f"Maximum frame switch time: {max_switch_time:.2f}ms")
        print(f"Target: <50ms")
        
        # Check performance
        self.assertLess(avg_switch_time, 50.0, "Average frame switch time exceeds 50ms")
        
    def test_concurrent_frame_loading(self):
        """Test concurrent loading of multiple frames"""
        print("\n=== Concurrent Frame Loading Test ===")
        
        # Clear cache to test cold start
        self.image_cache.clear()
        
        # Load multiple frames concurrently
        frame_ids = list(range(0, 100, 10))  # Every 10th frame
        
        start_time = time.time()
        
        # Request frames concurrently
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for frame_id in frame_ids:
                future = executor.submit(self.image_cache.get_image, frame_id)
                futures.append(future)
                
            # Wait for all to complete
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result is not None)
                
        load_time = (time.time() - start_time) * 1000
        
        print(f"Loaded {len(frame_ids)} frames in {load_time:.2f}ms")
        print(f"Average per frame: {load_time/len(frame_ids):.2f}ms")
        
        # All frames should be loaded successfully
        self.assertTrue(all(results))
        
    def test_preload_efficiency(self):
        """Test that preloading improves subsequent access times"""
        print("\n=== Preload Efficiency Test ===")
        
        # Clear cache
        self.image_cache.clear()
        
        # Move to frame 50 to trigger preloading
        self.frame_manager.move_to_frame(50)
        
        # Wait a bit for preloading to work
        time.sleep(0.5)
        
        # Test access times for nearby frames
        cache_hits = []
        access_times = []
        
        for offset in range(-10, 11):
            frame_id = 50 + offset
            
            start_time = time.time()
            image = self.image_cache.get_image(frame_id)
            access_time = (time.time() - start_time) * 1000
            
            access_times.append(access_time)
            cache_hits.append(self.image_cache.is_loaded(frame_id))
            
        hit_rate = sum(cache_hits) / len(cache_hits)
        avg_access_time = sum(access_times) / len(access_times)
        
        print(f"Cache hit rate: {hit_rate*100:.1f}%")
        print(f"Average access time: {avg_access_time:.2f}ms")
        
        # Should have high hit rate for nearby frames
        self.assertGreater(hit_rate, 0.8, "Cache hit rate too low")
        
    def test_thread_safety(self):
        """Test thread safety with concurrent operations"""
        print("\n=== Thread Safety Test ===")
        
        errors = []
        
        def worker(start_frame, end_frame):
            try:
                for i in range(start_frame, end_frame):
                    # Simulate random operations
                    self.frame_manager.move_to_frame(i)
                    self.image_cache.get_image(i)
                    self.frame_manager.get_frame_state(i)
            except Exception as e:
                errors.append(e)
                
        # Run multiple threads concurrently
        threads = []
        for i in range(4):
            start = i * 25
            end = (i + 1) * 25
            thread = threading.Thread(target=worker, args=(start, end))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join()
            
        print(f"Completed with {len(errors)} errors")
        
        # Should complete without errors
        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")
        
    def test_memory_efficiency(self):
        """Test that cache respects memory limits"""
        print("\n=== Memory Efficiency Test ===")
        
        # Try to load many frames
        for i in range(self.num_frames):
            self.image_cache.get_image(i)
            
        # Check memory usage
        memory_usage = self.image_cache.get_memory_usage()
        max_size = 2.0  # GB
        
        print(f"Memory usage: {memory_usage:.2f} GB")
        print(f"Maximum allowed: {max_size} GB")
        
        # Should not exceed limit
        self.assertLessEqual(memory_usage, max_size * 1.1, "Memory usage exceeds limit")
        
    def test_performance_metrics(self):
        """Test performance tracking and metrics"""
        print("\n=== Performance Metrics Test ===")
        
        # Perform various operations
        for i in range(50):
            self.frame_manager.move_to_frame(i)
            
        # Get statistics
        stats = self.frame_manager.get_progress_stats()
        cache_stats = stats['cache_stats']
        
        print(f"Average frame switch: {stats['avg_frame_switch_ms']:.2f}ms")
        print(f"Cache hit ratio: {cache_stats['cache_hit_ratio']*100:.1f}%")
        print(f"Average load time: {cache_stats['avg_load_time_ms']:.2f}ms")
        print(f"Cached frames: {cache_stats['cached_frames']}")
        
        # Verify metrics are being tracked
        self.assertGreater(stats['avg_frame_switch_ms'], 0)
        self.assertGreater(cache_stats['total_requests'], 0)
        
if __name__ == '__main__':
    unittest.main(verbosity=2)