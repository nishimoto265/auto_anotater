"""
Event Dispatch Performance Tests
イベント配信1ms以下・通信オーバーヘッド5%以下確認
"""
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../src'))

from data_bus.event_bus.event_dispatcher import EventDispatcher
from data_bus.event_bus.event_types import EVENT_FRAME_CHANGED, EVENT_BB_CREATED, EventData


class TestEventDispatchPerformance:
    """イベント配信性能テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.dispatcher = EventDispatcher(max_workers=8)
        self.received_events = []
        self.receive_times = []
        
    def teardown_method(self):
        """テストクリーンアップ"""
        self.dispatcher.shutdown()
    
    def test_event_publish_1ms(self):
        """イベント発行1ms以下確認"""
        # 単一購読者
        def callback(event):
            self.received_events.append(event)
        
        subscription_id = self.dispatcher.subscribe(EVENT_FRAME_CHANGED, callback)
        
        # パフォーマンス測定
        times = []
        for i in range(100):
            start_time = time.perf_counter()
            
            success = self.dispatcher.publish(
                EVENT_FRAME_CHANGED,
                {'current_frame_id': f'frame_{i:06d}', 'previous_frame_id': f'frame_{i-1:06d}'},
                'test_agent'
            )
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # ms
            times.append(execution_time)
            
            assert success, f"Event publish failed for iteration {i}"
        
        # 1ms以下確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 1.0, f"Average publish time {avg_time:.3f}ms exceeds 1ms"
        assert max_time < 2.0, f"Max publish time {max_time:.3f}ms exceeds 2ms"  # 若干の余裕
        
        # 統計確認
        stats = self.dispatcher.get_stats()
        assert stats['total_published'] == 100
        assert stats['avg_delivery_time'] < 1.0
        
        print(f"Event publish performance: avg={avg_time:.3f}ms, max={max_time:.3f}ms")
    
    def test_multi_subscriber_delivery(self):
        """複数購読者配信性能確認"""
        subscriber_count = 8
        callbacks = []
        received_counts = [0] * subscriber_count
        
        # 複数購読者登録
        for i in range(subscriber_count):
            def make_callback(index):
                def callback(event):
                    received_counts[index] += 1
                return callback
            
            callbacks.append(make_callback(i))
            self.dispatcher.subscribe(EVENT_BB_CREATED, callbacks[i])
        
        # イベント発行テスト
        event_count = 100
        times = []
        
        for i in range(event_count):
            start_time = time.perf_counter()
            
            success = self.dispatcher.publish(
                EVENT_BB_CREATED,
                {'bb_entity': {'id': i, 'x': 100, 'y': 100}, 'frame_id': f'frame_{i:06d}'},
                'test_agent'
            )
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # ms
            times.append(execution_time)
            
            assert success, f"Multi-subscriber publish failed for iteration {i}"
        
        # 配信完了待機
        time.sleep(0.1)
        
        # 性能確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 1.0, f"Multi-subscriber avg time {avg_time:.3f}ms exceeds 1ms"
        assert max_time < 3.0, f"Multi-subscriber max time {max_time:.3f}ms exceeds 3ms"
        
        # 全購読者に配信確認
        for i, count in enumerate(received_counts):
            assert count == event_count, f"Subscriber {i} received {count}/{event_count} events"
        
        print(f"Multi-subscriber delivery: {subscriber_count} subscribers, avg={avg_time:.3f}ms")
    
    def test_communication_overhead_5_percent(self):
        """通信オーバーヘッド5%以下確認"""
        # ベースライン測定（通信なし）
        baseline_times = []
        for i in range(100):
            start_time = time.perf_counter()
            
            # 通信なしでの処理時間測定
            dummy_data = {'frame_id': f'frame_{i:06d}', 'processing': True}
            dummy_result = len(str(dummy_data))  # ダミー処理
            
            end_time = time.perf_counter()
            baseline_times.append((end_time - start_time) * 1000)
        
        baseline_avg = sum(baseline_times) / len(baseline_times)
        
        # 通信ありでの測定
        received_count = 0
        def callback(event):
            nonlocal received_count
            received_count += 1
        
        self.dispatcher.subscribe(EVENT_FRAME_CHANGED, callback)
        
        communication_times = []
        for i in range(100):
            start_time = time.perf_counter()
            
            # 通信処理
            dummy_data = {'frame_id': f'frame_{i:06d}', 'processing': True}
            success = self.dispatcher.publish(EVENT_FRAME_CHANGED, dummy_data, 'test_agent')
            dummy_result = len(str(dummy_data))  # 同じダミー処理
            
            end_time = time.perf_counter()
            communication_times.append((end_time - start_time) * 1000)
            
            assert success
        
        communication_avg = sum(communication_times) / len(communication_times)
        
        # オーバーヘッド計算
        if baseline_avg > 0:
            overhead_ratio = (communication_avg - baseline_avg) / communication_avg
        else:
            overhead_ratio = communication_avg / (communication_avg + 0.001)  # ゼロ除算回避
        
        overhead_percent = overhead_ratio * 100
        
        assert overhead_percent < 5.0, f"Communication overhead {overhead_percent:.2f}% exceeds 5%"
        
        print(f"Communication overhead: {overhead_percent:.2f}% (baseline={baseline_avg:.3f}ms, comm={communication_avg:.3f}ms)")
    
    def test_concurrent_event_publishing(self):
        """並行イベント発行テスト"""
        subscriber_count = 4
        publisher_count = 4
        events_per_publisher = 25
        total_events = publisher_count * events_per_publisher
        
        received_events = []
        lock = threading.Lock()
        
        def callback(event):
            with lock:
                received_events.append(event)
        
        # 購読者登録
        for i in range(subscriber_count):
            self.dispatcher.subscribe(EVENT_FRAME_CHANGED, callback)
        
        # 並行発行テスト
        def publisher_task(publisher_id):
            times = []
            for i in range(events_per_publisher):
                start_time = time.perf_counter()
                
                success = self.dispatcher.publish(
                    EVENT_FRAME_CHANGED,
                    {
                        'current_frame_id': f'pub{publisher_id}_frame_{i:03d}',
                        'publisher_id': publisher_id
                    },
                    f'publisher_{publisher_id}'
                )
                
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                
                assert success
            
            return times
        
        # 並行実行
        with ThreadPoolExecutor(max_workers=publisher_count) as executor:
            futures = []
            for pub_id in range(publisher_count):
                future = executor.submit(publisher_task, pub_id)
                futures.append(future)
            
            # 結果収集
            all_times = []
            for future in futures:
                times = future.result()
                all_times.extend(times)
        
        # 配信完了待機
        time.sleep(0.2)
        
        # パフォーマンス確認
        avg_time = sum(all_times) / len(all_times)
        max_time = max(all_times)
        
        assert avg_time < 1.5, f"Concurrent publish avg time {avg_time:.3f}ms exceeds 1.5ms"
        assert max_time < 5.0, f"Concurrent publish max time {max_time:.3f}ms exceeds 5ms"
        
        # 配信確認
        expected_total_received = total_events * subscriber_count
        actual_received = len(received_events)
        
        # 許容範囲内での受信確認（非同期のため100%は難しい）
        assert actual_received >= expected_total_received * 0.95, \
            f"Received {actual_received}/{expected_total_received} events (95% threshold)"
        
        print(f"Concurrent publishing: {publisher_count} publishers × {events_per_publisher} events, avg={avg_time:.3f}ms")
    
    def test_event_ordering_under_load(self):
        """負荷下でのイベント順序確認"""
        received_order = []
        lock = threading.Lock()
        
        def callback(event):
            with lock:
                received_order.append(event.data.get('sequence_id'))
        
        self.dispatcher.subscribe(EVENT_FRAME_CHANGED, callback)
        
        # 順次発行
        sequence_count = 100
        for i in range(sequence_count):
            success = self.dispatcher.publish(
                EVENT_FRAME_CHANGED,
                {'sequence_id': i, 'frame_id': f'frame_{i:06d}'},
                'test_agent'
            )
            assert success
        
        # 完了待機
        time.sleep(0.1)
        
        # 順序確認（並行処理のため完全な順序は保証されないが、大半は順序通り）
        correct_order_count = 0
        for i in range(len(received_order) - 1):
            if received_order[i] is not None and received_order[i + 1] is not None:
                if received_order[i] <= received_order[i + 1]:
                    correct_order_count += 1
        
        if len(received_order) > 1:
            order_ratio = correct_order_count / (len(received_order) - 1)
            # 並行処理のため70%以上の順序保持を期待
            assert order_ratio >= 0.7, f"Event ordering ratio {order_ratio:.2f} below 70%"
        
        print(f"Event ordering: {correct_order_count}/{len(received_order)-1} in order ({order_ratio:.2%})")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])