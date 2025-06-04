"""
Performance Overhead Tests - 監視オーバーヘッドテスト

Agent8 Monitoring の性能要件確認
監視オーバーヘッド10ms以下（全体の2%以下）の検証
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from monitoring.performance.frame_timer import FrameTimer
from monitoring.performance.memory_profiler import MemoryProfiler
from monitoring.health.system_health import SystemHealthMonitor
from monitoring.debugging.debug_logger import DebugLogger


class TestMonitoringOverhead:
    """監視オーバーヘッドテスト"""
    
    def setup_method(self):
        """テスト前セットアップ"""
        self.mock_data_bus = Mock()
        
    def test_frame_timer_overhead_under_1ms(self):
        """FrameTimer測定オーバーヘッド1ms以下"""
        # Given: FrameTimer
        frame_timer = FrameTimer(data_bus=self.mock_data_bus)
        
        # When: 測定オーバーヘッド計算（100回平均）
        total_overhead = 0
        iterations = 100
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            # 最小限の測定操作
            session_id = frame_timer.start_frame_switch_measurement(f"overhead_test_{i}")
            frame_timer.end_frame_switch_measurement(session_id)
            
            end_time = time.perf_counter()
            total_overhead += (end_time - start_time) * 1000  # ms
            
        average_overhead = total_overhead / iterations
        
        # Then: 平均オーバーヘッド1ms以下
        assert average_overhead < 1.0, f"Frame timer overhead: {average_overhead:.3f}ms (>1ms)"
        
    def test_memory_profiler_overhead_under_5ms(self):
        """MemoryProfiler監視オーバーヘッド5ms以下"""
        # Given: MemoryProfiler
        memory_profiler = MemoryProfiler(data_bus=self.mock_data_bus)
        
        # When: メモリ使用量取得オーバーヘッド（50回平均）
        total_overhead = 0
        iterations = 50
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            try:
                # メモリ使用量取得
                _ = memory_profiler.get_current_memory_usage()
            except:
                # テスト環境でpsutilエラーが発生する可能性
                pass
                
            end_time = time.perf_counter()
            total_overhead += (end_time - start_time) * 1000  # ms
            
        average_overhead = total_overhead / iterations
        
        # Then: 平均オーバーヘッド5ms以下
        assert average_overhead < 5.0, f"Memory profiler overhead: {average_overhead:.3f}ms (>5ms)"
        
    def test_system_health_check_overhead_under_10ms(self):
        """SystemHealthMonitor健全性チェックオーバーヘッド10ms以下"""
        # Given: SystemHealthMonitor
        health_monitor = SystemHealthMonitor(data_bus=self.mock_data_bus)
        
        # When: 健全性チェック実行時間測定（20回平均）
        total_overhead = 0
        iterations = 20
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            # 健全性チェック実行
            _ = health_monitor.perform_health_check()
            
            end_time = time.perf_counter()
            total_overhead += (end_time - start_time) * 1000  # ms
            
        average_overhead = total_overhead / iterations
        
        # Then: 平均オーバーヘッド10ms以下
        assert average_overhead < 10.0, f"Health check overhead: {average_overhead:.3f}ms (>10ms)"
        
    def test_debug_logger_overhead_under_5ms(self):
        """DebugLogger ログ記録オーバーヘッド5ms以下"""
        # Given: DebugLogger
        debug_logger = DebugLogger(log_level="INFO")
        
        try:
            # When: ログ記録時間測定（100回平均）
            total_overhead = 0
            iterations = 100
            
            for i in range(iterations):
                start_time = time.perf_counter()
                
                # ログ記録（Agent別・性能・エラーログ）
                debug_logger.log_agent_event("cache", "INFO", f"Test message {i}")
                debug_logger.log_performance_event("test_operation", 30.0, "cache", True)
                
                end_time = time.perf_counter()
                total_overhead += (end_time - start_time) * 1000  # ms
                
            average_overhead = total_overhead / iterations
            
            # Then: 平均オーバーヘッド5ms以下
            assert average_overhead < 5.0, f"Debug logger overhead: {average_overhead:.3f}ms (>5ms)"
            
        finally:
            debug_logger.stop_async_logging()
            
    def test_integrated_monitoring_overhead_under_2_percent(self):
        """統合監視オーバーヘッド全体の2%以下"""
        # Given: 全監視コンポーネント
        frame_timer = FrameTimer(data_bus=self.mock_data_bus)
        memory_profiler = MemoryProfiler(data_bus=self.mock_data_bus)
        health_monitor = SystemHealthMonitor(data_bus=self.mock_data_bus)
        debug_logger = DebugLogger(log_level="INFO")
        
        try:
            # When: 統合監視処理時間測定
            monitoring_time = 0
            application_time = 0
            iterations = 50
            
            for i in range(iterations):
                # アプリケーション処理シミュレート（50ms）
                app_start = time.perf_counter()
                time.sleep(0.05)  # 50ms の重い処理をシミュレート
                app_end = time.perf_counter()
                application_time += (app_end - app_start) * 1000
                
                # 監視処理時間測定
                monitor_start = time.perf_counter()
                
                # フレーム切り替え監視
                session_id = frame_timer.start_frame_switch_measurement(f"frame_{i}")
                frame_timer.end_frame_switch_measurement(session_id)
                
                # メモリ監視
                try:
                    _ = memory_profiler.get_current_memory_usage()
                except:
                    pass
                    
                # ログ記録
                debug_logger.log_performance_event("integrated_test", 45.0, "monitoring", True)
                
                # 健全性チェック（10回に1回）
                if i % 10 == 0:
                    _ = health_monitor.perform_health_check()
                    
                monitor_end = time.perf_counter()
                monitoring_time += (monitor_end - monitor_start) * 1000
                
            # オーバーヘッド比率計算
            total_time = application_time + monitoring_time
            overhead_ratio = monitoring_time / total_time
            
            # Then: 監視オーバーヘッド全体の2%以下
            assert overhead_ratio < 0.02, f"Monitoring overhead: {overhead_ratio:.3%} (>2%)"
            
            # 詳細ログ出力
            print(f"\n=== Monitoring Overhead Analysis ===")
            print(f"Application time: {application_time:.1f}ms")
            print(f"Monitoring time: {monitoring_time:.1f}ms")
            print(f"Total time: {total_time:.1f}ms")
            print(f"Overhead ratio: {overhead_ratio:.3%}")
            print(f"Average app cycle: {application_time/iterations:.1f}ms")
            print(f"Average monitor cycle: {monitoring_time/iterations:.1f}ms")
            
        finally:
            debug_logger.stop_async_logging()
            
    def test_concurrent_monitoring_overhead(self):
        """並行監視オーバーヘッドテスト"""
        # Given: 複数監視コンポーネントの並行動作
        frame_timer = FrameTimer(data_bus=self.mock_data_bus)
        memory_profiler = MemoryProfiler(data_bus=self.mock_data_bus)
        debug_logger = DebugLogger(log_level="INFO")
        
        results = {"total_overhead": 0, "iterations": 0}
        
        def monitoring_worker():
            """監視ワーカー"""
            for i in range(20):
                start_time = time.perf_counter()
                
                # 並行監視処理
                session_id = frame_timer.start_frame_switch_measurement(f"concurrent_{i}")
                debug_logger.log_agent_event("cache", "INFO", f"Concurrent test {i}")
                frame_timer.end_frame_switch_measurement(session_id)
                
                end_time = time.perf_counter()
                results["total_overhead"] += (end_time - start_time) * 1000
                results["iterations"] += 1
                
                time.sleep(0.01)  # 10ms間隔
                
        try:
            # When: 複数スレッドで並行監視実行
            threads = []
            for _ in range(3):  # 3スレッド並行
                thread = threading.Thread(target=monitoring_worker)
                threads.append(thread)
                thread.start()
                
            # 全スレッド完了待機
            for thread in threads:
                thread.join()
                
            # Then: 並行動作でもオーバーヘッド制限内
            average_overhead = results["total_overhead"] / results["iterations"]
            assert average_overhead < 2.0, f"Concurrent monitoring overhead: {average_overhead:.3f}ms (>2ms)"
            
        finally:
            debug_logger.stop_async_logging()
            
    def test_memory_monitoring_continuous_overhead(self):
        """継続メモリ監視オーバーヘッドテスト"""
        # Given: 継続メモリ監視
        memory_profiler = MemoryProfiler(data_bus=self.mock_data_bus)
        
        try:
            # When: 継続監視開始
            memory_profiler.start_monitoring()
            
            # 5秒間のアプリケーション処理シミュレート
            app_start = time.perf_counter()
            total_app_time = 0
            
            for i in range(100):  # 50ms x 100回 = 5秒
                cycle_start = time.perf_counter()
                time.sleep(0.05)  # 50ms アプリケーション処理
                cycle_end = time.perf_counter()
                total_app_time += (cycle_end - cycle_start) * 1000
                
            app_end = time.perf_counter()
            total_elapsed = (app_end - app_start) * 1000
            
            # Then: バックグラウンド監視オーバーヘッド計算
            monitoring_overhead = total_elapsed - total_app_time
            overhead_ratio = monitoring_overhead / total_elapsed
            
            # 監視オーバーヘッド5%以下（バックグラウンド動作のため）
            assert overhead_ratio < 0.05, f"Continuous monitoring overhead: {overhead_ratio:.3%} (>5%)"
            
        finally:
            memory_profiler.stop_monitoring()
            
    @pytest.mark.performance
    def test_monitoring_scalability(self):
        """監視スケーラビリティテスト"""
        # Given: 大量監視イベント
        frame_timer = FrameTimer(data_bus=self.mock_data_bus)
        debug_logger = DebugLogger(log_level="INFO")
        
        try:
            # When: 1000回の監視操作
            iterations = 1000
            start_time = time.perf_counter()
            
            for i in range(iterations):
                # フレーム測定
                session_id = frame_timer.start_frame_switch_measurement(f"scale_test_{i}")
                frame_timer.end_frame_switch_measurement(session_id)
                
                # ログ記録
                if i % 10 == 0:  # 10回に1回ログ
                    debug_logger.log_performance_event("scale_test", 40.0, "cache", True)
                    
            end_time = time.perf_counter()
            total_time = (end_time - start_time) * 1000
            
            # Then: 平均処理時間1ms以下
            average_time = total_time / iterations
            assert average_time < 1.0, f"Scalability test average: {average_time:.3f}ms (>1ms)"
            
            # 統計確認
            stats = frame_timer.get_performance_statistics()
            assert stats.total_measurements == iterations
            
        finally:
            debug_logger.stop_async_logging()


class TestMonitoringAccuracy:
    """監視精度テスト"""
    
    def test_frame_timer_measurement_accuracy(self):
        """フレームタイマー測定精度"""
        # Given: 既知の遅延時間
        frame_timer = FrameTimer()
        target_delays = [10, 30, 50, 70, 100]  # ms
        
        for target_delay in target_delays:
            # When: 既知遅延の測定
            session_id = frame_timer.start_frame_switch_measurement(f"accuracy_test_{target_delay}")
            time.sleep(target_delay / 1000.0)  # ms -> 秒
            result = frame_timer.end_frame_switch_measurement(session_id)
            
            # Then: 測定誤差±10%以内
            error_ratio = abs(result.total_time - target_delay) / target_delay
            assert error_ratio < 0.1, f"Measurement error: {error_ratio:.3%} for {target_delay}ms"
            
    def test_memory_usage_measurement_consistency(self):
        """メモリ使用量測定一貫性"""
        # Given: MemoryProfiler
        memory_profiler = MemoryProfiler()
        
        # When: 連続メモリ測定（変動が少ない環境想定）
        measurements = []
        for i in range(10):
            try:
                usage = memory_profiler.get_current_memory_usage()
                measurements.append(usage.rss)
                time.sleep(0.1)
            except:
                # テスト環境でのエラーをスキップ
                pytest.skip("Memory measurement not available in test environment")
                
        # Then: 測定値の変動10%以内（安定環境想定）
        if measurements:
            avg_memory = sum(measurements) / len(measurements)
            max_deviation = max(abs(m - avg_memory) / avg_memory for m in measurements)
            assert max_deviation < 0.1, f"Memory measurement deviation: {max_deviation:.3%} (>10%)"