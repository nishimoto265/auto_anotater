"""
Agent6 Cache Layer: 캐싱 전략

동적 캐시 사이즈 및 정책 최적화
"""
from typing import Dict, Any, Optional
from enum import Enum


class CacheStrategy(Enum):
    """캐시 전략 타입"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class CachingStrategy:
    """
    동적 캐싱 전략
    
    메모리 사용량과 성능을 균형 있게 관리
    """
    
    def __init__(self, initial_strategy: CacheStrategy = CacheStrategy.BALANCED):
        self.current_strategy = initial_strategy
        self._performance_history = []
    
    def recommend_cache_size(self, current_performance: Dict[str, Any]) -> int:
        """성능 기반 캐시 사이즈 추천"""
        base_size = 100
        
        hit_rate = current_performance.get('hit_rate', 0.9)
        memory_usage = current_performance.get('memory_usage_percent', 50)
        
        if self.current_strategy == CacheStrategy.CONSERVATIVE:
            if memory_usage > 80:
                return max(50, int(base_size * 0.7))
            return base_size
        elif self.current_strategy == CacheStrategy.AGGRESSIVE:
            if hit_rate < 0.9 and memory_usage < 70:
                return min(200, int(base_size * 1.5))
            return base_size
        else:  # BALANCED
            if hit_rate < 0.9 and memory_usage < 80:
                return min(150, int(base_size * 1.2))
            elif memory_usage > 85:
                return max(75, int(base_size * 0.8))
            return base_size
    
    def adapt_strategy(self, performance_metrics: Dict[str, Any]):
        """성능 메트릭 기반 전략 적응"""
        self._performance_history.append(performance_metrics)
        
        if len(self._performance_history) < 5:
            return
        
        # 최근 성능 추세 분석
        recent_hit_rates = [m.get('hit_rate', 0.9) for m in self._performance_history[-5:]]
        recent_memory_usage = [m.get('memory_usage_percent', 50) for m in self._performance_history[-5:]]
        
        avg_hit_rate = sum(recent_hit_rates) / len(recent_hit_rates)
        avg_memory_usage = sum(recent_memory_usage) / len(recent_memory_usage)
        
        # 전략 조정
        if avg_hit_rate < 0.85 and avg_memory_usage < 60:
            self.current_strategy = CacheStrategy.AGGRESSIVE
        elif avg_memory_usage > 90:
            self.current_strategy = CacheStrategy.CONSERVATIVE
        else:
            self.current_strategy = CacheStrategy.BALANCED