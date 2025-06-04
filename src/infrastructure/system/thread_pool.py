"""
Optimized Thread Pool - High-performance task execution
Performance target: CPU and I/O optimized parallel processing
"""

import multiprocessing
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from queue import PriorityQueue, Empty
from threading import Thread, Event
from typing import Callable, Any, Optional, List, Tuple
import time
from dataclasses import dataclass

from ..video.video_loader import InfrastructureError


class ThreadPoolError(InfrastructureError):
    """Thread pool management error"""
    pass


@dataclass
class TaskResult:
    """Task execution result container"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0


@dataclass
class PriorityTask:
    """Priority task container"""
    priority: int
    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    future: Future
    
    def __lt__(self, other):
        return self.priority < other.priority


class OptimizedThreadPool:
    """
    Optimized thread pool for high-performance task execution
    
    Optimizations:
    - CPU-intensive processing ThreadPoolExecutor
    - I/O-intensive processing dedicated pool
    - Dynamic thread count adjustment
    - Priority-based task processing
    
    Performance targets:
    - Task submission: 1ms or less
    - Priority queue processing: Real-time
    - Resource efficiency: Optimal CPU/memory usage
    """
    
    def __init__(self, 
                 cpu_workers: Optional[int] = None,
                 io_workers: Optional[int] = None):
        
        # Configure worker counts
        cpu_count = multiprocessing.cpu_count()
        self.cpu_workers = cpu_workers or cpu_count
        self.io_workers = io_workers or (cpu_count * 2)
        
        # Create thread pools
        self.cpu_pool = ThreadPoolExecutor(
            max_workers=self.cpu_workers,
            thread_name_prefix="CPU-Worker"
        )
        self.io_pool = ThreadPoolExecutor(
            max_workers=self.io_workers,
            thread_name_prefix="IO-Worker"
        )
        
        # Priority queue management
        self.priority_queue = PriorityQueue()
        self.priority_worker_active = False
        self.priority_worker_thread: Optional[Thread] = None
        self.stop_event = Event()
        
        # Task tracking
        self.task_counter = 0
        self.active_tasks: dict = {}
        
        # Start priority worker
        self._start_priority_worker()
        
    def submit_cpu_task(self, 
                       func: Callable, 
                       *args, 
                       task_id: Optional[str] = None,
                       **kwargs) -> Future:
        """
        Submit CPU-intensive task
        
        Args:
            func: Function to execute
            *args: Function arguments
            task_id: Optional task identifier
            **kwargs: Function keyword arguments
            
        Returns:
            Future: Future object for result retrieval
        """
        if task_id is None:
            task_id = f"cpu_task_{self.task_counter}"
            self.task_counter += 1
            
        future = self.cpu_pool.submit(self._execute_with_timing, func, task_id, *args, **kwargs)
        self.active_tasks[task_id] = future
        
        return future
        
    def submit_io_task(self, 
                      func: Callable, 
                      *args,
                      task_id: Optional[str] = None,
                      **kwargs) -> Future:
        """
        Submit I/O-intensive task
        
        Args:
            func: Function to execute
            *args: Function arguments
            task_id: Optional task identifier
            **kwargs: Function keyword arguments
            
        Returns:
            Future: Future object for result retrieval
        """
        if task_id is None:
            task_id = f"io_task_{self.task_counter}"
            self.task_counter += 1
            
        future = self.io_pool.submit(self._execute_with_timing, func, task_id, *args, **kwargs)
        self.active_tasks[task_id] = future
        
        return future
        
    def submit_priority_task(self, 
                           priority: int, 
                           func: Callable,
                           *args,
                           task_id: Optional[str] = None,
                           **kwargs) -> Future:
        """
        Submit priority-based task (lower number = higher priority)
        
        Args:
            priority: Task priority (0 = highest)
            func: Function to execute
            *args: Function arguments
            task_id: Optional task identifier
            **kwargs: Function keyword arguments
            
        Returns:
            Future: Future object for result retrieval
        """
        if task_id is None:
            task_id = f"priority_task_{self.task_counter}"
            self.task_counter += 1
            
        future = Future()
        priority_task = PriorityTask(
            priority=priority,
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            future=future
        )
        
        self.priority_queue.put(priority_task)
        self.active_tasks[task_id] = future
        
        return future
        
    def submit_batch_tasks(self, 
                          tasks: List[Tuple[Callable, tuple, dict]], 
                          task_type: str = 'cpu') -> List[Future]:
        """
        Submit multiple tasks in batch
        
        Args:
            tasks: List of (func, args, kwargs) tuples
            task_type: 'cpu', 'io', or 'priority'
            
        Returns:
            List[Future]: List of Future objects
        """
        futures = []
        
        for i, (func, args, kwargs) in enumerate(tasks):
            task_id = f"batch_{task_type}_{i}_{self.task_counter}"
            
            if task_type == 'cpu':
                future = self.submit_cpu_task(func, *args, task_id=task_id, **kwargs)
            elif task_type == 'io':
                future = self.submit_io_task(func, *args, task_id=task_id, **kwargs)
            else:
                # Default priority for batch tasks
                future = self.submit_priority_task(10, func, *args, task_id=task_id, **kwargs)
                
            futures.append(future)
            
        return futures
        
    def wait_for_completion(self, 
                           futures: List[Future], 
                           timeout: Optional[float] = None) -> List[TaskResult]:
        """
        Wait for multiple tasks to complete
        
        Args:
            futures: List of Future objects
            timeout: Optional timeout in seconds
            
        Returns:
            List[TaskResult]: List of task results
        """
        results = []
        
        try:
            completed_futures = as_completed(futures, timeout=timeout)
            
            for future in completed_futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    error_result = TaskResult(
                        task_id="unknown",
                        success=False,
                        error=e
                    )
                    results.append(error_result)
                    
        except TimeoutError:
            # Handle partial results for timeout
            for future in futures:
                if future.done():
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        error_result = TaskResult(
                            task_id="unknown",
                            success=False,
                            error=e
                        )
                        results.append(error_result)
                        
        return results
        
    def get_active_task_count(self) -> dict:
        """
        Get count of active tasks by type
        
        Returns:
            dict: Task counts by type
        """
        return {
            'cpu_active': len([f for f in self.active_tasks.values() if not f.done()]),
            'total_active': len([f for f in self.active_tasks.values() if not f.done()]),
            'cpu_pool_size': self.cpu_workers,
            'io_pool_size': self.io_workers,
            'priority_queue_size': self.priority_queue.qsize()
        }
        
    def _execute_with_timing(self, func: Callable, task_id: str, *args, **kwargs) -> TaskResult:
        """
        Execute function with timing and error handling
        
        Args:
            func: Function to execute
            task_id: Task identifier
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            TaskResult: Execution result with timing
        """
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task_id,
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task_id,
                success=False,
                error=e,
                execution_time=execution_time
            )
        finally:
            # Remove from active tasks
            self.active_tasks.pop(task_id, None)
            
    def _start_priority_worker(self):
        """
        Start priority queue worker thread
        """
        if self.priority_worker_active:
            return
            
        self.priority_worker_active = True
        self.stop_event.clear()
        
        def priority_worker_loop():
            while not self.stop_event.is_set():
                try:
                    # Get priority task with timeout
                    priority_task = self.priority_queue.get(timeout=0.1)
                    
                    # Execute task
                    result = self._execute_with_timing(
                        priority_task.func,
                        priority_task.task_id,
                        *priority_task.args,
                        **priority_task.kwargs
                    )
                    
                    # Set future result
                    if result.success:
                        priority_task.future.set_result(result)
                    else:
                        priority_task.future.set_exception(result.error)
                        
                    self.priority_queue.task_done()
                    
                except Empty:
                    continue
                except Exception as e:
                    print(f"Priority worker error: {e}")
                    
        self.priority_worker_thread = Thread(target=priority_worker_loop, daemon=True)
        self.priority_worker_thread.start()
        
    def shutdown(self, wait: bool = True):
        """
        Shutdown thread pools
        
        Args:
            wait: Whether to wait for completion
        """
        # Stop priority worker
        self.priority_worker_active = False
        self.stop_event.set()
        
        if self.priority_worker_thread:
            self.priority_worker_thread.join(timeout=2.0)
            
        # Shutdown thread pools
        self.cpu_pool.shutdown(wait=wait)
        self.io_pool.shutdown(wait=wait)
        
        # Clear active tasks
        self.active_tasks.clear()
        
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()
        
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.shutdown(wait=False)
        except:
            pass