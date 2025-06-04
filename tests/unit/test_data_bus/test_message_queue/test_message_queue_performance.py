"""
Message Queue Performance Tests
メッセージ転送1ms以下・優先度キュー・並行メッセージング確認
"""
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../src'))

from data_bus.message_queue.queue_manager import QueueManager
from data_bus.message_queue.priority_queue import PriorityQueue
from data_bus.message_queue.message_serializer import create_message, create_request_message


class TestMessageQueuePerformance:
    """メッセージキュー性能テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.queue_manager = QueueManager(max_workers=8)
        self.test_responses = {}
        
        # テスト用Agentとサービス登録
        self.queue_manager.register_agent('test_agent')
        self.queue_manager.register_agent('cache_layer')
        
        # テスト用ハンドラー登録
        def echo_handler(params):
            return {'echo': params, 'timestamp': time.perf_counter()}
        
        def math_handler(params):
            a = params.get('a', 0)
            b = params.get('b', 0)
            return {'result': a + b}
        
        self.queue_manager.register_handler('test_agent', 'echo', echo_handler)
        self.queue_manager.register_handler('cache_layer', 'get_frame', 
                                           lambda p: {'frame_data': f"frame_{p.get('frame_id', 'unknown')}"})
        self.queue_manager.register_handler('test_agent', 'math', math_handler)
    
    def teardown_method(self):
        """テストクリーンアップ"""
        self.queue_manager.shutdown()
    
    def test_message_transfer_1ms(self):
        """メッセージ転送1ms以下確認"""
        times = []
        
        # 100回のメッセージ転送テスト
        for i in range(100):
            start_time = time.perf_counter()
            
            result = self.queue_manager.send_message(
                target_agent='test_agent',
                message={
                    'service': 'echo',
                    'params': {'test_data': f'message_{i}', 'index': i}
                },
                priority='normal',
                timeout=100  # 100ms timeout
            )
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # ms
            times.append(execution_time)
            
            assert result is not None, f"Message transfer failed for iteration {i}"
            assert result['echo']['index'] == i, "Response data mismatch"
        
        # 性能確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        assert avg_time < 1.0, f"Average transfer time {avg_time:.3f}ms exceeds 1ms"
        assert max_time < 5.0, f"Max transfer time {max_time:.3f}ms exceeds 5ms"
        
        # 統計確認
        stats = self.queue_manager.get_global_stats()
        assert stats['total_sent'] >= 100
        assert stats['avg_transfer_time'] < 1.0
        
        print(f"Message transfer performance: avg={avg_time:.3f}ms, min={min_time:.3f}ms, max={max_time:.3f}ms")
    
    def test_priority_queue_ordering(self):
        """優先度キュー動作確認"""
        priority_queue = PriorityQueue(max_size=100)
        
        # 異なる優先度のメッセージ作成
        messages = []
        for i in range(10):
            # 低優先度メッセージ
            msg_low = create_message('sender', 'receiver', 'test', {'order': i, 'type': 'low'}, 'low')
            messages.append(('low', msg_low))
            
            # 通常優先度メッセージ
            msg_normal = create_message('sender', 'receiver', 'test', {'order': i, 'type': 'normal'}, 'normal')
            messages.append(('normal', msg_normal))
            
            # 高優先度メッセージ
            msg_high = create_message('sender', 'receiver', 'test', {'order': i, 'type': 'high'}, 'high')
            messages.append(('high', msg_high))
        
        # ランダム順序で追加
        import random
        random.shuffle(messages)
        
        for priority, message in messages:
            success = priority_queue.put(message, block=False)
            assert success, f"Failed to enqueue {priority} priority message"
        
        # 取得順序確認（高優先度が先に出る）
        retrieved = []
        while not priority_queue.empty():
            message = priority_queue.get(block=False)
            retrieved.append(message.priority)
        
        # 優先度順序確認
        high_indices = [i for i, p in enumerate(retrieved) if p == 'high']
        normal_indices = [i for i, p in enumerate(retrieved) if p == 'normal']
        low_indices = [i for i, p in enumerate(retrieved) if p == 'low']
        
        # 高優先度が最初に来る
        if high_indices:
            assert min(high_indices) < min(normal_indices + low_indices), "High priority not first"
        
        # 通常優先度が低優先度より先
        if normal_indices and low_indices:
            assert min(normal_indices) < min(low_indices), "Normal priority not before low"
        
        print(f"Priority ordering: {len(high_indices)} high, {len(normal_indices)} normal, {len(low_indices)} low")
    
    def test_concurrent_messaging(self):
        """並行メッセージング確認"""
        sender_count = 4
        messages_per_sender = 25
        total_messages = sender_count * messages_per_sender
        
        results = []
        results_lock = threading.Lock()
        
        def sender_task(sender_id):
            """送信者タスク"""
            sender_times = []
            
            for i in range(messages_per_sender):
                start_time = time.perf_counter()
                
                try:
                    result = self.queue_manager.send_message(
                        target_agent='test_agent',
                        message={
                            'service': 'math',
                            'params': {'a': sender_id, 'b': i}
                        },
                        priority='normal',
                        timeout=1000
                    )
                    
                    end_time = time.perf_counter()
                    execution_time = (end_time - start_time) * 1000
                    sender_times.append(execution_time)
                    
                    with results_lock:
                        results.append({
                            'sender_id': sender_id,
                            'message_id': i,
                            'result': result,
                            'time': execution_time
                        })
                
                except Exception as e:
                    print(f"Sender {sender_id} message {i} failed: {e}")
            
            return sender_times
        
        # 並行送信実行
        with ThreadPoolExecutor(max_workers=sender_count) as executor:
            futures = []
            for sender_id in range(sender_count):
                future = executor.submit(sender_task, sender_id)
                futures.append(future)
            
            # 結果収集
            all_times = []
            for future in futures:
                times = future.result()
                all_times.extend(times)
        
        # 性能確認
        avg_time = sum(all_times) / len(all_times)
        max_time = max(all_times)
        success_count = len(results)
        
        assert avg_time < 2.0, f"Concurrent messaging avg time {avg_time:.3f}ms exceeds 2ms"
        assert max_time < 10.0, f"Concurrent messaging max time {max_time:.3f}ms exceeds 10ms"
        assert success_count >= total_messages * 0.95, f"Success rate {success_count}/{total_messages} below 95%"
        
        # 結果正確性確認
        for result_data in results[:10]:  # 最初の10個をサンプルチェック
            expected = result_data['sender_id'] + result_data['message_id']
            actual = result_data['result']['result']
            assert actual == expected, f"Math result mismatch: {actual} != {expected}"
        
        print(f"Concurrent messaging: {sender_count} senders × {messages_per_sender} messages, avg={avg_time:.3f}ms")
    
    def test_timeout_handling(self):
        """タイムアウト処理確認"""
        # タイムアウトするハンドラー登録
        def slow_handler(params):
            delay = params.get('delay', 0.1)
            time.sleep(delay)
            return {'completed': True}
        
        self.queue_manager.register_handler('test_agent', 'slow_service', slow_handler)
        
        # 短いタイムアウトでテスト
        start_time = time.perf_counter()
        
        with pytest.raises(Exception) as exc_info:
            self.queue_manager.send_message(
                target_agent='test_agent',
                message={
                    'service': 'slow_service',
                    'params': {'delay': 0.2}  # 200ms delay
                },
                timeout=50  # 50ms timeout
            )
        
        end_time = time.perf_counter()
        elapsed_time = (end_time - start_time) * 1000
        
        # タイムアウトエラー確認
        assert "timeout" in str(exc_info.value).lower(), "Timeout error not detected"
        assert 45 <= elapsed_time <= 100, f"Timeout time {elapsed_time:.1f}ms not in expected range"
        
        print(f"Timeout handling: {elapsed_time:.1f}ms timeout detected correctly")
    
    def test_cache_layer_fast_channel(self):
        """Cache Agent高速チャネル確認"""
        # Cache Agent専用高速キュー使用
        self.queue_manager.register_agent('cache_layer', use_fast_queue=True)
        
        # 高速フレーム取得テスト
        frame_count = 50
        times = []
        
        for i in range(frame_count):
            start_time = time.perf_counter()
            
            result = self.queue_manager.send_message(
                target_agent='cache_layer',
                message={
                    'service': 'get_frame',
                    'params': {'frame_id': f'{i:06d}'}
                },
                priority='high',  # 高優先度で高速キュー使用
                timeout=50  # 50ms以内
            )
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000
            times.append(execution_time)
            
            assert result is not None, f"Cache frame retrieval failed for frame {i}"
            assert f'{i:06d}' in result['frame_data'], "Frame data mismatch"
        
        # フレーム切り替え50ms要件確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 50.0, f"Cache layer avg time {avg_time:.3f}ms exceeds 50ms"
        assert max_time < 50.0, f"Cache layer max time {max_time:.3f}ms exceeds 50ms"
        
        # 95%が30ms以下であることを確認
        under_30ms = [t for t in times if t < 30.0]
        fast_ratio = len(under_30ms) / len(times)
        
        assert fast_ratio >= 0.95, f"Fast response ratio {fast_ratio:.2%} below 95%"
        
        print(f"Cache layer fast channel: avg={avg_time:.3f}ms, max={max_time:.3f}ms, 95% under 30ms")


class TestPriorityQueueDetails:
    """優先度キュー詳細テスト"""
    
    def test_priority_queue_performance(self):
        """優先度キュー性能テスト"""
        queue = PriorityQueue(max_size=1000)
        
        # 大量メッセージのenqueue/dequeue性能
        message_count = 1000
        enqueue_times = []
        dequeue_times = []
        
        # Enqueue性能
        for i in range(message_count):
            message = create_message('sender', 'receiver', 'test', {'index': i})
            
            start_time = time.perf_counter()
            success = queue.put(message, block=False)
            end_time = time.perf_counter()
            
            enqueue_times.append((end_time - start_time) * 1000)
            assert success, f"Enqueue failed at {i}"
        
        # Dequeue性能
        for i in range(message_count):
            start_time = time.perf_counter()
            message = queue.get(block=False)
            end_time = time.perf_counter()
            
            dequeue_times.append((end_time - start_time) * 1000)
            assert message is not None, f"Dequeue failed at {i}"
        
        # 性能確認
        avg_enqueue = sum(enqueue_times) / len(enqueue_times)
        avg_dequeue = sum(dequeue_times) / len(dequeue_times)
        
        assert avg_enqueue < 0.1, f"Average enqueue time {avg_enqueue:.3f}ms too slow"
        assert avg_dequeue < 0.1, f"Average dequeue time {avg_dequeue:.3f}ms too slow"
        
        print(f"Priority queue performance: enqueue={avg_enqueue:.3f}ms, dequeue={avg_dequeue:.3f}ms")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])