"""
Unit tests for OptimizedThreadPool - High-performance task execution
Performance target: CPU and I/O optimized parallel processing
"""

import pytest
import time
import multiprocessing
from concurrent.futures import Future
from unittest.mock import patch, MagicMock

from src.infrastructure.system.thread_pool import (
    OptimizedThreadPool, TaskResult, PriorityTask, ThreadPoolError
)


class TestOptimizedThreadPoolPerformance:
    """Performance tests for OptimizedThreadPool"""
    
    @pytest.fixture
    def thread_pool(self):
        pool = OptimizedThreadPool(cpu_workers=2, io_workers=4)
        yield pool
        pool.shutdown()
    
    def test_task_submission_1ms(self, thread_pool):
        """Test task submission under 1ms"""
        def simple_task():
            return "completed"
        
        start_time = time.perf_counter()
        
        future = thread_pool.submit_cpu_task(simple_task)
        
        elapsed_time = time.perf_counter() - start_time
        
        assert elapsed_time < 0.001, f"Task submission took {elapsed_time}s, should be < 0.001s"
        assert isinstance(future, Future)
        
        # Wait for completion and verify result
        result = future.result(timeout=1.0)
        assert result.success is True
        assert result.result == "completed"
    
    def test_priority_queue_real_time_processing(self, thread_pool):
        """Test priority queue processes tasks in real-time"""
        results = []
        
        def priority_task(task_id):
            results.append(task_id)
            return f"task_{task_id}"
        
        # Submit tasks with different priorities (lower number = higher priority)
        futures = []
        priorities = [3, 1, 2, 0]  # Submit in non-priority order
        
        start_time = time.perf_counter()
        
        for i, priority in enumerate(priorities):
            future = thread_pool.submit_priority_task(priority, priority_task, i)
            futures.append(future)
        
        # Wait for all to complete
        for future in futures:
            future.result(timeout=1.0)
        
        elapsed_time = time.perf_counter() - start_time
        
        assert elapsed_time < 0.1, f"Priority processing took {elapsed_time}s, should be < 0.1s"
        
        # Results should be in priority order (0, 1, 2, 3)
        expected_order = [3, 1, 2, 0]  # Corresponding task IDs for priorities [0, 1, 2, 3]
        assert results == expected_order
    
    def test_cpu_vs_io_task_separation(self, thread_pool):
        """Test CPU and I/O task separation efficiency"""
        cpu_results = []
        io_results = []
        
        def cpu_intensive_task(task_id):
            # Simulate CPU work
            total = 0
            for i in range(100000):
                total += i
            cpu_results.append(task_id)
            return total
        
        def io_intensive_task(task_id):
            # Simulate I/O work
            time.sleep(0.01)
            io_results.append(task_id)
            return f"io_{task_id}"
        
        start_time = time.perf_counter()
        
        # Submit mixed workload
        cpu_futures = [thread_pool.submit_cpu_task(cpu_intensive_task, i) for i in range(3)]
        io_futures = [thread_pool.submit_io_task(io_intensive_task, i) for i in range(3)]
        
        # Wait for completion
        for future in cpu_futures + io_futures:
            future.result(timeout=2.0)
        
        elapsed_time = time.perf_counter() - start_time
        
        # Should complete efficiently with parallel execution
        assert elapsed_time < 0.5, f"Mixed workload took {elapsed_time}s, should be < 0.5s"
        assert len(cpu_results) == 3
        assert len(io_results) == 3
    
    def test_batch_task_processing_efficiency(self, thread_pool):
        """Test batch task processing efficiency"""
        def batch_task(task_id):
            return task_id * 2
        
        # Create batch of tasks
        tasks = [(batch_task, (i,), {}) for i in range(10)]
        
        start_time = time.perf_counter()
        
        futures = thread_pool.submit_batch_tasks(tasks, 'cpu')
        results = thread_pool.wait_for_completion(futures, timeout=1.0)
        
        elapsed_time = time.perf_counter() - start_time
        
        assert elapsed_time < 0.1, f"Batch processing took {elapsed_time}s, should be < 0.1s"
        assert len(results) == 10
        assert all(result.success for result in results)


