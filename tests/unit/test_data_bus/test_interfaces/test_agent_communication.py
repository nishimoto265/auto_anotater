"""
Agent Communication Tests
全Agent間通信・Cache Agent高速チャネル確認
"""
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../src'))

from data_bus.interfaces.layer_interface import LayerInterface, CacheLayerInterface
from data_bus.interfaces.api_registry import get_global_api_registry
from data_bus.message_queue.queue_manager import get_global_queue_manager
from data_bus.event_bus.event_dispatcher import get_global_dispatcher
from data_bus.event_bus.event_types import EVENT_FRAME_CHANGED, EVENT_BB_CREATED


class TestAgentCommunication:
    """Agent間通信テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        # テスト用Agent作成
        self.agents = {}
        agent_names = ['presentation', 'application', 'domain', 'infrastructure', 
                      'cache_layer', 'persistence', 'monitoring']
        
        for agent_name in agent_names:
            self.agents[agent_name] = LayerInterface(agent_name)
        
        # テスト用サービス登録
        self._register_test_services()
        
        # 統計リセット
        for agent in self.agents.values():
            agent.reset_stats()
    
    def teardown_method(self):
        """テストクリーンアップ"""
        for agent in self.agents.values():
            agent.shutdown()
    
    def _register_test_services(self):
        """テスト用サービス登録"""
        # Presentation Layer
        def render_bb(bb_list):
            return {'rendered_count': len(bb_list), 'status': 'success'}
        
        def update_canvas():
            return {'updated': True, 'timestamp': time.perf_counter()}
        
        self.agents['presentation'].register_service('render_bb', render_bb, timeout=16)
        self.agents['presentation'].register_service('update_canvas', update_canvas, timeout=10)
        
        # Application Layer
        def create_bb(x, y, w, h, id, action):
            return {
                'bb_id': f'bb_{id}_{int(time.perf_counter()*1000)}',
                'coordinates': {'x': x, 'y': y, 'w': w, 'h': h},
                'id': id,
                'action': action,
                'created': True
            }
        
        def validate_bb(bb_data):
            valid = all(k in bb_data for k in ['x', 'y', 'w', 'h', 'id'])
            return {'valid': valid, 'errors': [] if valid else ['missing_fields']}
        
        self.agents['application'].register_service('create_bb', create_bb, timeout=10)
        self.agents['application'].register_service('validate_bb', validate_bb, timeout=3)
        
        # Domain Layer
        def calculate_iou(bb1, bb2):
            # シンプルなIOUシミュレーション
            return {'iou_score': 0.75, 'calculation_time': 0.5}
        
        def transform_coordinates(coords, from_format, to_format, width, height):
            if from_format == 'pixel' and to_format == 'yolo':
                return {
                    'x': coords['x'] / width,
                    'y': coords['y'] / height,
                    'w': coords['w'] / width,
                    'h': coords['h'] / height
                }
            return coords
        
        self.agents['domain'].register_service('calculate_iou', calculate_iou, timeout=1)
        self.agents['domain'].register_service('transform_coordinates', transform_coordinates, timeout=0.5)
        
        # Cache Layer (最重要)
        def get_frame(frame_id):
            # フレーム取得シミュレーション
            time.sleep(0.005)  # 5ms処理時間
            return {
                'frame_data': f'frame_data_{frame_id}',
                'width': 1920,
                'height': 1080,
                'loaded_time': time.perf_counter()
            }
        
        def preload_frames(frame_ids):
            return {'preloaded_count': len(frame_ids), 'status': 'started'}
        
        self.agents['cache_layer'].register_service('get_frame', get_frame, timeout=50)
        self.agents['cache_layer'].register_service('preload_frames', preload_frames, timeout=10)
        
        # Infrastructure Layer
        def load_video(video_path):
            return {'frame_count': 1500, 'fps': 30, 'loaded': True}
        
        def convert_frame(frame_data, target_size):
            return {'converted_frame': f'converted_{target_size}', 'processing_time': 15}
        
        self.agents['infrastructure'].register_service('load_video', load_video, timeout=1000)
        self.agents['infrastructure'].register_service('convert_frame', convert_frame, timeout=50)
        
        # Persistence Layer
        def save_annotations(frame_id, bb_list):
            return {'saved_count': len(bb_list), 'file_path': f'annotations/{frame_id}.txt'}
        
        def load_project(project_path):
            return {'project_data': {'name': 'test_project'}, 'loaded': True}
        
        self.agents['persistence'].register_service('save_annotations', save_annotations, timeout=100)
        self.agents['persistence'].register_service('load_project', load_project, timeout=50)
        
        # Monitoring Layer
        def collect_metrics():
            return {
                'cpu_usage': 45.2,
                'memory_usage': 8.5,
                'frame_time': 35.2,
                'timestamp': time.perf_counter()
            }
        
        def generate_alert(metric, value, threshold):
            return {'alert_id': f'alert_{int(time.perf_counter()*1000)}', 'severity': 'warning'}
        
        self.agents['monitoring'].register_service('collect_metrics', collect_metrics, timeout=10)
        self.agents['monitoring'].register_service('generate_alert', generate_alert, timeout=5)
    
    def test_all_agent_connectivity(self):
        """全Agent間通信確認"""
        # 各Agentから他の全Agentへのping実行
        connectivity_matrix = {}
        
        for source_agent_name, source_agent in self.agents.items():
            connectivity_matrix[source_agent_name] = {}
            
            for target_agent_name in self.agents.keys():
                if source_agent_name != target_agent_name:
                    try:
                        ping_time = source_agent.ping_agent(target_agent_name, timeout=100)
                        connectivity_matrix[source_agent_name][target_agent_name] = ping_time
                    except Exception as e:
                        connectivity_matrix[source_agent_name][target_agent_name] = -1
        
        # 接続性確認
        successful_connections = 0
        total_connections = 0
        
        for source, targets in connectivity_matrix.items():
            for target, ping_time in targets.items():
                total_connections += 1
                if ping_time >= 0:
                    successful_connections += 1
                    assert ping_time < 50.0, f"Ping {source}->{target} too slow: {ping_time:.2f}ms"
        
        connectivity_ratio = successful_connections / total_connections
        assert connectivity_ratio >= 0.95, f"Connectivity ratio {connectivity_ratio:.2%} below 95%"
        
        print(f"Agent connectivity: {successful_connections}/{total_connections} connections successful")
    
    def test_cache_agent_fast_channel(self):
        """Cache Agent高速チャネル確認"""
        cache_interface = CacheLayerInterface(self.agents['cache_layer'])
        
        # フレーム取得性能テスト
        frame_count = 100
        times = []
        
        for i in range(frame_count):
            frame_id = f'{i:06d}'
            
            start_time = time.perf_counter()
            frame_data = cache_interface.get_frame(frame_id, timeout=50)
            end_time = time.perf_counter()
            
            execution_time = (end_time - start_time) * 1000  # ms
            times.append(execution_time)
            
            assert frame_data is not None, f"Frame retrieval failed for {frame_id}"
            assert frame_id in frame_data['frame_data'], f"Frame data mismatch for {frame_id}"
        
        # 50ms以下確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 50.0, f"Cache avg time {avg_time:.3f}ms exceeds 50ms"
        assert max_time < 50.0, f"Cache max time {max_time:.3f}ms exceeds 50ms"
        
        # 95%が30ms以下
        fast_responses = [t for t in times if t < 30.0]
        fast_ratio = len(fast_responses) / len(times)
        
        assert fast_ratio >= 0.95, f"Fast response ratio {fast_ratio:.2%} below 95%"
        
        print(f"Cache fast channel: avg={avg_time:.3f}ms, max={max_time:.3f}ms, {fast_ratio:.1%} under 30ms")
    
    def test_typical_workflow_performance(self):
        """典型的ワークフロー性能テスト"""
        # フレーム切り替え→BB作成→保存のワークフロー
        workflow_count = 50
        workflow_times = []
        
        for i in range(workflow_count):
            workflow_start = time.perf_counter()
            
            # 1. フレーム取得（Cache Layer）
            frame_id = f'{i:06d}'
            frame_data = self.agents['cache_layer'].call_service(
                'cache_layer', 'get_frame', frame_id=frame_id
            )
            
            # 2. BB作成（Application Layer）
            bb_data = self.agents['application'].call_service(
                'application', 'create_bb',
                x=100+i, y=200+i, w=50, h=80, id=i%16, action=i%5
            )
            
            # 3. 座標変換（Domain Layer）
            coords = self.agents['domain'].call_service(
                'domain', 'transform_coordinates',
                coords={'x': 100+i, 'y': 200+i, 'w': 50, 'h': 80},
                from_format='pixel', to_format='yolo',
                width=1920, height=1080
            )
            
            # 4. アノテーション保存（Persistence Layer）
            save_result = self.agents['persistence'].call_service(
                'persistence', 'save_annotations',
                frame_id=frame_id, bb_list=[bb_data]
            )
            
            workflow_end = time.perf_counter()
            workflow_time = (workflow_end - workflow_start) * 1000  # ms
            workflow_times.append(workflow_time)
            
            # 結果確認
            assert frame_data is not None
            assert bb_data['created'] is True
            assert 'x' in coords
            assert save_result['saved_count'] == 1
        
        # ワークフロー性能確認
        avg_workflow_time = sum(workflow_times) / len(workflow_times)
        max_workflow_time = max(workflow_times)
        
        # フレーム切り替え全体で50ms以下
        assert avg_workflow_time < 50.0, f"Workflow avg time {avg_workflow_time:.3f}ms exceeds 50ms"
        assert max_workflow_time < 100.0, f"Workflow max time {max_workflow_time:.3f}ms exceeds 100ms"
        
        print(f"Workflow performance: avg={avg_workflow_time:.3f}ms, max={max_workflow_time:.3f}ms")
    
    def test_event_driven_communication(self):
        """イベント駆動通信テスト"""
        # イベント受信カウンター
        event_counters = {agent_name: 0 for agent_name in self.agents.keys()}
        received_events = []
        
        def make_event_handler(agent_name):
            def handler(event):
                event_counters[agent_name] += 1
                received_events.append((agent_name, event.event_type, time.perf_counter()))
            return handler
        
        # 全Agentでフレーム変更イベント購読
        subscriptions = {}
        for agent_name, agent in self.agents.items():
            subscription_id = agent.subscribe_event(EVENT_FRAME_CHANGED, make_event_handler(agent_name))
            subscriptions[agent_name] = subscription_id
        
        # イベント発行テスト
        event_count = 50
        publish_times = []
        
        for i in range(event_count):
            start_time = time.perf_counter()
            
            success = self.agents['application'].publish_event(
                EVENT_FRAME_CHANGED,
                {
                    'current_frame_id': f'frame_{i:06d}',
                    'previous_frame_id': f'frame_{i-1:06d}',
                    'switch_time': 25.5
                }
            )
            
            end_time = time.perf_counter()
            publish_time = (end_time - start_time) * 1000
            publish_times.append(publish_time)
            
            assert success, f"Event publish failed for iteration {i}"
        
        # イベント配信完了待機
        time.sleep(0.1)
        
        # イベント配信確認
        avg_publish_time = sum(publish_times) / len(publish_times)
        assert avg_publish_time < 1.0, f"Event publish avg time {avg_publish_time:.3f}ms exceeds 1ms"
        
        # 全Agentでのイベント受信確認
        for agent_name, count in event_counters.items():
            if agent_name != 'application':  # 発行者以外
                assert count >= event_count * 0.95, f"Agent {agent_name} received {count}/{event_count} events"
        
        print(f"Event communication: {len(received_events)} events received, avg publish={avg_publish_time:.3f}ms")
    
    def test_concurrent_multi_agent_operations(self):
        """並行マルチAgent操作テスト"""
        operation_count = 20
        agent_pairs = [
            ('presentation', 'application'),
            ('application', 'domain'),
            ('cache_layer', 'infrastructure'),
            ('domain', 'persistence'),
            ('monitoring', 'cache_layer')
        ]
        
        results = []
        results_lock = threading.Lock()
        
        def operation_task(source_agent_name, target_agent_name, task_id):
            """並行操作タスク"""
            source_agent = self.agents[source_agent_name]
            times = []
            
            for i in range(operation_count):
                start_time = time.perf_counter()
                
                try:
                    if target_agent_name == 'cache_layer':
                        result = source_agent.call_service(
                            target_agent_name, 'get_frame',
                            frame_id=f'{task_id}_{i:03d}'
                        )
                    elif target_agent_name == 'domain':
                        result = source_agent.call_service(
                            target_agent_name, 'calculate_iou',
                            bb1={'x': 100, 'y': 100, 'w': 50, 'h': 50},
                            bb2={'x': 120, 'y': 110, 'w': 50, 'h': 50}
                        )
                    elif target_agent_name == 'application':
                        result = source_agent.call_service(
                            target_agent_name, 'create_bb',
                            x=100+i, y=200+i, w=50, h=80, id=i%16, action=i%5
                        )
                    else:
                        # デフォルト操作
                        available_services = source_agent.get_available_services(target_agent_name)
                        if available_services:
                            service_name = available_services[0]['service_name']
                            result = source_agent.call_service(target_agent_name, service_name)
                        else:
                            result = {'status': 'no_service'}
                    
                    end_time = time.perf_counter()
                    execution_time = (end_time - start_time) * 1000
                    times.append(execution_time)
                    
                    with results_lock:
                        results.append({
                            'source': source_agent_name,
                            'target': target_agent_name,
                            'task_id': task_id,
                            'operation_id': i,
                            'time': execution_time,
                            'success': True
                        })
                
                except Exception as e:
                    with results_lock:
                        results.append({
                            'source': source_agent_name,
                            'target': target_agent_name,
                            'task_id': task_id,
                            'operation_id': i,
                            'error': str(e),
                            'success': False
                        })
            
            return times
        
        # 並行実行
        with ThreadPoolExecutor(max_workers=len(agent_pairs)) as executor:
            futures = []
            for task_id, (source, target) in enumerate(agent_pairs):
                future = executor.submit(operation_task, source, target, task_id)
                futures.append(future)
            
            # 結果収集
            all_times = []
            for future in futures:
                times = future.result()
                all_times.extend(times)
        
        # 成功率確認
        successful_operations = [r for r in results if r['success']]
        success_rate = len(successful_operations) / len(results)
        
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
        
        # 性能確認
        if all_times:
            avg_time = sum(all_times) / len(all_times)
            max_time = max(all_times)
            
            assert avg_time < 50.0, f"Concurrent operations avg time {avg_time:.3f}ms exceeds 50ms"
            assert max_time < 200.0, f"Concurrent operations max time {max_time:.3f}ms exceeds 200ms"
            
            print(f"Concurrent multi-agent: {len(results)} operations, {success_rate:.1%} success, avg={avg_time:.3f}ms")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])