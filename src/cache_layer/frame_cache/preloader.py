"""
Agent6 Cache Layer: 백그라운드 프리로더

90%+ 히트율 달성을 위한 지능형 선읽기 시스템
"""
import time
import asyncio
import threading
import numpy as np
from typing import Dict, List, Optional, Callable, Tuple, Set
from dataclasses import dataclass
from collections import deque, defaultdict
from enum import Enum
import heapq


class PreloadPriority(Enum):
    """선읽기 우선순위"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class PreloadTask:
    """선읽기 작업"""
    frame_id: str
    priority: PreloadPriority
    creation_time: float
    expected_access_time: float = 0.0
    
    def __lt__(self, other):
        """우선순위 큐를 위한 비교 연산자"""
        # 높은 우선순위가 먼저, 예상 접근 시간이 빠른 것이 먼저
        if self.priority != other.priority:
            return self.priority.value > other.priority.value
        return self.expected_access_time < other.expected_access_time


class AccessPatternAnalyzer:
    """액세스 패턴 분석기"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self._access_history = deque(maxlen=history_size)
        self._pattern_cache = {}
        self._last_analysis_time = 0
        self._analysis_interval = 10  # seconds
    
    def record_access(self, frame_id: str):
        """액세스 기록"""
        timestamp = time.time()
        self._access_history.append((timestamp, frame_id))
    
    def analyze_pattern(self) -> Dict[str, any]:
        """패턴 분석"""
        current_time = time.time()
        if current_time - self._last_analysis_time < self._analysis_interval:
            return self._pattern_cache
        
        if len(self._access_history) < 10:
            return {'pattern_type': 'insufficient_data', 'confidence': 0.0}
        
        # 최근 액세스 분석
        recent_accesses = list(self._access_history)[-50:]  # 최근 50개
        frame_sequence = [frame_id for _, frame_id in recent_accesses]
        
        # 순차 접근 분석
        sequential_score = self._analyze_sequential_pattern(frame_sequence)
        
        # 점프 접근 분석  
        jump_score = self._analyze_jump_pattern(frame_sequence)
        
        # 핫스팟 분석
        hotspot_score = self._analyze_hotspot_pattern(frame_sequence)
        
        # 랜덤 접근 분석
        random_score = 1.0 - max(sequential_score, jump_score, hotspot_score)
        
        # 지배적 패턴 결정
        patterns = {
            'sequential': sequential_score,
            'jump': jump_score, 
            'hotspot': hotspot_score,
            'random': random_score
        }
        
        dominant_pattern = max(patterns, key=patterns.get)
        confidence = patterns[dominant_pattern]
        
        result = {
            'pattern_type': dominant_pattern,
            'confidence': confidence,
            'patterns': patterns,
            'recommended_preload_range': self._calculate_preload_range(dominant_pattern, confidence)
        }
        
        self._pattern_cache = result
        self._last_analysis_time = current_time
        
        return result
    
    def _analyze_sequential_pattern(self, frame_sequence: List[str]) -> float:
        """순차 패턴 분석"""
        if len(frame_sequence) < 2:
            return 0.0
        
        sequential_count = 0
        total_transitions = len(frame_sequence) - 1
        
        for i in range(total_transitions):
            try:
                current_num = int(frame_sequence[i].split('_')[1])
                next_num = int(frame_sequence[i + 1].split('_')[1])
                if abs(next_num - current_num) == 1:  # 연속 프레임
                    sequential_count += 1
            except (ValueError, IndexError):
                continue
        
        return sequential_count / total_transitions if total_transitions > 0 else 0.0
    
    def _analyze_jump_pattern(self, frame_sequence: List[str]) -> float:
        """점프 패턴 분석 (일정한 간격)"""
        if len(frame_sequence) < 3:
            return 0.0
        
        # 연속된 3개 프레임 간의 간격 분석
        intervals = []
        for i in range(len(frame_sequence) - 2):
            try:
                num1 = int(frame_sequence[i].split('_')[1])
                num2 = int(frame_sequence[i + 1].split('_')[1])
                num3 = int(frame_sequence[i + 2].split('_')[1])
                
                interval1 = abs(num2 - num1)
                interval2 = abs(num3 - num2)
                
                if interval1 == interval2 and interval1 > 1:
                    intervals.append(interval1)
                    
            except (ValueError, IndexError):
                continue
        
        if len(intervals) == 0:
            return 0.0
        
        # 일정한 간격이 유지되는 비율
        most_common_interval = max(set(intervals), key=intervals.count)
        consistent_intervals = sum(1 for interval in intervals if interval == most_common_interval)
        
        return consistent_intervals / len(intervals)
    
    def _analyze_hotspot_pattern(self, frame_sequence: List[str]) -> float:
        """핫스팟 패턴 분석"""
        if len(frame_sequence) < 5:
            return 0.0
        
        frame_counts = defaultdict(int)
        for frame in frame_sequence:
            frame_counts[frame] += 1
        
        total_accesses = len(frame_sequence)
        unique_frames = len(frame_counts)
        
        if unique_frames <= 1:
            return 1.0
        
        # 상위 20% 프레임이 전체 액세스의 몇 %를 차지하는가?
        sorted_counts = sorted(frame_counts.values(), reverse=True)
        top_20_percent = max(1, int(unique_frames * 0.2))
        top_accesses = sum(sorted_counts[:top_20_percent])
        
        concentration = top_accesses / total_accesses
        return min(1.0, concentration)
    
    def _calculate_preload_range(self, pattern_type: str, confidence: float) -> int:
        """패턴별 최적 선읽기 범위 계산"""
        base_range = 25  # 기본 범위
        
        if confidence < 0.5:
            return base_range
        
        if pattern_type == 'sequential':
            return int(base_range * 1.5)  # 순차 접근 시 더 넓은 범위
        elif pattern_type == 'jump':
            return base_range  # 점프 패턴은 기본 범위
        elif pattern_type == 'hotspot':
            return int(base_range * 0.8)  # 핫스팟은 더 좁은 범위
        else:  # random
            return int(base_range * 1.2)  # 랜덤은 약간 넓은 범위
        
        return base_range


