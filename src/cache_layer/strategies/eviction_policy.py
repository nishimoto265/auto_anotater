"""
Agent6 Cache Layer: 제거 정책

지능형 LRU 및 최적화된 제거 전략
"""
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class EvictionCandidate:
    """제거 후보"""
    frame_id: str
    last_access_time: float
    access_count: int
    size: int
    priority_score: float


class EvictionPolicy:
    """
    지능형 제거 정책
    
    단순 LRU를 넘어선 최적화된 제거 전략
    """
    
    def __init__(self):
        self._access_patterns = {}
        self._hotspot_threshold = 5
    
    def calculate_eviction_priority(self, frame_id: str, last_access_time: float, 
                                  access_count: int, size: int) -> float:
        """제거 우선순위 계산 (낮을수록 먼저 제거)"""
        current_time = time.time()
        time_since_access = current_time - last_access_time
        
        # 기본 LRU 스코어
        lru_score = time_since_access
        
        # 액세스 빈도 보정
        frequency_bonus = min(access_count / 10.0, 1.0)  # 최대 1.0
        
        # 사이즈 패널티 (큰 프레임은 먼저 제거)
        size_penalty = size / (50 * 1024 * 1024)  # 50MB 기준
        
        # 핫스팟 보정
        hotspot_bonus = 0.0
        if access_count >= self._hotspot_threshold:
            hotspot_bonus = 0.5
        
        # 최종 우선순위 (낮을수록 먼저 제거)
        priority = lru_score + size_penalty - frequency_bonus - hotspot_bonus
        
        return max(0.0, priority)
    
    def select_eviction_candidates(self, cache_items: List[Dict[str, Any]], 
                                 count: int) -> List[str]:
        """제거 후보 선택"""
        candidates = []
        
        for item in cache_items:
            priority = self.calculate_eviction_priority(
                item['frame_id'],
                item['last_access_time'],
                item.get('access_count', 1),
                item['size']
            )
            
            candidates.append(EvictionCandidate(
                frame_id=item['frame_id'],
                last_access_time=item['last_access_time'],
                access_count=item.get('access_count', 1),
                size=item['size'],
                priority_score=priority
            ))
        
        # 우선순위 순으로 정렬 (낮은 것부터)
        candidates.sort(key=lambda x: x.priority_score)
        
        return [candidate.frame_id for candidate in candidates[:count]]