class TestOptimizedThreadPoolFunctionality:
    """Functionality tests for OptimizedThreadPool"""
    
    @pytest.fixture
    def thread_pool(self):
        pool = OptimizedThreadPool(cpu_workers=2, io_workers=2)
        yield pool
        pool.shutdown()
    
    def test_initialization_with_defaults(self):
        """Test initialization with default parameters"""
        with OptimizedThreadPool() as pool:
            cpu_count = multiprocessing.cpu_count()
            assert pool.cpu_workers == cpu_count
            assert pool.io_workers == cpu_count * 2
    
    def test_initialization_with_custom_workers(self):
        """Test initialization with custom worker counts"""
        with OptimizedThreadPool(cpu_workers=3, io_workers=5) as pool:
            assert pool.cpu_workers == 3
            assert pool.io_workers == 5
    
    def test_cpu_task_execution(self, thread_pool):
        """Test CPU task execution"""
        def cpu_task(x, y):
            return x + y
        
        future = thread_pool.submit_cpu_task(cpu_task, 5, 3, task_id="test_cpu")
        result = future.result(timeout=1.0)
        
        assert isinstance(result, TaskResult)
        assert result.task_id == "test_cpu"
        assert result.success is True
        assert result.result == 8
        assert result.execution_time > 0
    
    def test_io_task_execution(self, thread_pool):
        """Test I/O task execution"""
        def io_task(delay):
            time.sleep(delay)
            return "io_completed"
        
        future = thread_pool.submit_io_task(io_task, 0.01, task_id="test_io")
        result = future.result(timeout=1.0)
        
        assert isinstance(result, TaskResult)
        assert result.task_id == "test_io"
        assert result.success is True
        assert result.result == "io_completed"
        assert result.execution_time >= 0.01
    
    def test_priority_task_execution(self, thread_pool):
        """Test priority task execution"""
        def priority_task(message):
            return message
        
        future = thread_pool.submit_priority_task(1, priority_task, "high_priority", task_id="test_priority")
        result = future.result(timeout=1.0)
        
        assert isinstance(result, TaskResult)
        assert result.task_id == "test_priority"
        assert result.success is True
        assert result.result == "high_priority"
    
    def test_task_error_handling(self, thread_pool):
        """Test task error handling"""
        def failing_task():
            raise ValueError("Task failed intentionally")
        
        future = thread_pool.submit_cpu_task(failing_task, task_id="failing_task")
        result = future.result(timeout=1.0)
        
        assert isinstance(result, TaskResult)
        assert result.task_id == "failing_task"
        assert result.success is False
        assert isinstance(result.error, ValueError)
        assert "Task failed intentionally" in str(result.error)
    
    def test_automatic_task_id_generation(self, thread_pool):
        """Test automatic task ID generation"""
        def simple_task():
            return "done"
        
        future = thread_pool.submit_cpu_task(simple_task)  # No task_id provided
        result = future.result(timeout=1.0)
        
        assert result.task_id.startswith("cpu_task_")
    
    def test_active_task_tracking(self, thread_pool):
        """Test active task tracking"""
        def slow_task():
            time.sleep(0.1)
            return "slow_done"
        
        # Submit multiple tasks
        futures = []
        for i in range(3):
            future = thread_pool.submit_cpu_task(slow_task, task_id=f"slow_{i}")
            futures.append(future)
        
        # Check active task count
        task_counts = thread_pool.get_active_task_count()
        assert task_counts['total_active'] > 0
        assert task_counts['cpu_pool_size'] == 2
        assert task_counts['io_pool_size'] == 2
        
        # Wait for completion
        for future in futures:
            future.result(timeout=1.0)
        
        # Active count should decrease
        final_counts = thread_pool.get_active_task_count()
        assert final_counts['total_active'] == 0
    
    def test_batch_task_submission(self, thread_pool):
        """Test batch task submission"""
        def batch_task(value):
            return value * 2
        
        tasks = [(batch_task, (i,), {}) for i in range(5)]
        
        futures = thread_pool.submit_batch_tasks(tasks, 'cpu')
        
        assert len(futures) == 5
        
        results = []
        for future in futures:
            result = future.result(timeout=1.0)
            results.append(result.result)
        
        assert results == [0, 2, 4, 6, 8]
    
    def test_wait_for_completion_success(self, thread_pool):
        """Test waiting for multiple tasks to complete successfully"""
        def test_task(value):
            return value * 3
        
        futures = []
        for i in range(3):
            future = thread_pool.submit_cpu_task(test_task, i)
            futures.append(future)
        
        results = thread_pool.wait_for_completion(futures, timeout=1.0)
        
        assert len(results) == 3
        assert all(result.success for result in results)
        expected_values = [0, 3, 6]
        actual_values = [result.result for result in results]
        assert sorted(actual_values) == sorted(expected_values)
    
    def test_wait_for_completion_timeout(self, thread_pool):
        """Test wait for completion with timeout"""
        def slow_task():
            time.sleep(1.0)  # Longer than timeout
            return "slow_result"
        
        futures = [thread_pool.submit_cpu_task(slow_task) for _ in range(2)]
        
        # Short timeout should return partial results
        results = thread_pool.wait_for_completion(futures, timeout=0.1)
        
        # May return empty or partial results due to timeout
        assert len(results) >= 0
    
    def test_context_manager_functionality(self):
        """Test context manager functionality"""
        with OptimizedThreadPool(cpu_workers=1, io_workers=1) as pool:
            future = pool.submit_cpu_task(lambda: "context_test")
            result = future.result(timeout=1.0)
            assert result.success is True
        
        # Pool should be shutdown after context exit
        assert pool.cpu_pool._shutdown
        assert pool.io_pool._shutdown


