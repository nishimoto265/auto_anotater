"""
Agent6 Cache Layer: 간단한 통합 테스트

핵심 기능 동작 확인
"""
import time
import pytest
import numpy as np

from src.cache_layer.frame_cache.lru_cache import LRUFrameCache
from src.cache_layer.frame_cache.memory_monitor import MemoryMonitor
from src.cache_layer.frame_cache.cache_optimizer import CacheOptimizer


class TestSimpleIntegration:
    """간단한 통합 테스트"""
    
    @pytest.fixture
    def integrated_system(self):
        """통합 시스템"""
        cache = LRUFrameCache(max_size=50, memory_limit=5 * 1024**3)
        memory_monitor = MemoryMonitor(cache, monitoring_interval=0.1)
        optimizer = CacheOptimizer(cache, memory_monitor)
        return cache, memory_monitor, optimizer
    
    @pytest.fixture  
    def test_frame_data(self):
        """테스트 프레임 데이터"""
        return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    def test_basic_cache_operations(self, integrated_system, test_frame_data):
        """기본 캐시 동작 확인"""
        cache, memory_monitor, optimizer = integrated_system
        
        # 프레임 저장
        result = cache.put("frame_000001", test_frame_data)
        assert result is True, "Frame put failed"
        
        # 프레임 조회
        retrieved_data = cache.get("frame_000001")
        assert retrieved_data is not None, "Frame get failed"
        assert retrieved_data.shape == test_frame_data.shape, "Shape mismatch"
        
        # 캐시 크기 확인
        assert cache.size() == 1, "Cache size incorrect"
        
        # 메모리 사용량 확인
        memory_usage = cache.get_memory_usage()
        assert memory_usage > 0, "Memory usage not tracked"
    
    def test_50ms_frame_switching(self, integrated_system, test_frame_data):
        """50ms 프레임 전환 테스트"""
        cache, memory_monitor, optimizer = integrated_system
        
        # 10개 프레임 사전 로드
        for i in range(10):
            cache.put(f"frame_{i:06d}", test_frame_data)
        
        # 100회 프레임 전환 테스트
        switching_times = []
        for i in range(100):
            frame_id = f"frame_{i % 10:06d}"
            
            start_time = time.perf_counter()
            frame_data = cache.get(frame_id)
            end_time = time.perf_counter()
            
            switching_time = (end_time - start_time) * 1000
            switching_times.append(switching_time)
            
            assert frame_data is not None, f"Frame {frame_id} not found"
            assert switching_time <= 50.0, f"Switching time exceeded 50ms: {switching_time:.2f}ms"
        
        # 평균 시간 확인
        avg_time = np.mean(switching_times)
        max_time = np.max(switching_times)
        
        print(f"Average switching time: {avg_time:.2f}ms")
        print(f"Maximum switching time: {max_time:.2f}ms")
        
        assert avg_time <= 10.0, f"Average switching time too high: {avg_time:.2f}ms"
        assert max_time <= 50.0, f"Maximum switching time exceeded: {max_time:.2f}ms"
    
    def test_memory_monitoring(self, integrated_system, test_frame_data):
        """메모리 모니터링 테스트"""
        cache, memory_monitor, optimizer = integrated_system
        
        # 메모리 상태 확인
        initial_status = memory_monitor.get_current_memory_status()
        assert initial_status.cache_memory_gb == 0.0, "Initial memory not zero"
        
        # 프레임 추가 후 메모리 확인
        cache.put("test_frame", test_frame_data)
        
        after_status = memory_monitor.get_current_memory_status()
        assert after_status.cache_memory_gb > 0.0, "Memory usage not tracked"
        
        # 메모리 통계 확인
        stats = memory_monitor.get_memory_statistics()
        assert 'current_cache_memory_gb' in stats, "Memory statistics missing"
        assert stats['current_cache_memory_gb'] > 0, "Memory statistics incorrect"
    
    def test_cache_optimizer(self, integrated_system, test_frame_data):
        """캐시 최적화 테스트"""
        cache, memory_monitor, optimizer = integrated_system
        
        # 프레임 전환 기록
        for i in range(20):
            frame_id = f"frame_{i:06d}"
            cache.put(frame_id, test_frame_data)
            
            # 프레임 전환 시간 기록
            start_time = time.perf_counter()
            cache.get(frame_id)
            end_time = time.perf_counter()
            
            switch_time = (end_time - start_time) * 1000
            optimizer.record_frame_switch_time(switch_time, frame_id)
        
        # 액세스 패턴 분석
        pattern_analysis = optimizer.analyze_access_patterns()
        assert 'pattern_type' in pattern_analysis, "Pattern analysis failed"
        
        # 최적화 통계 확인
        stats = optimizer.get_optimization_statistics()
        assert 'current_performance' in stats, "Optimization statistics missing"
        
        # 추천사항 확인
        recommendations = optimizer.get_optimization_recommendations()
        assert isinstance(recommendations, list), "Recommendations not generated"
    
    def test_lru_eviction(self, integrated_system, test_frame_data):
        """LRU 제거 정책 테스트"""
        cache, memory_monitor, optimizer = integrated_system
        
        # 캐시 제한 (3개)까지 채우기
        small_cache = LRUFrameCache(max_size=3, memory_limit=1024**3)
        
        # 3개 프레임 추가
        small_cache.put("frame_A", test_frame_data)
        small_cache.put("frame_B", test_frame_data)
        small_cache.put("frame_C", test_frame_data)
        
        assert small_cache.size() == 3, "Cache size incorrect"
        
        # frame_A 액세스 (최근 사용됨으로 표시)
        small_cache.get("frame_A")
        
        # 4번째 프레임 추가 (frame_B가 제거되어야 함)
        small_cache.put("frame_D", test_frame_data)
        
        assert small_cache.size() == 3, "Cache size should remain 3"
        assert small_cache.get("frame_B") is None, "LRU item not evicted"
        assert small_cache.get("frame_A") is not None, "Recently used item evicted"
        assert small_cache.get("frame_C") is not None, "Wrong item evicted"
        assert small_cache.get("frame_D") is not None, "New item not added"
    
    def test_hit_rate_calculation(self, integrated_system, test_frame_data):
        """히트율 계산 테스트"""
        cache, memory_monitor, optimizer = integrated_system
        
        # 초기 히트율 확인
        initial_hit_rate = cache.get_hit_rate()
        assert initial_hit_rate == 0.0, "Initial hit rate should be 0"
        
        # 프레임 추가
        cache.put("frame_001", test_frame_data)
        
        # 히트 발생
        cache.get("frame_001")  # Hit
        cache.get("frame_002")  # Miss
        cache.get("frame_001")  # Hit
        
        hit_rate = cache.get_hit_rate()
        expected_hit_rate = 2 / 3  # 2 hits out of 3 accesses
        
        assert abs(hit_rate - expected_hit_rate) < 0.01, f"Hit rate calculation incorrect: {hit_rate}"
    
    def test_performance_statistics(self, integrated_system, test_frame_data):
        """성능 통계 테스트"""
        cache, memory_monitor, optimizer = integrated_system
        
        # 몇 가지 작업 수행
        for i in range(5):
            cache.put(f"frame_{i:03d}", test_frame_data)
            cache.get(f"frame_{i:03d}")
        
        # 성능 통계 확인
        stats = cache.get_performance_stats()
        
        required_keys = [
            'hit_rate', 'memory_usage_gb', 'memory_usage_percent', 
            'cache_size', 'total_hits', 'total_misses'
        ]
        
        for key in required_keys:
            assert key in stats, f"Performance stat '{key}' missing"
        
        assert stats['cache_size'] == 5, "Cache size stat incorrect"
        assert stats['total_hits'] == 5, "Hit count incorrect"
        assert stats['memory_usage_gb'] > 0, "Memory usage stat incorrect"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])