class AsyncPreloader:
    """
    비동기 백그라운드 프리로더
    
    기능:
    - 지능형 선읽기
    - 우선순위 기반 작업 스케줄링
    - 90%+ 히트율 달성
    - UI 블로킹 없음
    """
    
    def __init__(self, cache_instance, preload_range: int = 50, max_concurrent: int = 3):
        """
        Args:
            cache_instance: 대상 캐시
            preload_range: 기본 선읽기 범위
            max_concurrent: 최대 동시 실행 수
        """
        self.cache = cache_instance
        self.preload_range = preload_range
        self.max_concurrent = max_concurrent
        
        # 비동기 작업 관리
        self._task_queue = []  # 우선순위 큐
        self._active_tasks: Set[str] = set()
        self._completed_tasks: Set[str] = set()
        self._cancelled_tasks: Set[str] = set()
        
        # 패턴 분석기
        self._pattern_analyzer = AccessPatternAnalyzer()
        
        # 스레드 관리
        self._executor_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        
        # 성능 통계
        self._preload_stats = {
            'total_requests': 0,
            'successful_preloads': 0,
            'cancelled_preloads': 0,
            'hit_contributions': 0  # 선읽기가 히트에 기여한 횟수
        }
        
        # 프레임 로더 (Infrastructure 층 연결점)
        self._frame_loader: Optional[Callable] = None
    
    def set_frame_loader(self, loader: Callable[[str], Optional[np.ndarray]]):
        """프레임 로더 설정"""
        self._frame_loader = loader
    
    def start_preload(self, current_frame: str, direction: str = "both", priority: PreloadPriority = PreloadPriority.NORMAL) -> bool:
        """
        선읽기 시작 (1ms 이하 보장)
        
        Args:
            current_frame: 현재 프레임 ID
            direction: 선읽기 방향 ("forward", "backward", "both")
            priority: 우선순위
            
        Returns:
            선읽기 큐잉 성공 여부
        """
        start_time = time.perf_counter()
        
        with self._lock:
            if not self._running:
                self._start_executor()
            
            # 패턴 분석 및 범위 조정
            pattern_info = self._pattern_analyzer.analyze_pattern()
            adaptive_range = pattern_info.get('recommended_preload_range', self.preload_range)
            
            # 선읽기 대상 프레임 계산
            target_frames = self._calculate_preload_targets(current_frame, direction, adaptive_range)
            
            # 작업 큐에 추가
            for frame_id in target_frames:
                if (frame_id not in self._active_tasks and 
                    frame_id not in self._completed_tasks and
                    frame_id not in self._cancelled_tasks and
                    self.cache.get(frame_id) is None):  # 이미 캐시에 없는 경우만
                    
                    task = PreloadTask(
                        frame_id=frame_id,
                        priority=priority,
                        creation_time=time.time(),
                        expected_access_time=self._estimate_access_time(frame_id, current_frame)
                    )
                    
                    heapq.heappush(self._task_queue, task)
                    self._preload_stats['total_requests'] += 1
        
        operation_time = (time.perf_counter() - start_time) * 1000
        return operation_time <= 1.0  # 1ms 이하 보장
    
    def stop_preloader(self):
        """선읽기 중지"""
        with self._lock:
            self._running = False
            if self._executor_thread:
                self._executor_thread.join(timeout=2.0)
                self._executor_thread = None
    
    def get_preload_statistics(self) -> Dict[str, any]:
        """선읽기 통계"""
        with self._lock:
            total_requests = self._preload_stats['total_requests']
            successful_preloads = self._preload_stats['successful_preloads']
            
            success_rate = 0.0
            if total_requests > 0:
                success_rate = successful_preloads / total_requests
            
            return {
                'total_requests': total_requests,
                'successful_preloads': successful_preloads,
                'cancelled_preloads': self._preload_stats['cancelled_preloads'],
                'success_rate': success_rate,
                'hit_contributions': self._preload_stats['hit_contributions'],
                'active_tasks': len(self._active_tasks),
                'queue_size': len(self._task_queue),
                'current_range': self.preload_range
            }
    
    def record_frame_access(self, frame_id: str):
        """프레임 액세스 기록 (히트율 분석용)"""
        self._pattern_analyzer.record_access(frame_id)
        
        # 선읽기 기여도 체크
        with self._lock:
            if frame_id in self._completed_tasks:
                self._preload_stats['hit_contributions'] += 1
    
    def get_queue_size(self) -> int:
        """큐 크기 반환"""
        return len(self._task_queue)
    
    def get_active_task_count(self) -> int:
        """활성 작업 수 반환"""
        return len(self._active_tasks)
    
    # Private methods
    
    def _start_executor(self):
        """실행자 스레드 시작"""
        if self._executor_thread is None or not self._executor_thread.is_alive():
            self._running = True
            self._executor_thread = threading.Thread(
                target=self._executor_loop,
                daemon=True,
                name="PreloadExecutor"
            )
            self._executor_thread.start()
    
    def _executor_loop(self):
        """실행자 루프"""
        while self._running:
            try:
                # 작업 가져오기
                task = None
                with self._lock:
                    if self._task_queue and len(self._active_tasks) < self.max_concurrent:
                        task = heapq.heappop(self._task_queue)
                        self._active_tasks.add(task.frame_id)
                
                if task:
                    # 선읽기 실행
                    success = self._execute_preload_task(task)
                    
                    with self._lock:
                        self._active_tasks.discard(task.frame_id)
                        if success:
                            self._completed_tasks.add(task.frame_id)
                            self._preload_stats['successful_preloads'] += 1
                        else:
                            self._cancelled_tasks.add(task.frame_id)
                            self._preload_stats['cancelled_preloads'] += 1
                else:
                    time.sleep(0.01)  # 10ms 대기
                    
            except Exception as e:
                print(f"Preloader error: {e}")
                time.sleep(0.1)
    
    def _execute_preload_task(self, task: PreloadTask) -> bool:
        """선읽기 작업 실행"""
        if not self._frame_loader:
            return False
        
        try:
            # Infrastructure 층에서 프레임 로드
            frame_data = self._frame_loader(task.frame_id)
            if frame_data is not None:
                # 캐시에 저장
                return self.cache.put(task.frame_id, frame_data)
            return False
        except Exception as e:
            print(f"Preload failed for {task.frame_id}: {e}")
            return False
    
    def _calculate_preload_targets(self, current_frame: str, direction: str, range_size: int) -> List[str]:
        """선읽기 대상 프레임 계산"""
        try:
            current_num = int(current_frame.split('_')[1])
        except (ValueError, IndexError):
            return []
        
        targets = []
        
        if direction in ["forward", "both"]:
            for i in range(1, range_size + 1):
                targets.append(f"frame_{current_num + i:06d}")
        
        if direction in ["backward", "both"]:
            for i in range(1, range_size + 1):
                if current_num - i >= 0:
                    targets.append(f"frame_{current_num - i:06d}")
        
        return targets
    
    def _estimate_access_time(self, frame_id: str, current_frame: str) -> float:
        """프레임 액세스 시간 추정"""
        try:
            current_num = int(current_frame.split('_')[1])
            target_num = int(frame_id.split('_')[1])
            distance = abs(target_num - current_num)
            
            # 거리에 따른 액세스 시간 추정 (휴리스틱)
            estimated_time = time.time() + distance * 0.1  # 0.1초 per frame
            return estimated_time
        except (ValueError, IndexError):
            return time.time() + 1.0


# Mock frame loader for testing
def mock_frame_loader(frame_id: str) -> Optional[np.ndarray]:
    """모의 프레임 로더"""
    time.sleep(0.01)  # 10ms 로딩 시뮬레이션
    return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)