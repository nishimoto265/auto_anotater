"""
Memory Profiler Unit Tests - メモリプロファイラーテスト

20GB上限監視・メモリリーク検知・ガベージコレクション効率の品質保証
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from monitoring.performance.memory_profiler import (
    MemoryProfiler, MemoryUsage, MemoryLeakResult, GCStats
)


class TestMemoryProfiler:
    """メモリプロファイラーテスト"""
    
    def setup_method(self):
        """テスト前セットアップ"""
        self.mock_data_bus = Mock()
        self.memory_profiler = MemoryProfiler(data_bus=self.mock_data_bus)
        
    def teardown_method(self):
        """テスト後クリーンアップ"""
        if self.memory_profiler.is_monitoring:
            self.memory_profiler.stop_monitoring()
            
    def test_current_memory_usage_accuracy(self):
        """現在メモリ使用量取得精度"""
        # Given: MemoryProfiler初期化済み
        
        # Mock psutil responses
        mock_memory_info = Mock()
        mock_memory_info.rss = 8 * 1024 ** 3  # 8GB
        mock_memory_info.vms = 16 * 1024 ** 3  # 16GB
        
        mock_system_memory = Mock()
        mock_system_memory.total = 64 * 1024 ** 3  # 64GB
        mock_system_memory.available = 48 * 1024 ** 3  # 48GB
        mock_system_memory.used = 16 * 1024 ** 3  # 16GB
        
        with patch.object(self.memory_profiler.process, 'memory_info', return_value=mock_memory_info), \
             patch.object(self.memory_profiler.process, 'memory_percent', return_value=12.5), \
             patch('psutil.virtual_memory', return_value=mock_system_memory):
            
            # When: get_current_memory_usage()
            usage = self.memory_profiler.get_current_memory_usage()
            
        # Then: psutil結果と一致・RSS/VMS正確
        assert usage.rss == 8 * 1024 ** 3
        assert usage.vms == 16 * 1024 ** 3
        assert usage.percent == 12.5
        assert usage.system_total == 64 * 1024 ** 3
        assert usage.rss_gb == pytest.approx(8.0, abs=0.01)
        assert usage.vms_gb == pytest.approx(16.0, abs=0.01)
        assert isinstance(usage.timestamp, datetime)
        
    def test_memory_leak_detection_positive(self):
        """メモリリーク検知（陽性）"""
        # Given: 5分間で100MB増加パターンを模擬
        base_memory = 10 * 1024 ** 3  # 10GB
        leak_rate = 1024 * 1024  # 1MB/秒
        
        # 300秒間のメモリ履歴作成（線形増加）
        for i in range(300):
            mock_usage = MemoryUsage(
                rss=int(base_memory + i * leak_rate),
                vms=int(base_memory * 2 + i * leak_rate),
                percent=50.0,
                system_total=64 * 1024 ** 3,
                system_available=32 * 1024 ** 3,
                system_used=32 * 1024 ** 3,
                timestamp=datetime.now()
            )
            self.memory_profiler.memory_history.append(mock_usage)
            
        # When: detect_memory_leak()
        leak_result = self.memory_profiler.detect_memory_leak()
        
        # Then: leak_detected=True・成長率計算正確
        assert leak_result.leak_detected is True
        assert leak_result.growth_rate_mb_per_sec == pytest.approx(1.0, abs=0.1)  # 1MB/秒
        assert leak_result.correlation > 0.7  # 高い相関
        assert leak_result.p_value < 0.05  # 統計的有意性
        assert leak_result.estimated_time_to_limit is not None
        
    def test_memory_leak_detection_negative(self):
        """メモリリーク検知（陰性）"""
        # Given: 安定メモリ使用パターン（±5%変動）
        base_memory = 10 * 1024 ** 3  # 10GB
        
        # 300秒間の安定メモリ履歴作成
        for i in range(300):
            # ランダムな小変動（±5%）
            variation = (i % 20 - 10) * 0.005  # -5%から+5%
            memory_value = int(base_memory * (1 + variation))
            
            mock_usage = MemoryUsage(
                rss=memory_value,
                vms=memory_value * 2,
                percent=50.0,
                system_total=64 * 1024 ** 3,
                system_available=32 * 1024 ** 3,
                system_used=32 * 1024 ** 3,
                timestamp=datetime.now()
            )
            self.memory_profiler.memory_history.append(mock_usage)
            
        # When: detect_memory_leak()
        leak_result = self.memory_profiler.detect_memory_leak()
        
        # Then: leak_detected=False
        assert leak_result.leak_detected is False
        assert abs(leak_result.growth_rate_mb_per_sec) < 0.1  # 成長率ほぼゼロ
        
    def test_memory_warning_at_18gb_threshold(self):
        """18GB警告閾値での警告発信"""
        # Given: warning_threshold=18GB
        assert self.memory_profiler.warning_threshold == 18 * 1024 ** 3
        
        # 18.5GB使用状況を模擬
        mock_usage = MemoryUsage(
            rss=int(18.5 * 1024 ** 3),  # 18.5GB
            vms=int(36 * 1024 ** 3),
            percent=75.0,
            system_total=64 * 1024 ** 3,
            system_available=16 * 1024 ** 3,
            system_used=48 * 1024 ** 3,
            timestamp=datetime.now()
        )
        
        # When: 警告チェック実行
        self.memory_profiler._check_and_emit_warnings(mock_usage)
        
        # Then: memory_usage warning event発信
        self.mock_data_bus.publish.assert_called_once()
        call_args = self.mock_data_bus.publish.call_args
        assert call_args[0][0] == "performance_warning"
        warning_data = call_args[0][1]
        assert warning_data["severity"] == "warning"
        assert warning_data["metric_name"] == "memory_usage"
        assert warning_data["usage_gb"] == pytest.approx(18.5, abs=0.1)
        
    def test_monitoring_thread_start_stop(self):
        """監視スレッド開始・停止"""
        # Given: MemoryProfiler初期化済み
        assert not self.memory_profiler.is_monitoring
        
        # When: start_monitoring()
        self.memory_profiler.start_monitoring()
        
        # Then: スレッド正常起動
        assert self.memory_profiler.is_monitoring is True
        assert self.memory_profiler.monitoring_thread is not None
        assert self.memory_profiler.monitoring_thread.is_alive()
        
        # When: stop_monitoring()
        self.memory_profiler.stop_monitoring()
        
        # Then: スレッド正常停止
        assert self.memory_profiler.is_monitoring is False
        # スレッドの終了を待つ
        time.sleep(0.1)
        assert not self.memory_profiler.monitoring_thread.is_alive()
        
    def test_memory_history_max_length_3600(self):
        """メモリ履歴最大長3600（1時間）"""
        # Given: MemoryProfiler with maxlen=3600
        assert self.memory_profiler.memory_history.maxlen == 3600
        
        # When: 3700個のメモリ使用量データ追加
        for i in range(3700):
            mock_usage = MemoryUsage(
                rss=10 * 1024 ** 3,
                vms=20 * 1024 ** 3,
                percent=50.0,
                system_total=64 * 1024 ** 3,
                system_available=32 * 1024 ** 3,
                system_used=32 * 1024 ** 3,
                timestamp=datetime.now()
            )
            self.memory_profiler.memory_history.append(mock_usage)
            
        # Then: memory_history最大3600要素維持
        assert len(self.memory_profiler.memory_history) == 3600
        
    def test_monitoring_interval_1_second(self):
        """監視間隔1秒精度"""
        # Given: monitoring_interval=1.0秒
        assert self.memory_profiler.monitoring_interval == 1.0
        
        # 監視ワーカーの動作テスト（短時間）
        start_time = time.time()
        self.memory_profiler.start_monitoring()
        
        # 2.5秒待機
        time.sleep(2.5)
        
        self.memory_profiler.stop_monitoring()
        elapsed_time = time.time() - start_time
        
        # Then: 約2-3回の記録・間隔1秒±0.5秒
        history_length = len(self.memory_profiler.memory_history)
        assert 2 <= history_length <= 4  # 2.5秒で2-4回の記録
        
    @patch('scipy.stats.linregress')
    def test_linear_regression_accuracy(self, mock_linregress):
        """線形回帰計算精度"""
        # Given: 既知傾きのメモリデータ（2MB/秒増加）
        mock_linregress.return_value = (
            2 * 1024 * 1024,  # slope: 2MB/秒
            10 * 1024 ** 3,   # intercept: 10GB
            0.99,             # r_value: 高い相関
            0.001,            # p_value: 統計的有意
            0.1               # std_err
        )
        
        # 300秒のデータ追加
        for i in range(300):
            mock_usage = MemoryUsage(
                rss=10 * 1024 ** 3 + i * 2 * 1024 * 1024,  # 10GB + 2MB*i
                vms=20 * 1024 ** 3,
                percent=50.0,
                system_total=64 * 1024 ** 3,
                system_available=32 * 1024 ** 3,
                system_used=32 * 1024 ** 3,
                timestamp=datetime.now()
            )
            self.memory_profiler.memory_history.append(mock_usage)
            
        # When: detect_memory_leak()
        leak_result = self.memory_profiler.detect_memory_leak()
        
        # Then: slope計算±1%精度
        assert leak_result.growth_rate_mb_per_sec == pytest.approx(2.0, abs=0.02)  # 2MB/秒 ±1%
        assert leak_result.correlation == 0.99
        assert leak_result.leak_detected is True
        
    def test_monitoring_overhead_under_5ms(self):
        """監視オーバーヘッド5ms以下"""
        # Given: MemoryProfiler
        
        # When: get_monitoring_overhead()実行
        overhead = self.memory_profiler.get_monitoring_overhead()
        
        # Then: 監視オーバーヘッド5ms以下
        assert overhead < 5.0  # 5ms以下
        
    @patch('gc.get_stats')
    @patch('gc.garbage', [])
    def test_gc_statistics(self, mock_gc_stats):
        """ガベージコレクション統計"""
        # Given: Mock GC統計
        mock_gc_stats.return_value = [
            {'collections': 100, 'collected': 1000},  # Gen 0
            {'collections': 10, 'collected': 500},    # Gen 1
            {'collections': 1, 'collected': 50}       # Gen 2
        ]
        
        # When: get_gc_statistics()
        gc_stats = self.memory_profiler.get_gc_statistics()
        
        # Then: 正確な統計取得
        assert gc_stats.collections == [100, 10, 1]
        assert gc_stats.collected == [1000, 500, 50]
        assert gc_stats.uncollectable == 0
        
        stats_dict = gc_stats.to_dict()
        assert stats_dict['gen0_collections'] == 100
        assert stats_dict['gen1_collections'] == 10
        assert stats_dict['gen2_collections'] == 1
        
    @patch('gc.collect')
    def test_force_garbage_collection(self, mock_gc_collect):
        """強制ガベージコレクション"""
        # Given: Mock GC戻り値
        mock_gc_collect.return_value = 42  # 42オブジェクト回収
        
        # When: force_garbage_collection()
        collected = self.memory_profiler.force_garbage_collection()
        
        # Then: GC実行・戻り値正確
        mock_gc_collect.assert_called_once()
        assert collected == 42
        
    def test_detailed_tracking_enable_disable(self):
        """詳細メモリ追跡有効化・無効化"""
        # Given: 初期状態（無効）
        assert not self.memory_profiler.tracemalloc_enabled
        
        # When: 有効化
        with patch('tracemalloc.start') as mock_start:
            self.memory_profiler.enable_detailed_tracking()
            
        # Then: tracemalloc開始・フラグ更新
        mock_start.assert_called_once()
        assert self.memory_profiler.tracemalloc_enabled is True
        
        # When: 無効化
        with patch('tracemalloc.stop') as mock_stop:
            self.memory_profiler.disable_detailed_tracking()
            
        # Then: tracemalloc停止・フラグ更新
        mock_stop.assert_called_once()
        assert self.memory_profiler.tracemalloc_enabled is False
        
    def test_memory_statistics_comprehensive(self):
        """包括的メモリ統計"""
        # Given: メモリ履歴データ
        test_values = [8, 10, 12, 9, 11, 13, 10, 12]  # GB
        
        for gb_value in test_values:
            mock_usage = MemoryUsage(
                rss=gb_value * 1024 ** 3,
                vms=gb_value * 2 * 1024 ** 3,
                percent=50.0,
                system_total=64 * 1024 ** 3,
                system_available=32 * 1024 ** 3,
                system_used=32 * 1024 ** 3,
                timestamp=datetime.now()
            )
            self.memory_profiler.memory_history.append(mock_usage)
            
        # When: get_memory_statistics()
        stats = self.memory_profiler.get_memory_statistics()
        
        # Then: 正確な統計計算
        assert stats['history_length'] == 8
        assert stats['max_usage_gb'] == 13.0
        assert stats['min_usage_gb'] == 8.0
        assert stats['avg_usage_gb'] == pytest.approx(10.625, abs=0.01)  # (8+10+12+9+11+13+10+12)/8
        assert stats['limit_gb'] == 20.0
        assert 'current_usage' in stats
        assert 'gc_stats' in stats
        
    def test_insufficient_data_for_leak_detection(self):
        """リーク検知用データ不足"""
        # Given: 100秒分のデータのみ（300秒必要）
        for i in range(100):
            mock_usage = MemoryUsage(
                rss=10 * 1024 ** 3,
                vms=20 * 1024 ** 3,
                percent=50.0,
                system_total=64 * 1024 ** 3,
                system_available=32 * 1024 ** 3,
                system_used=32 * 1024 ** 3,
                timestamp=datetime.now()
            )
            self.memory_profiler.memory_history.append(mock_usage)
            
        # When: detect_memory_leak()
        leak_result = self.memory_profiler.detect_memory_leak()
        
        # Then: データ不足でリーク検知不可
        assert leak_result.leak_detected is False
        assert "Insufficient data" in leak_result.reason
        
    def test_error_handling_in_usage_collection(self):
        """メモリ使用量取得エラー処理"""
        # Given: psutil.Errorを発生させる
        with patch.object(self.memory_profiler.process, 'memory_info', side_effect=Exception("Process error")):
            
            # When: get_current_memory_usage()
            # Then: RuntimeError発生
            with pytest.raises(RuntimeError, match="Failed to get memory usage"):
                self.memory_profiler.get_current_memory_usage()


class TestMemoryUsage:
    """MemoryUsage データクラステスト"""
    
    def test_memory_usage_properties(self):
        """メモリ使用量プロパティ"""
        usage = MemoryUsage(
            rss=8 * 1024 ** 3,  # 8GB
            vms=16 * 1024 ** 3,  # 16GB
            percent=12.5,
            system_total=64 * 1024 ** 3,
            system_available=48 * 1024 ** 3,
            system_used=16 * 1024 ** 3,
            timestamp=datetime.now()
        )
        
        assert usage.rss_gb == pytest.approx(8.0, abs=0.01)
        assert usage.vms_gb == pytest.approx(16.0, abs=0.01)
        
        usage_dict = usage.to_dict()
        assert usage_dict['rss_gb'] == pytest.approx(8.0, abs=0.01)
        assert usage_dict['vms_gb'] == pytest.approx(16.0, abs=0.01)
        assert usage_dict['percent'] == 12.5
        assert 'timestamp' in usage_dict


class TestMemoryLeakResult:
    """MemoryLeakResult データクラステスト"""
    
    def test_leak_result_to_dict(self):
        """リーク結果辞書変換"""
        result = MemoryLeakResult(
            leak_detected=True,
            slope=2048000,  # 2MB/秒 in bytes
            correlation=0.95,
            p_value=0.001,
            growth_rate_mb_per_sec=2.0,
            estimated_time_to_limit=3600.0,  # 1時間
            reason="Analysis completed"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['leak_detected'] is True
        assert result_dict['growth_rate_mb_per_sec'] == 2.0
        assert result_dict['correlation'] == 0.95
        assert result_dict['p_value'] == 0.001
        assert result_dict['estimated_time_to_limit_hours'] == pytest.approx(1.0, abs=0.01)
        assert result_dict['reason'] == "Analysis completed"