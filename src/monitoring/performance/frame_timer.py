"""
Frame Timer - フレーム切り替え時間測定（最重要監視）

Agent8 Monitoring の最重要コンポーネント。
フレーム切り替え50ms以下を確実に監視し、性能劣化を早期発見。
"""

import time
import uuid
import statistics
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List, Any


@dataclass
class FrameSwitchMeasurement:
    """フレーム切り替え測定データ"""
    session_id: str
    frame_id: str
    start_time: float
    cache_start_time: Optional[float] = None
    cache_end_time: Optional[float] = None
    ui_start_time: Optional[float] = None
    ui_end_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class FrameSwitchResult:
    """フレーム切り替え測定結果"""
    frame_id: str
    total_time: float  # ms
    cache_time: Optional[float]  # ms
    ui_time: Optional[float]  # ms
    success: bool
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class FramePerformanceStats:
    """フレーム切り替え性能統計"""
    total_measurements: int = 0
    average_time: float = 0.0
    median_time: float = 0.0
    min_time: float = 0.0
    max_time: float = 0.0
    std_deviation: float = 0.0
    success_rate: float = 0.0
    under_50ms_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """統計を辞書形式で返却"""
        return {
            'total_measurements': self.total_measurements,
            'average_time': round(self.average_time, 3),
            'median_time': round(self.median_time, 3),
            'min_time': round(self.min_time, 3),
            'max_time': round(self.max_time, 3),
            'std_deviation': round(self.std_deviation, 3),
            'success_rate': round(self.success_rate, 3),
            'under_50ms_rate': round(self.under_50ms_rate, 3)
        }


class MonitoringError(Exception):
    """監視層専用例外"""
    pass


