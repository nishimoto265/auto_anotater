"""
Agent6 Cache Layer: 선읽기 전략

지능형 패턴 분석 기반 최적화
"""
import time
import numpy as np
from typing import List, Dict, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class AccessPattern:
    """액세스 패턴 정보"""
    pattern_type: str
    confidence: float
    parameters: Dict[str, Any]


class PrefetchStrategy:
    """
    지능형 선읽기 전략
    
    기능:
    - 액세스 패턴 학습
    - 동적 범위 조정
    - 예측 기반 선읽기
    """
    
    def __init__(self, history_size: int = 100, prediction_window: int = 50):
        """
        Args:
            history_size: 히스토리 크기
            prediction_window: 예측 윈도우
        """
        self.history_size = history_size
        self.prediction_window = prediction_window
        
        # 액세스 히스토리
        self._access_history = deque(maxlen=history_size)
        self._hit_rate_history = deque(maxlen=50)
        
        # 패턴 분석 결과
        self._current_pattern: Optional[AccessPattern] = None
        self._hot_spots: Dict[str, int] = defaultdict(int)
        
        # 성능 통계
        self._prediction_accuracy = 0.0
        self._last_analysis_time = 0
    
    def record_access(self, frame_id: str):
        """액세스 기록"""
        timestamp = time.time()
        self._access_history.append((timestamp, frame_id))
        self._hot_spots[frame_id] += 1
    
    def record_hit_rate(self, hit_rate: float):
        """히트율 기록"""
        self._hit_rate_history.append(hit_rate)
    
    def predict_next_frames(self, current_frame: str, count: int = 10) -> List[str]:
        """다음 프레임 예측"""
        if not self._current_pattern:
            self._analyze_current_pattern()
        
        predictions = []
        
        if self._current_pattern:
            if self._current_pattern.pattern_type == 'sequential':
                predictions = self._predict_sequential(current_frame, count)
            elif self._current_pattern.pattern_type == 'jump':
                predictions = self._predict_jump(current_frame, count)
            elif self._current_pattern.pattern_type == 'hotspot':
                predictions = self._predict_hotspot(current_frame, count)
            else:  # random
                predictions = self._predict_random(current_frame, count)
        
        if len(predictions) < count:
            # 예측이 부족하면 순차 예측으로 보완
            remaining = count - len(predictions)
            sequential_predictions = self._predict_sequential(current_frame, remaining)
            predictions.extend(sequential_predictions)
        
        return predictions[:count]
    
    def get_hot_spots(self, threshold: int = 5) -> List[str]:
        """핫스팟 프레임 목록"""
        return [frame_id for frame_id, count in self._hot_spots.items() if count >= threshold]
    
    def calculate_optimal_range(self) -> int:
        """최적 선읽기 범위 계산"""
        if not self._current_pattern:
            return 25  # 기본값
        
        base_range = 25
        confidence = self._current_pattern.confidence
        
        if confidence < 0.5:
            return base_range
        
        pattern_type = self._current_pattern.pattern_type
        
        if pattern_type == 'sequential':
            return int(base_range * (1.0 + confidence * 0.5))  # 최대 37.5
        elif pattern_type == 'jump':
            return int(base_range * (1.0 + confidence * 0.3))  # 최대 32.5
        elif pattern_type == 'hotspot':
            return int(base_range * (0.8 + confidence * 0.2))  # 20-25
        else:  # random
            return int(base_range * (1.0 + confidence * 0.4))  # 최대 35
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """전략 통계"""
        avg_hit_rate = 0.0
        if self._hit_rate_history:
            avg_hit_rate = np.mean(self._hit_rate_history)
        
        return {
            'current_pattern': self._current_pattern.__dict__ if self._current_pattern else None,
            'prediction_accuracy': self._prediction_accuracy,
            'avg_hit_rate': avg_hit_rate,
            'hot_spots_count': len(self.get_hot_spots()),
            'access_history_size': len(self._access_history),
            'optimal_range': self.calculate_optimal_range()
        }
    
    # Private methods
    
    def _analyze_current_pattern(self):
        """현재 패턴 분석"""
        if len(self._access_history) < 10:
            return
        
        recent_accesses = list(self._access_history)[-30:]  # 최근 30개
        frame_sequence = [frame_id for _, frame_id in recent_accesses]
        
        # 각 패턴 스코어 계산
        sequential_score = self._calculate_sequential_score(frame_sequence)
        jump_score = self._calculate_jump_score(frame_sequence)
        hotspot_score = self._calculate_hotspot_score(frame_sequence)
        
        # 지배적 패턴 결정
        patterns = {
            'sequential': sequential_score,
            'jump': jump_score,
            'hotspot': hotspot_score
        }
        
        dominant_pattern = max(patterns, key=patterns.get)
        confidence = patterns[dominant_pattern]
        
        # 랜덤 패턴 체크 (모든 스코어가 낮으면)
        if confidence < 0.3:
            dominant_pattern = 'random'
            confidence = 1.0 - max(patterns.values())
        
        self._current_pattern = AccessPattern(
            pattern_type=dominant_pattern,
            confidence=confidence,
            parameters=patterns
        )
    
    def _calculate_sequential_score(self, frame_sequence: List[str]) -> float:
        """순차 패턴 스코어"""
        if len(frame_sequence) < 2:
            return 0.0
        
        sequential_count = 0
        total_transitions = len(frame_sequence) - 1
        
        for i in range(total_transitions):
            try:
                current_num = int(frame_sequence[i].split('_')[1])
                next_num = int(frame_sequence[i + 1].split('_')[1])
                if abs(next_num - current_num) == 1:
                    sequential_count += 1
            except (ValueError, IndexError):
                continue
        
        return sequential_count / total_transitions if total_transitions > 0 else 0.0
    
    def _calculate_jump_score(self, frame_sequence: List[str]) -> float:
        """점프 패턴 스코어"""
        if len(frame_sequence) < 3:
            return 0.0
        
        consistent_jumps = 0
        total_jumps = len(frame_sequence) - 2
        
        for i in range(total_jumps):
            try:
                num1 = int(frame_sequence[i].split('_')[1])
                num2 = int(frame_sequence[i + 1].split('_')[1])
                num3 = int(frame_sequence[i + 2].split('_')[1])
                
                jump1 = abs(num2 - num1)
                jump2 = abs(num3 - num2)
                
                if jump1 == jump2 and jump1 > 1:
                    consistent_jumps += 1
                    
            except (ValueError, IndexError):
                continue
        
        return consistent_jumps / total_jumps if total_jumps > 0 else 0.0
    
    def _calculate_hotspot_score(self, frame_sequence: List[str]) -> float:
        """핫스팟 패턴 스코어"""
        if len(frame_sequence) < 5:
            return 0.0
        
        frame_counts = defaultdict(int)
        for frame in frame_sequence:
            frame_counts[frame] += 1
        
        total_accesses = len(frame_sequence)
        unique_frames = len(frame_counts)
        
        if unique_frames <= 1:
            return 1.0
        
        # 상위 20% 프레임의 집중도
        sorted_counts = sorted(frame_counts.values(), reverse=True)
        top_20_percent = max(1, int(unique_frames * 0.2))
        top_accesses = sum(sorted_counts[:top_20_percent])
        
        return min(1.0, top_accesses / total_accesses)
    
    def _predict_sequential(self, current_frame: str, count: int) -> List[str]:
        """순차 예측"""
        try:
            current_num = int(current_frame.split('_')[1])
        except (ValueError, IndexError):
            return []
        
        predictions = []
        
        # 최근 방향 분석
        direction = self._analyze_recent_direction()
        
        if direction > 0:  # 전진
            for i in range(1, count + 1):
                predictions.append(f"frame_{current_num + i:06d}")
        elif direction < 0:  # 후진
            for i in range(1, count + 1):
                if current_num - i >= 0:
                    predictions.append(f"frame_{current_num - i:06d}")
        else:  # 양방향
            for i in range(1, count // 2 + 1):
                predictions.append(f"frame_{current_num + i:06d}")
                if current_num - i >= 0:
                    predictions.append(f"frame_{current_num - i:06d}")
        
        return predictions
    
    def _predict_jump(self, current_frame: str, count: int) -> List[str]:
        """점프 예측"""
        try:
            current_num = int(current_frame.split('_')[1])
        except (ValueError, IndexError):
            return []
        
        # 최근 점프 간격 분석
        jump_interval = self._analyze_jump_interval()
        if jump_interval == 0:
            return self._predict_sequential(current_frame, count)
        
        predictions = []
        for i in range(1, count + 1):
            next_num = current_num + jump_interval * i
            if next_num >= 0:
                predictions.append(f"frame_{next_num:06d}")
        
        return predictions
    
    def _predict_hotspot(self, current_frame: str, count: int) -> List[str]:
        """핫스팟 예측"""
        hot_spots = self.get_hot_spots()
        
        # 현재 프레임 주변의 핫스팟 우선
        try:
            current_num = int(current_frame.split('_')[1])
            hot_spots_with_distance = []
            
            for hot_spot in hot_spots:
                try:
                    hot_num = int(hot_spot.split('_')[1])
                    distance = abs(hot_num - current_num)
                    hot_spots_with_distance.append((distance, hot_spot))
                except (ValueError, IndexError):
                    continue
            
            # 거리순 정렬
            hot_spots_with_distance.sort()
            return [frame for _, frame in hot_spots_with_distance[:count]]
            
        except (ValueError, IndexError):
            return hot_spots[:count]
    
    def _predict_random(self, current_frame: str, count: int) -> List[str]:
        """랜덤 예측 (최근 액세스 기반)"""
        recent_frames = [frame_id for _, frame_id in list(self._access_history)[-20:]]
        
        # 최근 액세스된 프레임 중에서 선택
        unique_recent = list(set(recent_frames))
        
        if len(unique_recent) >= count:
            return unique_recent[:count]
        else:
            # 부족하면 순차 예측으로 보완
            remaining = count - len(unique_recent)
            sequential = self._predict_sequential(current_frame, remaining)
            return unique_recent + sequential
    
    def _analyze_recent_direction(self) -> int:
        """최근 이동 방향 분석"""
        if len(self._access_history) < 3:
            return 0
        
        recent_frames = [frame_id for _, frame_id in list(self._access_history)[-5:]]
        
        forward_moves = 0
        backward_moves = 0
        
        for i in range(len(recent_frames) - 1):
            try:
                current_num = int(recent_frames[i].split('_')[1])
                next_num = int(recent_frames[i + 1].split('_')[1])
                
                if next_num > current_num:
                    forward_moves += 1
                elif next_num < current_num:
                    backward_moves += 1
                    
            except (ValueError, IndexError):
                continue
        
        if forward_moves > backward_moves:
            return 1  # 전진
        elif backward_moves > forward_moves:
            return -1  # 후진
        else:
            return 0  # 양방향
    
    def _analyze_jump_interval(self) -> int:
        """점프 간격 분석"""
        if len(self._access_history) < 3:
            return 0
        
        recent_frames = [frame_id for _, frame_id in list(self._access_history)[-10:]]
        intervals = []
        
        for i in range(len(recent_frames) - 1):
            try:
                current_num = int(recent_frames[i].split('_')[1])
                next_num = int(recent_frames[i + 1].split('_')[1])
                interval = abs(next_num - current_num)
                if interval > 1:  # 점프로 간주
                    intervals.append(interval)
            except (ValueError, IndexError):
                continue
        
        if intervals:
            # 가장 빈번한 간격 반환
            return max(set(intervals), key=intervals.count)
        
        return 0