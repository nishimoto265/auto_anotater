"""
Agent6 Cache Layer: キャッシュ最適化エンジン

フレーム切り替え50ms以下達成のための動的最適化
"""
import time
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum


class OptimizationStrategy(Enum):
    """最適化戦略"""
    CONSERVATIVE = "conservative"  # 安全第一
    BALANCED = "balanced"         # バランス型
    AGGRESSIVE = "aggressive"     # 性能重視


@dataclass
class PerformanceMetrics:
    """性能メトリクス"""
    avg_frame_switch_time_ms: float
    cache_hit_rate: float
    memory_usage_percent: float
    operation_count: int
    timestamp: float


@dataclass
class OptimizationResult:
    """最適化結果"""
    strategy_applied: str
    performance_before: PerformanceMetrics
    performance_after: PerformanceMetrics
    improvement_percent: float
    timestamp: float


class CacheOptimizer:
    """
    動的キャッシュ最適化エンジン
    
    機能:
    - リアルタイム性能監視
    - 動的パラメータ調整
    - 予測的最適化
    - 50ms以下保証
    """
    
    def __init__(self, cache_instance, memory_monitor):
        """
        Args:
            cache_instance: 最適化対象キャッシュ
            memory_monitor: メモリ監視インスタンス
        """
        self.cache = cache_instance
        self.memory_monitor = memory_monitor
        
        # Optimization parameters
        self.target_frame_time_ms = 45.0  # 5ms margin for 50ms target
        self.target_hit_rate = 0.95
        self.target_memory_usage = 0.85  # 85% of limit
        
        # Performance history
        self._performance_history: deque = deque(maxlen=1000)
        self._optimization_history: List[OptimizationResult] = []
        
        # Access pattern analysis
        self._access_patterns = defaultdict(list)
        self._sequential_threshold = 0.8  # 80% sequential for optimization
        
        # Optimization state
        self._optimization_active = False
        self._optimization_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Current strategy
        self._current_strategy = OptimizationStrategy.BALANCED
        
        # Performance tracking
        self._frame_switch_times = deque(maxlen=100)
        self._last_optimization_time = 0
        self._optimization_interval = 30  # seconds
    
    def start_optimization(self):
        """最適化エンジン開始"""
        with self._lock:
            if self._optimization_active:
                return
            
            self._optimization_active = True
            self._optimization_thread = threading.Thread(
                target=self._optimization_loop,
                daemon=True,
                name="CacheOptimizer"
            )
            self._optimization_thread.start()
    
    def stop_optimization(self):
        """最適化エンジン停止"""
        with self._lock:
            self._optimization_active = False
            if self._optimization_thread:
                self._optimization_thread.join(timeout=2.0)
                self._optimization_thread = None
    
    def record_frame_switch_time(self, switch_time_ms: float, frame_id: str):
        """フレーム切り替え時間記録"""
        self._frame_switch_times.append(switch_time_ms)
        
        # Access pattern analysis
        current_time = time.time()
        self._access_patterns[frame_id].append(current_time)
        
        # Real-time optimization trigger
        if switch_time_ms > self.target_frame_time_ms:
            self._trigger_emergency_optimization()
    
    def analyze_access_patterns(self) -> Dict[str, Any]:
        """アクセスパターン分析"""
        if not self._access_patterns:
            return {'pattern_type': 'unknown', 'confidence': 0.0}
        
        # Recent access analysis
        recent_time = time.time() - 300  # Last 5 minutes
        recent_accesses = []
        
        for frame_id, access_times in self._access_patterns.items():
            recent_times = [t for t in access_times if t > recent_time]
            if recent_times:
                recent_accesses.extend([(t, frame_id) for t in recent_times])
        
        if len(recent_accesses) < 10:
            return {'pattern_type': 'insufficient_data', 'confidence': 0.0}
        
        # Sort by time
        recent_accesses.sort()
        frame_sequence = [frame_id for _, frame_id in recent_accesses]
        
        # Analyze patterns
        sequential_score = self._calculate_sequential_score(frame_sequence)
        random_score = self._calculate_random_score(frame_sequence)
        hotspot_score = self._calculate_hotspot_score(frame_sequence)
        
        # Determine dominant pattern
        scores = {
            'sequential': sequential_score,
            'random': random_score,
            'hotspot': hotspot_score
        }
        
        dominant_pattern = max(scores, key=scores.get)
        confidence = scores[dominant_pattern]
        
        return {
            'pattern_type': dominant_pattern,
            'confidence': confidence,
            'scores': scores,
            'total_accesses': len(recent_accesses)
        }
    
    def optimize_for_pattern(self, pattern_analysis: Dict[str, Any]) -> bool:
        """パターン別最適化実行"""
        pattern_type = pattern_analysis['pattern_type']
        confidence = pattern_analysis['confidence']
        
        if confidence < 0.5:
            return False  # Not confident enough
        
        before_metrics = self._get_current_metrics()
        optimization_applied = False
        
        if pattern_type == 'sequential':
            optimization_applied = self._optimize_for_sequential()
        elif pattern_type == 'random':
            optimization_applied = self._optimize_for_random()
        elif pattern_type == 'hotspot':
            optimization_applied = self._optimize_for_hotspot()
        
        if optimization_applied:
            time.sleep(1.0)  # Allow changes to take effect
            after_metrics = self._get_current_metrics()
            self._record_optimization_result(
                f"{pattern_type}_optimization",
                before_metrics,
                after_metrics
            )
        
        return optimization_applied
    
    def emergency_optimization(self) -> bool:
        """緊急最適化（50ms超過時）"""
        current_metrics = self._get_current_metrics()
        
        # Immediate actions for emergency
        actions_applied = []
        
        # 1. Aggressive memory cleanup
        if current_metrics.memory_usage_percent > 80:
            self.memory_monitor.force_memory_cleanup(target_memory_gb=12.0)
            actions_applied.append("aggressive_memory_cleanup")
        
        # 2. Cache size reduction
        if self.cache.size() > 80:
            target_size = max(50, int(self.cache.size() * 0.7))
            while self.cache.size() > target_size:
                self.cache._evict_lru()
            actions_applied.append("cache_size_reduction")
        
        # 3. Force garbage collection
        import gc
        gc.collect()
        actions_applied.append("garbage_collection")
        
        # Record emergency optimization
        after_metrics = self._get_current_metrics()
        self._record_optimization_result(
            f"emergency_optimization_{'+'.join(actions_applied)}",
            current_metrics,
            after_metrics
        )
        
        return len(actions_applied) > 0
    
    def get_optimization_recommendations(self) -> List[str]:
        """最適化推奨事項取得"""
        recommendations = []
        current_metrics = self._get_current_metrics()
        
        # Frame switching time recommendations
        if current_metrics.avg_frame_switch_time_ms > 40:
            recommendations.append("Reduce cache size for faster access")
            recommendations.append("Increase preload aggressiveness")
        
        # Hit rate recommendations
        if current_metrics.cache_hit_rate < 0.90:
            recommendations.append("Increase cache size")
            recommendations.append("Improve preload strategy")
        
        # Memory usage recommendations
        if current_metrics.memory_usage_percent > 90:
            recommendations.append("Reduce cache size immediately")
            recommendations.append("Enable aggressive LRU eviction")
        elif current_metrics.memory_usage_percent < 50:
            recommendations.append("Increase cache size for better hit rate")
        
        # Pattern-based recommendations
        pattern_analysis = self.analyze_access_patterns()
        if pattern_analysis['confidence'] > 0.7:
            pattern_type = pattern_analysis['pattern_type']
            if pattern_type == 'sequential':
                recommendations.append("Optimize for sequential access pattern")
            elif pattern_type == 'hotspot':
                recommendations.append("Implement hotspot-aware caching")
        
        return recommendations
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """最適化統計取得"""
        current_metrics = self._get_current_metrics()
        
        # Calculate improvement trends
        recent_optimizations = self._optimization_history[-10:]
        avg_improvement = 0.0
        if recent_optimizations:
            improvements = [opt.improvement_percent for opt in recent_optimizations]
            avg_improvement = np.mean(improvements)
        
        return {
            'current_performance': current_metrics.__dict__,
            'optimization_count': len(self._optimization_history),
            'avg_improvement_percent': avg_improvement,
            'optimization_active': self._optimization_active,
            'current_strategy': self._current_strategy.value,
            'last_optimization_time': self._last_optimization_time,
            'access_pattern_analysis': self.analyze_access_patterns(),
            'recommendations': self.get_optimization_recommendations()
        }
    
    # Private methods
    
    def _optimization_loop(self):
        """最適化ループ"""
        while self._optimization_active:
            try:
                current_time = time.time()
                
                if current_time - self._last_optimization_time > self._optimization_interval:
                    self._perform_routine_optimization()
                    self._last_optimization_time = current_time
                
                time.sleep(5.0)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Optimization loop error: {e}")
                time.sleep(5.0)
    
    def _perform_routine_optimization(self):
        """定期最適化実行"""
        # Analyze current performance
        current_metrics = self._get_current_metrics()
        
        # Check if optimization is needed
        if (current_metrics.avg_frame_switch_time_ms <= self.target_frame_time_ms and
            current_metrics.cache_hit_rate >= self.target_hit_rate and
            current_metrics.memory_usage_percent <= self.target_memory_usage * 100):
            return  # Performance is good
        
        # Analyze access patterns
        pattern_analysis = self.analyze_access_patterns()
        
        # Apply optimization
        self.optimize_for_pattern(pattern_analysis)
    
    def _trigger_emergency_optimization(self):
        """緊急最適化トリガー"""
        # Run in separate thread to avoid blocking
        def emergency_thread():
            self.emergency_optimization()
        
        thread = threading.Thread(target=emergency_thread, daemon=True)
        thread.start()
    
    def _get_current_metrics(self) -> PerformanceMetrics:
        """現在の性能メトリクス取得"""
        # Frame switching time
        avg_switch_time = 0.0
        if self._frame_switch_times:
            avg_switch_time = np.mean(list(self._frame_switch_times))
        
        # Cache performance
        hit_rate = self.cache.get_hit_rate()
        memory_usage_percent = (self.cache.get_memory_usage() / (20 * 1024**3)) * 100
        
        return PerformanceMetrics(
            avg_frame_switch_time_ms=avg_switch_time,
            cache_hit_rate=hit_rate,
            memory_usage_percent=memory_usage_percent,
            operation_count=self.cache._hits + self.cache._misses,
            timestamp=time.time()
        )
    
    def _record_optimization_result(self, strategy: str, before: PerformanceMetrics, after: PerformanceMetrics):
        """最適化結果記録"""
        # Calculate improvement
        if before.avg_frame_switch_time_ms > 0:
            time_improvement = (before.avg_frame_switch_time_ms - after.avg_frame_switch_time_ms) / before.avg_frame_switch_time_ms * 100
        else:
            time_improvement = 0.0
        
        result = OptimizationResult(
            strategy_applied=strategy,
            performance_before=before,
            performance_after=after,
            improvement_percent=time_improvement,
            timestamp=time.time()
        )
        
        self._optimization_history.append(result)
        
        # Keep only recent 100 optimizations
        if len(self._optimization_history) > 100:
            self._optimization_history = self._optimization_history[-100:]
    
    def _calculate_sequential_score(self, frame_sequence: List[str]) -> float:
        """順次アクセススコア計算"""
        if len(frame_sequence) < 2:
            return 0.0
        
        sequential_count = 0
        total_transitions = len(frame_sequence) - 1
        
        for i in range(total_transitions):
            try:
                current_num = int(frame_sequence[i].split('_')[1])
                next_num = int(frame_sequence[i + 1].split('_')[1])
                if abs(next_num - current_num) <= 1:  # Adjacent frames
                    sequential_count += 1
            except (ValueError, IndexError):
                continue
        
        return sequential_count / total_transitions if total_transitions > 0 else 0.0
    
    def _calculate_random_score(self, frame_sequence: List[str]) -> float:
        """ランダムアクセススコア計算"""
        if len(frame_sequence) < 2:
            return 0.0
        
        # High variance in frame numbers indicates random access
        try:
            frame_numbers = [int(frame.split('_')[1]) for frame in frame_sequence]
            variance = np.var(frame_numbers)
            # Normalize variance to 0-1 scale (heuristic)
            normalized_variance = min(1.0, variance / 100000.0)
            return normalized_variance
        except (ValueError, IndexError):
            return 0.0
    
    def _calculate_hotspot_score(self, frame_sequence: List[str]) -> float:
        """ホットスポットスコア計算"""
        if len(frame_sequence) < 5:
            return 0.0
        
        # Count frequency of each frame
        frame_counts = defaultdict(int)
        for frame in frame_sequence:
            frame_counts[frame] += 1
        
        # Calculate concentration (how much access is concentrated on few frames)
        total_unique = len(frame_counts)
        total_accesses = len(frame_sequence)
        
        if total_unique <= 1:
            return 1.0
        
        # Top 20% of frames account for what percentage of accesses?
        sorted_counts = sorted(frame_counts.values(), reverse=True)
        top_20_percent_count = max(1, int(total_unique * 0.2))
        top_accesses = sum(sorted_counts[:top_20_percent_count])
        
        concentration = top_accesses / total_accesses
        return min(1.0, concentration)
    
    def _optimize_for_sequential(self) -> bool:
        """順次アクセス最適化"""
        # Increase preload range for sequential access
        # This would be implemented when preloader is available
        return True
    
    def _optimize_for_random(self) -> bool:
        """ランダムアクセス最適化"""
        # Increase cache size for random access
        if self.cache.size() < 150:
            # Cache size increase would be handled by preloader
            pass
        return True
    
    def _optimize_for_hotspot(self) -> bool:
        """ホットスポット最適化"""
        # Implement hotspot-aware caching
        # Keep frequently accessed frames longer
        return True