class FrameTimer:
    """
    フレーム切り替え時間測定（最重要監視）
    
    監視項目:
    - フレーム切り替え時間（50ms以下監視）
    - Cache層応答時間
    - UI更新時間
    - 全体レスポンス時間
    
    性能要件:
    - 測定オーバーヘッド: 1ms以下
    - 同時測定セッション: 最大10セッション
    - 履歴保持: 直近1000回
    """
    
    def __init__(self, data_bus=None):
        """
        初期化
        
        Args:
            data_bus: Agent間通信用データバス
        """
        self.frame_switch_times = deque(maxlen=1000)  # 直近1000回記録
        self.active_measurements: Dict[str, FrameSwitchMeasurement] = {}
        
        # 閾値設定
        self.performance_threshold = 50.0  # 50ms閾値（絶対要件）
        self.warning_threshold = 45.0      # 45ms警告
        self.critical_threshold = 40.0     # 40ms注意
        
        # Data Bus接続
        self.data_bus = data_bus
        
        # 統計キャッシュ
        self._stats_cache = None
        self._stats_cache_time = 0
        self.stats_cache_duration = 1.0  # 1秒間キャッシュ
        
    def start_frame_switch_measurement(self, frame_id: str) -> str:
        """
        フレーム切り替え測定開始
        
        Args:
            frame_id: 切り替え先フレームID
            
        Returns:
            str: 測定セッションID
            
        Raises:
            MonitoringError: セッション数上限超過
        """
        # セッション数制限チェック
        if len(self.active_measurements) >= 10:
            raise MonitoringError("Maximum concurrent measurement sessions exceeded")
            
        session_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        
        measurement = FrameSwitchMeasurement(
            session_id=session_id,
            frame_id=frame_id,
            start_time=start_time
        )
        
        self.active_measurements[session_id] = measurement
        return session_id
        
    def record_cache_timing(self, session_id: str, cache_start: bool = True):
        """
        Cache層タイミング記録
        
        Args:
            session_id: 測定セッションID
            cache_start: True=開始時刻、False=終了時刻
        """
        if session_id not in self.active_measurements:
            return  # セッション無効時は無視（エラーログ出力は他コンポーネント）
            
        measurement = self.active_measurements[session_id]
        current_time = time.perf_counter()
        
        if cache_start:
            measurement.cache_start_time = current_time
        else:
            measurement.cache_end_time = current_time
                
    def record_ui_timing(self, session_id: str, ui_start: bool = True):
        """
        UI層タイミング記録
        
        Args:
            session_id: 測定セッションID
            ui_start: True=開始時刻、False=終了時刻
        """
        if session_id not in self.active_measurements:
            return  # セッション無効時は無視
            
        measurement = self.active_measurements[session_id]
        current_time = time.perf_counter()
        
        if ui_start:
            measurement.ui_start_time = current_time
        else:
            measurement.ui_end_time = current_time
                
    def end_frame_switch_measurement(self, session_id: str) -> FrameSwitchResult:
        """
        フレーム切り替え測定終了
        
        Args:
            session_id: 測定セッションID
            
        Returns:
            FrameSwitchResult: 測定結果
            
        Raises:
            MonitoringError: セッション無効
        """
        if session_id not in self.active_measurements:
            raise MonitoringError(f"Measurement session not found: {session_id}")
            
        measurement = self.active_measurements[session_id]
        measurement.end_time = time.perf_counter()
        
        # 時間計算（ミリ秒）
        total_time = (measurement.end_time - measurement.start_time) * 1000
        cache_time = None
        ui_time = None
        
        if measurement.cache_start_time and measurement.cache_end_time:
            cache_time = (measurement.cache_end_time - measurement.cache_start_time) * 1000
            
        if measurement.ui_start_time and measurement.ui_end_time:
            ui_time = (measurement.ui_end_time - measurement.ui_start_time) * 1000
            
        # 結果作成
        result = FrameSwitchResult(
            frame_id=measurement.frame_id,
            total_time=total_time,
            cache_time=cache_time,
            ui_time=ui_time,
            success=total_time <= self.performance_threshold
        )
        
        # 履歴記録
        self.frame_switch_times.append(result)
        
        # 警告チェック・発信
        self._check_and_emit_warnings(result)
            
        # セッションクリーンアップ
        del self.active_measurements[session_id]
        
        # 統計キャッシュ無効化
        self._stats_cache = None
        
        return result
        
    def get_performance_statistics(self) -> FramePerformanceStats:
        """
        フレーム切り替え性能統計
        
        Returns:
            FramePerformanceStats: 性能統計
        """
        # キャッシュチェック
        current_time = time.time()
        if (self._stats_cache and 
            current_time - self._stats_cache_time < self.stats_cache_duration):
            return self._stats_cache
            
        if not self.frame_switch_times:
            return FramePerformanceStats()
            
        times = [result.total_time for result in self.frame_switch_times]
        
        stats = FramePerformanceStats(
            total_measurements=len(times),
            average_time=statistics.mean(times),
            median_time=statistics.median(times),
            min_time=min(times),
            max_time=max(times),
            std_deviation=statistics.stdev(times) if len(times) > 1 else 0.0,
            success_rate=sum(1 for result in self.frame_switch_times if result.success) / len(times),
            under_50ms_rate=sum(1 for time in times if time <= 50.0) / len(times)
        )
        
        # キャッシュ更新
        self._stats_cache = stats
        self._stats_cache_time = current_time
        
        return stats
        
    def get_recent_measurements(self, count: int = 10) -> List[FrameSwitchResult]:
        """
        最近の測定結果取得
        
        Args:
            count: 取得件数
            
        Returns:
            List[FrameSwitchResult]: 最近の測定結果
        """
        return list(self.frame_switch_times)[-count:]
        
    def get_slow_frames(self, threshold_ms: float = 45.0) -> List[FrameSwitchResult]:
        """
        遅いフレーム切り替え取得
        
        Args:
            threshold_ms: 閾値（ミリ秒）
            
        Returns:
            List[FrameSwitchResult]: 閾値超過の測定結果
        """
        return [result for result in self.frame_switch_times 
                if result.total_time > threshold_ms]
        
    def reset_statistics(self):
        """統計リセット"""
        self.frame_switch_times.clear()
        self._stats_cache = None
        
    def _check_and_emit_warnings(self, result: FrameSwitchResult):
        """
        警告チェック・発信
        
        Args:
            result: 測定結果
        """
        severity = self._determine_severity(result.total_time)
        
        if severity and self.data_bus:
            warning_data = {
                "metric_name": "frame_switching_time",
                "value": result.total_time,
                "threshold": self.performance_threshold,
                "frame_id": result.frame_id,
                "severity": severity,
                "cache_time": result.cache_time,
                "ui_time": result.ui_time,
                "timestamp": result.timestamp.isoformat()
            }
            
            self.data_bus.publish("performance_warning", warning_data)
            
    def _determine_severity(self, time_ms: float) -> Optional[str]:
        """
        重要度判定
        
        Args:
            time_ms: 測定時間（ミリ秒）
            
        Returns:
            Optional[str]: 重要度（"info"/"warning"/"error"）
        """
        if time_ms > self.performance_threshold:
            return "error"
        elif time_ms > self.warning_threshold:
            return "warning"
        elif time_ms > self.critical_threshold:
            return "info"
        else:
            return None
            
    def get_measurement_overhead(self) -> float:
        """
        測定オーバーヘッド計算
        
        Returns:
            float: 測定オーバーヘッド（ミリ秒）
        """
        # 空測定でオーバーヘッド計算
        start_time = time.perf_counter()
        session_id = str(uuid.uuid4())
        measurement = FrameSwitchMeasurement(
            session_id=session_id,
            frame_id="overhead_test",
            start_time=start_time
        )
        end_time = time.perf_counter()
        
        return (end_time - start_time) * 1000  # ms