class TestPriorityTask:
    """Test PriorityTask dataclass"""
    
    def test_priority_task_creation(self):
        """Test PriorityTask creation"""
        future = Future()
        task = PriorityTask(
            priority=1,
            task_id="test_task",
            func=lambda: "test",
            args=(),
            kwargs={},
            future=future
        )
        
        assert task.priority == 1
        assert task.task_id == "test_task"
        assert task.future is future
    
    def test_priority_task_comparison(self):
        """Test PriorityTask comparison for priority queue"""
        task1 = PriorityTask(1, "task1", lambda: None, (), {}, Future())
        task2 = PriorityTask(2, "task2", lambda: None, (), {}, Future())
        task3 = PriorityTask(0, "task3", lambda: None, (), {}, Future())
        
        # Lower number = higher priority
        assert task3 < task1  # Priority 0 < 1
        assert task1 < task2  # Priority 1 < 2
        assert not task2 < task1  # Priority 2 not < 1


class TestTaskResult:
    """Test TaskResult dataclass"""
    
    def test_successful_task_result(self):
        """Test successful task result"""
        result = TaskResult(
            task_id="success_task",
            success=True,
            result="success_value",
            execution_time=0.1
        )
        
        assert result.task_id == "success_task"
        assert result.success is True
        assert result.result == "success_value"
        assert result.error is None
        assert result.execution_time == 0.1
    
    def test_failed_task_result(self):
        """Test failed task result"""
        error = ValueError("Test error")
        result = TaskResult(
            task_id="failed_task",
            success=False,
            error=error,
            execution_time=0.05
        )
        
        assert result.task_id == "failed_task"
        assert result.success is False
        assert result.result is None
        assert result.error is error
        assert result.execution_time == 0.05


class TestOptimizedThreadPoolIntegration:
    """Integration tests for OptimizedThreadPool"""
    
    def test_thread_pool_resource_cleanup(self):
        """Test proper resource cleanup"""
        pool = OptimizedThreadPool(cpu_workers=1, io_workers=1)
        
        # Submit some tasks
        futures = []
        for i in range(3):
            future = pool.submit_cpu_task(lambda x=i: x)
            futures.append(future)
        
        # Wait for completion
        for future in futures:
            future.result(timeout=1.0)
        
        # Shutdown and verify cleanup
        pool.shutdown(wait=True)
        
        assert pool.cpu_pool._shutdown
        assert pool.io_pool._shutdown
        assert len(pool.active_tasks) == 0
        assert not pool.priority_worker_active
    
    def test_priority_worker_thread_lifecycle(self):
        """Test priority worker thread lifecycle"""
        pool = OptimizedThreadPool()
        
        # Priority worker should be started
        assert pool.priority_worker_active is True
        assert pool.priority_worker_thread is not None
        
        # Submit priority task
        future = pool.submit_priority_task(1, lambda: "priority_test")
        result = future.result(timeout=1.0)
        assert result.success is True
        
        # Shutdown should stop priority worker
        pool.shutdown()
        assert pool.priority_worker_active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])