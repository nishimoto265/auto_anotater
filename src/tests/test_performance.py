import unittest
import time
import psutil
import os
import numpy as np
from memory_profiler import profile
from line_profiler import LineProfiler

from src.core.image_cache import ImageCache

class PerformanceTest(unittest.TestCase):
    def setUp(self):
        self.image_cache = ImageCache()
        self.test_frames = self._generate_test_frames()
        self.test_bboxes = self._generate_test_bboxes()
        
    def _generate_test_frames(self):
        frames = []
        for i in range(1000):
            frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            frames.append(frame)
        return frames

    def _generate_test_bboxes(self):
        bboxes = []
        for i in range(100):
            bbox = {
                'id': i,
                'x': np.random.uniform(0, 1),
                'y': np.random.uniform(0, 1),
                'w': np.random.uniform(0, 0.5),
                'h': np.random.uniform(0, 0.5)
            }
            bboxes.append(bbox)
        return bboxes

    @profile
    def test_frame_switch_speed(self):
        times = []
        for i in range(100):
            start = time.perf_counter_ns()
            self.image_cache.get_frame(i)
            end = time.perf_counter_ns()
            times.append((end - start) / 1e6)  # Convert to ms
            
        avg_time = np.mean(times)
        self.assertLess(avg_time, 50.0)

    @profile  
    def test_image_display_speed(self):
        times = []
        for frame in self.test_frames[:10]:
            start = time.perf_counter_ns()
            self.image_cache.prepare_display(frame)
            end = time.perf_counter_ns()
            times.append((end - start) / 1e6)
            
        avg_time = np.mean(times)
        self.assertLess(avg_time, 100.0)

    @profile
    def test_bbox_drawing_speed(self):
        times = []
        for frame in self.test_frames[:10]:
            start = time.perf_counter_ns()
            self.image_cache.draw_bboxes(frame, self.test_bboxes)
            end = time.perf_counter_ns()
            times.append((end - start) / 1e6)
            
        avg_time = np.mean(times)
        self.assertLess(avg_time, 16.0)

    def test_memory_efficiency(self):
        initial_mem = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Load test data
        for _ in range(5):
            self.image_cache.load_frames(self.test_frames)
            
        final_mem = psutil.Process().memory_info().rss / 1024 / 1024
        mem_increase = final_mem - initial_mem
        
        self.assertLess(mem_increase, 1000)  # Max 1GB increase

    def test_load_performance(self):
        start_time = time.time()
        cpu_percent = psutil.cpu_percent(interval=1)
        io_counters_start = psutil.disk_io_counters()

        # Process 4K video frames
        for frame in self.test_frames:
            self.image_cache.process_frame(frame)

        end_time = time.time()
        io_counters_end = psutil.disk_io_counters()

        processing_time = end_time - start_time
        io_read = io_counters_end.read_bytes - io_counters_start.read_bytes
        io_write = io_counters_end.write_bytes - io_counters_start.write_bytes

        metrics = {
            'processing_time': processing_time,
            'cpu_percent': cpu_percent,
            'io_read_mb': io_read / (1024 * 1024),
            'io_write_mb': io_write / (1024 * 1024)
        }

        self.assertLess(processing_time, 60)  # Max 1 minute
        self.assertLess(cpu_percent, 80)  # Max 80% CPU
        
    def test_memory_leak(self):
        initial_mem = psutil.Process().memory_info().rss
        
        for _ in range(10):
            self.image_cache.load_frames(self.test_frames)
            self.image_cache.clear_cache()
            
        final_mem = psutil.Process().memory_info().rss
        leak = final_mem - initial_mem
        
        self.assertLess(leak, 10 * 1024 * 1024)  # Max 10MB leak

    def profile_bottlenecks(self):
        profiler = LineProfiler()
        profiler.add_function(self.image_cache.process_frame)
        profiler.add_function(self.image_cache.draw_bboxes)
        
        profiler.run("self.test_frame_switch_speed()")
        profiler.print_stats()

    def test_config_comparison(self):
        configs = [
            {'cache_size': 100, 'preload': 10},
            {'cache_size': 500, 'preload': 50},
            {'cache_size': 1000, 'preload': 100}
        ]
        
        results = {}
        for config in configs:
            self.image_cache.configure(config)
            start = time.time()
            self.test_frame_switch_speed()
            end = time.time()
            results[f"config_{config['cache_size']}"] = end - start
            
        return results

if __name__ == '__main__':
    unittest.main();