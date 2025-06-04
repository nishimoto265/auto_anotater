"""
Frame Timer Unit Tests - フレーム切り替え時間測定テスト

Agent8 Monitoring の最重要コンポーネントの品質保証
フレーム切り替え50ms以下監視の精度確認
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from monitoring.performance.frame_timer import (
    FrameTimer, FrameSwitchMeasurement, FrameSwitchResult, 
    FramePerformanceStats, MonitoringError
)


class TestFrameTimer:
    """フレーム切り替え時間測定テスト"""
    
    def setup_method(self):
        """テスト前セットアップ"""
        self.mock_data_bus = Mock()
        self.frame_timer = FrameTimer(data_bus=self.mock_data_bus)
        
    def test_start_frame_switch_measurement(self):
        """測定開始の正常動作"""
        # Given: FrameTimer初期化済み
        frame_id = "frame_001"
        
        # When: フレーム切り替え測定開始
        session_id = self.frame_timer.start_frame_switch_measurement(frame_id)
        
        # Then: セッションID生成・測定開始時刻記録
        assert session_id is not None
        assert session_id in self.frame_timer.active_measurements
        
        measurement = self.frame_timer.active_measurements[session_id]
        assert measurement.frame_id == frame_id
        assert measurement.start_time > 0
        assert measurement.session_id == session_id
        
    def test_start_measurement_session_limit(self):
        """セッション数上限チェック"""
        # Given: 10セッション作成済み
        for i in range(10):
            self.frame_timer.start_frame_switch_measurement(f"frame_{i:03d}")
            
        # When: 11セッション目作成試行
        # Then: MonitoringError発生
        with pytest.raises(MonitoringError, match="Maximum concurrent measurement sessions exceeded"):
            self.frame_timer.start_frame_switch_measurement("frame_overflow")
            
    def test_end_frame_switch_measurement_under_50ms(self):
        """50ms以下の正常な測定終了"""
        # Given: 測定開始済み
        frame_id = "frame_fast"
        session_id = self.frame_timer.start_frame_switch_measurement(frame_id)
        
        # 30ms相当の遅延をシミュレート
        start_time = self.frame_timer.active_measurements[session_id].start_time
        
        # When: 30ms後に測定終了（time.perf_counterをモック）
        with patch('time.perf_counter') as mock_time:
            mock_time.return_value = start_time + 0.030  # 30ms後
            result = self.frame_timer.end_frame_switch_measurement(session_id)
            
        # Then: success=True・total_time=30ms記録
        assert result.success is True
        assert abs(result.total_time - 30.0) < 1.0  # 30ms ± 1ms
        assert result.frame_id == frame_id
        assert session_id not in self.frame_timer.active_measurements  # クリーンアップ確認
        
    def test_end_frame_switch_measurement_over_50ms(self):
        """50ms超過の測定終了"""
        # Given: 測定開始済み
        frame_id = "frame_slow"
        session_id = self.frame_timer.start_frame_switch_measurement(frame_id)
        start_time = self.frame_timer.active_measurements[session_id].start_time
        
        # When: 60ms後に測定終了
        with patch('time.perf_counter') as mock_time:
            mock_time.return_value = start_time + 0.060  # 60ms後
            result = self.frame_timer.end_frame_switch_measurement(session_id)
            
        # Then: success=False・警告発信
        assert result.success is False
        assert abs(result.total_time - 60.0) < 1.0  # 60ms ± 1ms
        
        # Data Bus警告発信確認
        self.mock_data_bus.publish.assert_called_once()
        call_args = self.mock_data_bus.publish.call_args
        assert call_args[0][0] == "performance_warning"  # イベント名
        warning_data = call_args[0][1]
        assert warning_data["severity"] == "error"
        assert warning_data["metric_name"] == "frame_switching_time"
        
    def test_cache_timing_recording(self):
        """Cache層タイミング記録"""
        # Given: 測定セッション有効
        session_id = self.frame_timer.start_frame_switch_measurement("frame_cache")
        
        # When: cache_start/cache_end記録
        with patch('time.perf_counter') as mock_time:
            # Cache開始
            mock_time.return_value = 1000.0
            self.frame_timer.record_cache_timing(session_id, cache_start=True)
            
            # Cache終了
            mock_time.return_value = 1000.025  # 25ms後
            self.frame_timer.record_cache_timing(session_id, cache_start=False)
            
            # 測定終了
            mock_time.return_value = 1000.040  # 40ms後
            result = self.frame_timer.end_frame_switch_measurement(session_id)
            
        # Then: cache_time正確計算
        assert result.cache_time is not None
        assert abs(result.cache_time - 25.0) < 1.0  # 25ms ± 1ms
        
    def test_ui_timing_recording(self):
        """UI層タイミング記録"""
        # Given: 測定セッション有効
        session_id = self.frame_timer.start_frame_switch_measurement("frame_ui")
        
        # When: ui_start/ui_end記録
        with patch('time.perf_counter') as mock_time:
            # UI開始
            mock_time.return_value = 2000.0
            self.frame_timer.record_ui_timing(session_id, ui_start=True)
            
            # UI終了
            mock_time.return_value = 2000.010  # 10ms後
            self.frame_timer.record_ui_timing(session_id, ui_start=False)
            
            # 測定終了
            mock_time.return_value = 2000.035  # 35ms後
            result = self.frame_timer.end_frame_switch_measurement(session_id)
            
        # Then: ui_time正確計算
        assert result.ui_time is not None
        assert abs(result.ui_time - 10.0) < 1.0  # 10ms ± 1ms
        
    def test_performance_statistics_calculation(self):
        """性能統計計算の正確性"""
        # Given: 複数の測定データ
        test_times = [30.0, 40.0, 50.0, 60.0, 70.0]  # ms
        
        with patch('time.perf_counter') as mock_time:
            for i, target_time in enumerate(test_times):
                session_id = self.frame_timer.start_frame_switch_measurement(f"frame_{i}")
                start_time = 1000.0 + i * 100
                mock_time.return_value = start_time
                self.frame_timer.active_measurements[session_id].start_time = start_time
                
                # 目標時間後に終了
                mock_time.return_value = start_time + target_time / 1000
                self.frame_timer.end_frame_switch_measurement(session_id)
                
        # When: get_performance_statistics()
        stats = self.frame_timer.get_performance_statistics()
        
        # Then: 平均・中央値・標準偏差・成功率正確
        assert stats.total_measurements == 5
        assert abs(stats.average_time - 50.0) < 1.0  # 平均50ms
        assert abs(stats.median_time - 50.0) < 1.0   # 中央値50ms
        assert stats.min_time == 30.0
        assert stats.max_time == 70.0
        assert stats.success_rate == 0.6  # 30,40,50msが成功（3/5）
        assert stats.under_50ms_rate == 0.6  # 30,40,50msが50ms以下（3/5）
        
    def test_performance_warning_emission_at_45ms(self):
        """45ms警告閾値での警告発信"""
        # Given: warning_threshold=45ms
        assert self.frame_timer.warning_threshold == 45.0
        
        session_id = self.frame_timer.start_frame_switch_measurement("frame_warning")
        start_time = self.frame_timer.active_measurements[session_id].start_time
        
        # When: 46ms測定結果
        with patch('time.perf_counter') as mock_time:
            mock_time.return_value = start_time + 0.046  # 46ms後
            result = self.frame_timer.end_frame_switch_measurement(session_id)
            
        # Then: performance_warning event発信
        self.mock_data_bus.publish.assert_called_once()
        call_args = self.mock_data_bus.publish.call_args
        assert call_args[0][0] == "performance_warning"
        warning_data = call_args[0][1]
        assert warning_data["severity"] == "warning"  # 45-50ms間は警告
        assert warning_data["value"] == pytest.approx(46.0, abs=1.0)
        
    def test_measurement_session_cleanup(self):
        """測定セッションクリーンアップ"""
        # Given: アクティブセッション
        session_id = self.frame_timer.start_frame_switch_measurement("frame_cleanup")
        assert session_id in self.frame_timer.active_measurements
        
        # When: 測定終了
        with patch('time.perf_counter') as mock_time:
            start_time = self.frame_timer.active_measurements[session_id].start_time
            mock_time.return_value = start_time + 0.030
            self.frame_timer.end_frame_switch_measurement(session_id)
            
        # Then: active_measurements[session_id]削除
        assert session_id not in self.frame_timer.active_measurements
        
    def test_concurrent_measurements(self):
        """並行測定セッション処理"""
        # Given: 複数セッション同時実行
        session_ids = []
        for i in range(5):
            session_id = self.frame_timer.start_frame_switch_measurement(f"concurrent_frame_{i}")
            session_ids.append(session_id)
            
        # When: 各セッション独立で測定
        results = []
        with patch('time.perf_counter') as mock_time:
            for i, session_id in enumerate(session_ids):
                start_time = self.frame_timer.active_measurements[session_id].start_time
                target_time = 20.0 + i * 10  # 20, 30, 40, 50, 60ms
                mock_time.return_value = start_time + target_time / 1000
                result = self.frame_timer.end_frame_switch_measurement(session_id)
                results.append(result)
                
        # Then: 相互干渉なし・正確測定
        assert len(results) == 5
        for i, result in enumerate(results):
            expected_time = 20.0 + i * 10
            assert abs(result.total_time - expected_time) < 1.0
            assert result.frame_id == f"concurrent_frame_{i}"
            
    def test_measurement_overhead_under_1ms(self):
        """測定オーバーヘッド1ms以下"""
        # Given: FrameTimer
        
        # When: start/end測定のみ実行
        overhead = self.frame_timer.get_measurement_overhead()
        
        # Then: オーバーヘッド1ms以下
        assert overhead < 1.0  # 1ms以下
        
    def test_invalid_session_handling(self):
        """無効セッション処理"""
        # Given: 存在しないセッションID
        invalid_session_id = "invalid_session"
        
        # When: 無効セッションで操作
        # Then: 適切なエラー処理
        with pytest.raises(MonitoringError, match="Measurement session not found"):
            self.frame_timer.end_frame_switch_measurement(invalid_session_id)
            
        # record_cache_timing/record_ui_timingは例外なし（無視）
        self.frame_timer.record_cache_timing(invalid_session_id)
        self.frame_timer.record_ui_timing(invalid_session_id)
        
    def test_recent_measurements(self):
        """最近の測定結果取得"""
        # Given: 複数測定実行
        for i in range(15):
            session_id = self.frame_timer.start_frame_switch_measurement(f"frame_{i}")
            with patch('time.perf_counter') as mock_time:
                start_time = self.frame_timer.active_measurements[session_id].start_time
                mock_time.return_value = start_time + 0.030  # 30ms
                self.frame_timer.end_frame_switch_measurement(session_id)
                
        # When: 最近10件取得
        recent = self.frame_timer.get_recent_measurements(10)
        
        # Then: 最新10件が取得される
        assert len(recent) == 10
        assert recent[0].frame_id == "frame_5"  # 最新から10件前
        assert recent[-1].frame_id == "frame_14"  # 最新
        
    def test_slow_frames_detection(self):
        """遅いフレーム検知"""
        # Given: 様々な速度のフレーム
        test_data = [
            ("fast_1", 20.0),
            ("fast_2", 30.0),
            ("slow_1", 60.0),
            ("slow_2", 70.0),
            ("normal", 45.0)
        ]
        
        for frame_id, target_time in test_data:
            session_id = self.frame_timer.start_frame_switch_measurement(frame_id)
            with patch('time.perf_counter') as mock_time:
                start_time = self.frame_timer.active_measurements[session_id].start_time
                mock_time.return_value = start_time + target_time / 1000
                self.frame_timer.end_frame_switch_measurement(session_id)
                
        # When: 45ms閾値で遅いフレーム取得
        slow_frames = self.frame_timer.get_slow_frames(45.0)
        
        # Then: 閾値超過フレームのみ取得
        assert len(slow_frames) == 2
        slow_frame_ids = [result.frame_id for result in slow_frames]
        assert "slow_1" in slow_frame_ids
        assert "slow_2" in slow_frame_ids
        
    def test_statistics_caching(self):
        """統計キャッシュ機能"""
        # Given: 測定データ
        session_id = self.frame_timer.start_frame_switch_measurement("cache_test")
        with patch('time.perf_counter') as mock_time:
            start_time = self.frame_timer.active_measurements[session_id].start_time
            mock_time.return_value = start_time + 0.040
            self.frame_timer.end_frame_switch_measurement(session_id)
            
        # When: 連続で統計取得
        with patch('time.time') as mock_time_time:
            mock_time_time.return_value = 3000.0
            stats1 = self.frame_timer.get_performance_statistics()
            
            # 0.5秒後（キャッシュ有効期間内）
            mock_time_time.return_value = 3000.5
            stats2 = self.frame_timer.get_performance_statistics()
            
        # Then: 同一インスタンス（キャッシュされている）
        assert stats1 is stats2
        
    def test_reset_statistics(self):
        """統計リセット"""
        # Given: 測定データ有り
        session_id = self.frame_timer.start_frame_switch_measurement("reset_test")
        with patch('time.perf_counter') as mock_time:
            start_time = self.frame_timer.active_measurements[session_id].start_time
            mock_time.return_value = start_time + 0.040
            self.frame_timer.end_frame_switch_measurement(session_id)
            
        assert len(self.frame_timer.frame_switch_times) == 1
        
        # When: リセット実行
        self.frame_timer.reset_statistics()
        
        # Then: 統計クリア
        assert len(self.frame_timer.frame_switch_times) == 0
        assert self.frame_timer._stats_cache is None
        
        stats = self.frame_timer.get_performance_statistics()
        assert stats.total_measurements == 0


class TestFrameSwitchResult:
    """FrameSwitchResult データクラステスト"""
    
    def test_result_creation(self):
        """結果作成"""
        result = FrameSwitchResult(
            frame_id="test_frame",
            total_time=45.5,
            cache_time=30.0,
            ui_time=10.0,
            success=True
        )
        
        assert result.frame_id == "test_frame"
        assert result.total_time == 45.5
        assert result.cache_time == 30.0
        assert result.ui_time == 10.0
        assert result.success is True
        assert isinstance(result.timestamp, datetime)
        
    def test_timestamp_auto_generation(self):
        """タイムスタンプ自動生成"""
        before = datetime.now()
        result = FrameSwitchResult(
            frame_id="timestamp_test",
            total_time=40.0,
            cache_time=None,
            ui_time=None,
            success=True
        )
        after = datetime.now()
        
        assert before <= result.timestamp <= after


class TestFramePerformanceStats:
    """FramePerformanceStats データクラステスト"""
    
    def test_stats_to_dict(self):
        """統計辞書変換"""
        stats = FramePerformanceStats(
            total_measurements=100,
            average_time=45.123,
            median_time=44.567,
            min_time=20.1,
            max_time=80.9,
            std_deviation=15.432,
            success_rate=0.856,
            under_50ms_rate=0.92
        )
        
        result_dict = stats.to_dict()
        
        assert result_dict["total_measurements"] == 100
        assert result_dict["average_time"] == 45.123  # 3桁まで
        assert result_dict["success_rate"] == 0.856
        assert all(isinstance(v, (int, float)) for v in result_dict.values())