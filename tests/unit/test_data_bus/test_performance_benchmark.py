"""
Performance Benchmark Test
1ms通信目標達成確認・総合性能テスト
"""
import pytest
import time
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from data_bus.event_bus.event_dispatcher import EventDispatcher
from data_bus.message_queue.queue_manager import QueueManager  
from data_bus.interfaces.layer_interface import LayerInterface
from data_bus.event_bus.event_types import EVENT_FRAME_CHANGED, EVENT_BB_CREATED


class TestPerformanceBenchmark:
    """総合性能ベンチマーク"""
    
    def setup_method(self):
        """ベンチマーク環境セットアップ"""
        # コンポーネント初期化
        self.event_dispatcher = EventDispatcher(max_workers=8)
        self.queue_manager = QueueManager(max_workers=8)
        
        # テスト用Agent作成
        self.agents = {}
        agent_names = ['cache_layer', 'presentation', 'application', 'domain']
        
        for agent_name in agent_names:
            self.agents[agent_name] = LayerInterface(agent_name)
        
        # 高速サービス登録
        self._register_performance_services()
        
        # 統計リセット
        self.event_dispatcher.reset_stats()
        self.queue_manager.reset_stats()
        
        print("Performance benchmark environment initialized")
    
    def teardown_method(self):
        """ベンチマーク環境クリーンアップ"""
        for agent in self.agents.values():
            agent.shutdown()
        self.event_dispatcher.shutdown()
        self.queue_manager.shutdown()
    
    def _register_performance_services(self):
        """性能テスト用サービス登録"""
        # 高速フレーム取得（Cache Layer）
        def fast_get_frame(frame_id):
            return {'frame_data': f'data_{frame_id}', 'size': 1920*1080*3}
        
        # 軽量BB作成（Application Layer）
        def lightweight_create_bb(x, y, w, h):
            return {'bb_id': f'bb_{int(time.perf_counter()*1000000)}', 'coords': [x, y, w, h]}
        
        # 高速座標変換（Domain Layer）
        def fast_transform(coords):
            return {'transformed': [c * 0.5 for c in coords]}
        
        # 軽量描画更新（Presentation Layer）
        def quick_render(data):
            return {'rendered': True, 'objects': len(data) if isinstance(data, list) else 1}
        
        self.agents['cache_layer'].register_service('fast_get_frame', fast_get_frame, timeout=50)
        self.agents['application'].register_service('lightweight_create_bb', lightweight_create_bb, timeout=10)
        self.agents['domain'].register_service('fast_transform', fast_transform, timeout=1)
        self.agents['presentation'].register_service('quick_render', quick_render, timeout=16)
    
    def test_event_dispatch_1ms_target(self):
        """イベント配信1ms目標達成確認"""
        print("\n=== Event Dispatch 1ms Target Test ===")
        
        # 購読者設定
        received_count = 0
        def fast_callback(event):
            nonlocal received_count
            received_count += 1
        
        subscription_id = self.event_dispatcher.subscribe(EVENT_FRAME_CHANGED, fast_callback)
        
        # 1000回のイベント配信測定
        times = []
        for i in range(1000):
            start_time = time.perf_counter()
            
            success = self.event_dispatcher.publish(
                EVENT_FRAME_CHANGED,
                {'frame_id': f'{i:06d}', 'timestamp': time.perf_counter()},
                'benchmark_test'
            )
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # ms
            times.append(execution_time)
            
            assert success, f"Event dispatch failed at iteration {i}"
        
        # 統計分析
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95%ile
        p99_time = statistics.quantiles(times, n=100)[98]  # 99%ile
        max_time = max(times)
        min_time = min(times)
        
        # 1ms目標確認
        assert avg_time < 1.0, f"Average event dispatch time {avg_time:.3f}ms exceeds 1ms target"
        assert p95_time < 1.5, f"95%ile event dispatch time {p95_time:.3f}ms exceeds 1.5ms"
        assert p99_time < 2.0, f"99%ile event dispatch time {p99_time:.3f}ms exceeds 2ms"
        
        # 結果出力
        print(f"Event Dispatch Performance:")
        print(f"  Average: {avg_time:.3f}ms")
        print(f"  Median:  {median_time:.3f}ms")
        print(f"  95%ile:  {p95_time:.3f}ms")
        print(f"  99%ile:  {p99_time:.3f}ms")
        print(f"  Min:     {min_time:.3f}ms")
        print(f"  Max:     {max_time:.3f}ms")
        print(f"  Target:  1.000ms - {'✓ PASS' if avg_time < 1.0 else '✗ FAIL'}")
    
    def test_message_transfer_1ms_target(self):
        """メッセージ転送1ms目標達成確認"""
        print("\n=== Message Transfer 1ms Target Test ===")
        
        # 1000回のメッセージ転送測定
        times = []
        for i in range(1000):
            start_time = time.perf_counter()
            
            result = self.agents['application'].call_service(
                'domain', 'fast_transform',
                coords=[100+i, 200+i, 50, 80]
            )
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # ms
            times.append(execution_time)
            
            assert result is not None, f"Message transfer failed at iteration {i}"
        
        # 統計分析
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        p99_time = statistics.quantiles(times, n=100)[98]
        max_time = max(times)
        min_time = min(times)
        
        # 1ms目標確認
        assert avg_time < 1.0, f"Average message transfer time {avg_time:.3f}ms exceeds 1ms target"
        assert p95_time < 2.0, f"95%ile message transfer time {p95_time:.3f}ms exceeds 2ms"
        assert p99_time < 5.0, f"99%ile message transfer time {p99_time:.3f}ms exceeds 5ms"
        
        # 結果出力
        print(f"Message Transfer Performance:")
        print(f"  Average: {avg_time:.3f}ms")
        print(f"  Median:  {median_time:.3f}ms")
        print(f"  95%ile:  {p95_time:.3f}ms")
        print(f"  99%ile:  {p99_time:.3f}ms")
        print(f"  Min:     {min_time:.3f}ms")
        print(f"  Max:     {max_time:.3f}ms")
        print(f"  Target:  1.000ms - {'✓ PASS' if avg_time < 1.0 else '✗ FAIL'}")
    
    def test_cache_layer_50ms_target(self):
        """Cache Layer 50ms目標達成確認（最重要）"""
        print("\n=== Cache Layer 50ms Target Test ===")
        
        # フレーム取得性能測定
        frame_times = []
        for i in range(500):
            start_time = time.perf_counter()
            
            frame_data = self.agents['cache_layer'].call_service(
                'cache_layer', 'fast_get_frame',
                frame_id=f'{i:06d}'
            )
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # ms
            frame_times.append(execution_time)
            
            assert frame_data is not None, f"Frame retrieval failed at frame {i}"
        
        # 統計分析
        avg_time = statistics.mean(frame_times)
        median_time = statistics.median(frame_times)
        p95_time = statistics.quantiles(frame_times, n=20)[18]
        p99_time = statistics.quantiles(frame_times, n=100)[98]
        max_time = max(frame_times)
        
        # 50ms目標確認（最重要要件）
        assert avg_time < 50.0, f"Average frame retrieval time {avg_time:.3f}ms exceeds 50ms target"
        assert p95_time < 50.0, f"95%ile frame retrieval time {p95_time:.3f}ms exceeds 50ms"
        assert p99_time < 50.0, f"99%ile frame retrieval time {p99_time:.3f}ms exceeds 50ms"
        assert max_time < 50.0, f"Max frame retrieval time {max_time:.3f}ms exceeds 50ms"
        
        # 30ms以下の割合確認
        under_30ms = [t for t in frame_times if t < 30.0]
        fast_ratio = len(under_30ms) / len(frame_times)
        
        assert fast_ratio >= 0.95, f"Fast response ratio {fast_ratio:.2%} below 95%"
        
        # 結果出力
        print(f"Cache Layer Performance:")
        print(f"  Average: {avg_time:.3f}ms")
        print(f"  Median:  {median_time:.3f}ms")
        print(f"  95%ile:  {p95_time:.3f}ms")
        print(f"  99%ile:  {p99_time:.3f}ms")
        print(f"  Max:     {max_time:.3f}ms")
        print(f"  <30ms:   {fast_ratio:.1%}")
        print(f"  Target:  50.000ms - {'✓ PASS' if max_time < 50.0 else '✗ FAIL'}")
    
    def test_communication_overhead_5_percent(self):
        """通信オーバーヘッド5%以下確認"""
        print("\n=== Communication Overhead 5% Target Test ===")
        
        # ベースライン処理時間測定（通信なし）
        baseline_times = []
        for i in range(500):
            start_time = time.perf_counter()
            
            # ローカル処理のみ
            coords = [100+i, 200+i, 50, 80]
            result = {'transformed': [c * 0.5 for c in coords]}
            
            end_time = time.perf_counter()
            baseline_times.append((end_time - start_time) * 1000)
        
        baseline_avg = statistics.mean(baseline_times)
        
        # 通信ありの処理時間測定
        communication_times = []
        for i in range(500):
            start_time = time.perf_counter()
            
            # Agent間通信あり
            result = self.agents['application'].call_service(
                'domain', 'fast_transform',
                coords=[100+i, 200+i, 50, 80]
            )
            
            end_time = time.perf_counter()
            communication_times.append((end_time - start_time) * 1000)
        
        communication_avg = statistics.mean(communication_times)
        
        # オーバーヘッド計算
        if baseline_avg > 0:
            overhead_ratio = (communication_avg - baseline_avg) / communication_avg
        else:
            overhead_ratio = 0.95  # ベースラインがゼロの場合は保守的に95%とする
        
        overhead_percent = overhead_ratio * 100
        
        # 5%以下確認
        assert overhead_percent < 5.0, f"Communication overhead {overhead_percent:.2f}% exceeds 5% target"
        
        # 結果出力
        print(f"Communication Overhead:")
        print(f"  Baseline avg:     {baseline_avg:.3f}ms")
        print(f"  Communication avg: {communication_avg:.3f}ms")
        print(f"  Overhead:         {overhead_percent:.2f}%")
        print(f"  Target:           5.00% - {'✓ PASS' if overhead_percent < 5.0 else '✗ FAIL'}")
    
    def test_concurrent_performance_degradation(self):
        """並行処理時の性能劣化確認"""
        print("\n=== Concurrent Performance Degradation Test ===")
        
        # 単一スレッド性能測定
        single_thread_times = []
        for i in range(100):
            start_time = time.perf_counter()
            
            # 複数操作の組み合わせ
            frame_data = self.agents['cache_layer'].call_service(
                'cache_layer', 'fast_get_frame', frame_id=f'{i:06d}'
            )
            bb_data = self.agents['application'].call_service(
                'application', 'lightweight_create_bb', x=100, y=200, w=50, h=80
            )
            
            end_time = time.perf_counter()
            single_thread_times.append((end_time - start_time) * 1000)
        
        single_thread_avg = statistics.mean(single_thread_times)
        
        # 並行スレッド性能測定
        concurrent_times = []
        results_lock = threading.Lock()
        
        def concurrent_task(task_id):
            task_times = []
            for i in range(25):  # 25操作 × 4スレッド = 100操作
                start_time = time.perf_counter()
                
                frame_data = self.agents['cache_layer'].call_service(
                    'cache_layer', 'fast_get_frame', frame_id=f'{task_id}_{i:03d}'
                )
                bb_data = self.agents['application'].call_service(
                    'application', 'lightweight_create_bb', x=100+i, y=200+i, w=50, h=80
                )
                
                end_time = time.perf_counter()
                task_times.append((end_time - start_time) * 1000)
            
            with results_lock:
                concurrent_times.extend(task_times)
            
            return task_times
        
        # 4スレッドで並行実行
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for task_id in range(4):
                future = executor.submit(concurrent_task, task_id)
                futures.append(future)
            
            for future in futures:
                future.result()
        
        concurrent_avg = statistics.mean(concurrent_times)
        
        # 性能劣化確認
        degradation_ratio = (concurrent_avg - single_thread_avg) / single_thread_avg
        degradation_percent = degradation_ratio * 100
        
        # 20%以下の劣化を許容
        assert degradation_percent < 20.0, f"Performance degradation {degradation_percent:.2f}% exceeds 20%"
        
        # 結果出力
        print(f"Performance Degradation:")
        print(f"  Single thread avg: {single_thread_avg:.3f}ms")
        print(f"  Concurrent avg:    {concurrent_avg:.3f}ms")
        print(f"  Degradation:       {degradation_percent:.2f}%")
        print(f"  Target:            20.00% - {'✓ PASS' if degradation_percent < 20.0 else '✗ FAIL'}")
    
    def test_stress_test_stability(self):
        """ストレステスト安定性確認"""
        print("\n=== Stress Test Stability ===")
        
        # 高負荷テスト（5分間相当）
        operation_count = 2000
        error_count = 0
        times = []
        
        start_time = time.perf_counter()
        
        for i in range(operation_count):
            try:
                op_start = time.perf_counter()
                
                # ランダムな操作実行
                if i % 3 == 0:
                    result = self.agents['cache_layer'].call_service(
                        'cache_layer', 'fast_get_frame', frame_id=f'{i:06d}'
                    )
                elif i % 3 == 1:
                    result = self.agents['application'].call_service(
                        'application', 'lightweight_create_bb', x=100+i%500, y=200+i%500, w=50, h=80
                    )
                else:
                    result = self.agents['domain'].call_service(
                        'domain', 'fast_transform', coords=[100+i%500, 200+i%500, 50, 80]
                    )
                
                op_end = time.perf_counter()
                times.append((op_end - op_start) * 1000)
                
                # 進捗表示（100操作ごと）
                if (i + 1) % 100 == 0:
                    current_avg = statistics.mean(times[-100:])
                    print(f"  Progress: {i+1}/{operation_count}, avg last 100: {current_avg:.3f}ms")
                
            except Exception as e:
                error_count += 1
                print(f"  Error at operation {i}: {e}")
        
        end_time = time.perf_counter()
        total_duration = end_time - start_time
        
        # 安定性確認
        error_rate = error_count / operation_count
        assert error_rate < 0.01, f"Error rate {error_rate:.2%} exceeds 1%"
        
        # 性能確認
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        
        assert avg_time < 5.0, f"Stress test avg time {avg_time:.3f}ms exceeds 5ms"
        assert p95_time < 10.0, f"Stress test 95%ile time {p95_time:.3f}ms exceeds 10ms"
        
        # 結果出力
        print(f"Stress Test Results:")
        print(f"  Total operations: {operation_count}")
        print(f"  Total duration:   {total_duration:.1f}s")
        print(f"  Operations/sec:   {operation_count/total_duration:.1f}")
        print(f"  Error rate:       {error_rate:.2%}")
        print(f"  Average time:     {avg_time:.3f}ms")
        print(f"  95%ile time:      {p95_time:.3f}ms")
        print(f"  Stability:        {'✓ PASS' if error_rate < 0.01 else '✗ FAIL'}")
    
    def test_comprehensive_performance_summary(self):
        """総合性能サマリー"""
        print("\n=== Comprehensive Performance Summary ===")
        
        # 各コンポーネントの統計取得
        event_stats = self.event_dispatcher.get_stats()
        queue_stats = self.queue_manager.get_global_stats()
        
        # Agent統計取得
        agent_stats = {}
        for agent_name, agent in self.agents.items():
            agent_stats[agent_name] = agent.get_call_stats()
        
        print(f"Event Dispatcher Stats:")
        print(f"  Total published:    {event_stats['total_published']}")
        print(f"  Total delivered:    {event_stats['total_delivered']}")
        print(f"  Avg delivery time:  {event_stats['avg_delivery_time']:.3f}ms")
        print(f"  Max delivery time:  {event_stats['max_delivery_time']:.3f}ms")
        
        print(f"\nQueue Manager Stats:")
        print(f"  Total sent:         {queue_stats['total_sent']}")
        print(f"  Total received:     {queue_stats['total_received']}")
        print(f"  Avg transfer time:  {queue_stats['avg_transfer_time']:.3f}ms")
        print(f"  Max transfer time:  {queue_stats['max_transfer_time']:.3f}ms")
        print(f"  Timeout count:      {queue_stats['timeout_count']}")
        print(f"  Error count:        {queue_stats['error_count']}")
        
        # 目標達成確認
        targets_met = []
        targets_met.append(("Event dispatch < 1ms", event_stats['avg_delivery_time'] < 1.0))
        targets_met.append(("Message transfer < 1ms", queue_stats['avg_transfer_time'] < 1.0))
        targets_met.append(("Error rate < 1%", queue_stats['error_count'] / max(queue_stats['total_sent'], 1) < 0.01))
        
        print(f"\n=== Performance Targets Summary ===")
        for target_name, met in targets_met:
            status = "✓ PASS" if met else "✗ FAIL"
            print(f"  {target_name:<25} {status}")
        
        all_targets_met = all(met for _, met in targets_met)
        overall_status = "✓ ALL TARGETS MET" if all_targets_met else "✗ SOME TARGETS FAILED"
        print(f"\nOverall Status: {overall_status}")
        
        assert all_targets_met, "Performance targets not met"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])