"""
Agent6 Cache Layer: Cache Agent 통합 테스트

50ms 프레임 전환 절대 달성 검증
"""
import time
import pytest
import numpy as np

from src.cache_layer.cache_agent import CacheAgent, create_cache_agent
from src.cache_layer.interfaces.infrastructure_interface import MockInfrastructureInterface
from src.cache_layer.interfaces.data_bus_interface import MockDataBusInterface


class TestCacheAgent:
    """Cache Agent 통합 테스트"""
    
    @pytest.fixture
    def cache_agent(self):
        """테스트용 Cache Agent"""
        infrastructure = MockInfrastructureInterface(load_delay_ms=1.0)  # 1ms로 단축
        data_bus = MockDataBusInterface()
        
        agent = CacheAgent(
            max_cache_size=50,
            memory_limit_gb=5.0,
            infrastructure_interface=infrastructure,
            data_bus_interface=data_bus
        )
        
        agent.start()
        yield agent
        agent.stop()
    
    @pytest.fixture
    def test_frames(self):
        """테스트 프레임 목록"""
        return [f"frame_{i:06d}" for i in range(100)]
    
    def test_agent_lifecycle(self):
        """에이전트 생명주기 테스트"""
        agent = create_cache_agent(memory_limit_gb=1.0, cache_size=10)
        
        # 시작 전 상태
        assert not agent._running
        
        # 시작
        agent.start()
        assert agent._running
        
        # 정지
        agent.stop()
        assert not agent._running
    
    def test_50ms_frame_switching_guarantee(self, cache_agent, test_frames):
        """50ms 프레임 전환 절대 보장 테스트"""
        switching_times = []
        
        # 1000회 프레임 전환 테스트
        for i in range(1000):
            frame_id = test_frames[i % len(test_frames)]
            
            start_time = time.perf_counter()
            frame_data = cache_agent.get_frame(frame_id)
            end_time = time.perf_counter()
            
            switching_time = (end_time - start_time) * 1000
            switching_times.append(switching_time)
            
            # 각 전환이 50ms 이하인지 확인
            assert switching_time <= 50.0, f"Frame switching exceeded 50ms: {switching_time:.2f}ms"
            assert frame_data is not None, f"Frame {frame_id} not loaded"
            assert frame_data.shape == (1080, 1920, 3), "Frame shape incorrect"
        
        # 통계 검증
        avg_time = np.mean(switching_times)
        max_time = np.max(switching_times)
        p99_time = np.percentile(switching_times, 99)
        
        print(f"Frame switching performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")
        print(f"  99th percentile: {p99_time:.2f}ms")
        
        # 성능 기준 확인
        assert avg_time <= 30.0, f"Average switching time too high: {avg_time:.2f}ms"
        assert max_time <= 50.0, f"Maximum switching time exceeded: {max_time:.2f}ms"
        assert p99_time <= 45.0, f"99th percentile too high: {p99_time:.2f}ms"
    
    def test_cache_hit_rate_95_percent(self, cache_agent, test_frames):
        """95% 이상 캐시 히트율 테스트"""
        # 순차 액세스 패턴 (캐시 친화적)
        access_pattern = []
        for _ in range(10):  # 10회 반복
            for i in range(25):  # 전진
                access_pattern.append(test_frames[i])
            for i in range(24, -1, -1):  # 후진
                access_pattern.append(test_frames[i])
        
        # 액세스 실행
        for frame_id in access_pattern:
            frame_data = cache_agent.get_frame(frame_id)
            assert frame_data is not None
        
        # 히트율 확인
        stats = cache_agent.get_cache_statistics()
        hit_rate = stats['cache']['hit_rate']
        
        print(f"Cache hit rate: {hit_rate:.1%}")
        assert hit_rate >= 0.95, f"Hit rate too low: {hit_rate:.1%}"
    
    def test_memory_limit_enforcement(self, cache_agent):
        """메모리 한도 준수 테스트"""
        # 대량 프레임 추가하여 메모리 한도 테스트
        large_frames = [f"frame_{i:06d}" for i in range(500)]
        
        for frame_id in large_frames:
            frame_data = cache_agent.get_frame(frame_id)
            
            # 메모리 사용량 확인
            stats = cache_agent.get_cache_statistics()
            memory_usage_gb = stats['memory']['current_cache_memory_gb']
            
            assert memory_usage_gb <= 5.0, f"Memory limit exceeded: {memory_usage_gb:.2f}GB"
    
    def test_preloader_functionality(self, cache_agent, test_frames):
        """프리로더 기능 테스트"""
        current_frame = test_frames[50]
        
        # 수동 선읽기 실행
        result = cache_agent.preload_frames(current_frame, direction="both")
        assert result is True, "Preload request failed"
        
        # 잠시 대기 (선읽기 완료)
        time.sleep(0.5)
        
        # 선읽기된 프레임들이 캐시에 있는지 확인
        hit_count = 0
        test_range = 10  # 전후 10프레임 확인
        
        for i in range(-test_range, test_range + 1):
            frame_num = 50 + i
            if 0 <= frame_num < len(test_frames):
                frame_id = test_frames[frame_num]
                
                start_time = time.perf_counter()
                frame_data = cache_agent.cache.get(frame_id)
                end_time = time.perf_counter()
                
                if frame_data is not None:
                    hit_count += 1
                    access_time = (end_time - start_time) * 1000
                    assert access_time <= 5.0, f"Cache access too slow: {access_time:.2f}ms"
        
        # 선읽기 효율성 확인
        preload_efficiency = hit_count / (test_range * 2 + 1)
        print(f"Preload efficiency: {preload_efficiency:.1%}")
        assert preload_efficiency >= 0.3, f"Preload efficiency too low: {preload_efficiency:.1%}"
    
    def test_event_publishing(self, cache_agent, test_frames):
        """이벤트 발행 테스트"""
        # 이벤트 히스토리 클리어
        cache_agent.data_bus.clear_history()
        
        # 몇 개 프레임 액세스
        for i in range(5):
            cache_agent.get_frame(test_frames[i])
        
        # 이벤트 히스토리 확인
        events = cache_agent.data_bus.get_event_history()
        assert len(events) > 0, "No events published"
        
        # 프레임 변경 이벤트 확인
        frame_changed_events = [e for e in events if e.event_type.value == "frame_changed"]
        assert len(frame_changed_events) >= 3, "Frame changed events not published"
        
        # 캐시 관련 이벤트 확인
        cache_events = [e for e in events if e.event_type.value in ["cache_hit", "cache_miss"]]
        assert len(cache_events) >= 5, "Cache events not published"
    
    def test_performance_monitoring(self, cache_agent, test_frames):
        """성능 모니터링 테스트"""
        # 프레임 액세스 수행
        for i in range(10):
            cache_agent.get_frame(test_frames[i])
        
        # 통계 확인
        stats = cache_agent.get_cache_statistics()
        
        # 필수 통계 항목 확인
        assert 'cache' in stats
        assert 'memory' in stats
        assert 'optimizer' in stats
        assert 'preloader' in stats
        assert 'performance' in stats
        
        # 성능 메트릭 확인
        perf_stats = stats['performance']
        assert perf_stats['total_frame_switches'] == 10
        assert perf_stats['avg_frame_switch_time_ms'] <= 50.0
        assert perf_stats['running'] is True
    
    def test_cache_optimization(self, cache_agent, test_frames):
        """캐시 최적화 테스트"""
        # 최적화 전 상태 기록
        initial_stats = cache_agent.get_cache_statistics()
        
        # 일부 액세스 패턴 생성
        for i in range(20):
            cache_agent.get_frame(test_frames[i % 10])  # 반복 패턴
        
        # 수동 최적화 실행
        optimization_result = cache_agent.optimize_cache()
        assert optimization_result is True, "Optimization failed"
        
        # 최적화 후 상태 확인
        optimized_stats = cache_agent.get_cache_statistics()
        
        # 최적화기가 동작했는지 확인
        optimizer_stats = optimized_stats['optimizer']
        assert 'optimization_count' in optimizer_stats
    
    def test_context_manager(self, test_frames):
        """Context Manager 테스트"""
        infrastructure = MockInfrastructureInterface(load_delay_ms=10.0)
        data_bus = MockDataBusInterface()
        
        with CacheAgent(
            max_cache_size=20,
            memory_limit_gb=1.0,
            infrastructure_interface=infrastructure,
            data_bus_interface=data_bus
        ) as agent:
            # 에이전트가 시작된 상태
            assert agent._running is True
            
            # 프레임 액세스 테스트
            frame_data = agent.get_frame(test_frames[0])
            assert frame_data is not None
        
        # Context manager 종료 후 에이전트가 정지된 상태
        assert agent._running is False
    
    def test_concurrent_access(self, cache_agent, test_frames):
        """동시 액세스 테스트"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def access_frames(start_idx: int, count: int):
            access_times = []
            for i in range(count):
                frame_id = test_frames[(start_idx + i) % len(test_frames)]
                
                start_time = time.perf_counter()
                frame_data = cache_agent.get_frame(frame_id)
                end_time = time.perf_counter()
                
                access_time = (end_time - start_time) * 1000
                access_times.append(access_time)
                
                assert frame_data is not None
                assert access_time <= 50.0, f"Concurrent access too slow: {access_time:.2f}ms"
            
            results_queue.put(access_times)
        
        # 3개 스레드에서 동시 액세스
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=access_frames,
                args=(i * 10, 20)
            )
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 결과 검증
        all_times = []
        while not results_queue.empty():
            thread_times = results_queue.get()
            all_times.extend(thread_times)
        
        assert len(all_times) == 60, "Not all accesses completed"
        
        max_concurrent_time = max(all_times)
        avg_concurrent_time = np.mean(all_times)
        
        print(f"Concurrent access performance:")
        print(f"  Average: {avg_concurrent_time:.2f}ms")
        print(f"  Maximum: {max_concurrent_time:.2f}ms")
        
        assert max_concurrent_time <= 50.0, f"Concurrent access exceeded 50ms"
        assert avg_concurrent_time <= 25.0, f"Average concurrent time too high"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])