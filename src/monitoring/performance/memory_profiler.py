"""
Memory Profiler - メモリ使用量監視・プロファイラー

20GB上限監視・メモリリーク検知・ガベージコレクション効率監視
Cache層の大容量メモリ使用を継続監視し、パフォーマンス劣化を防止。
"""

import time
import threading
import tracemalloc
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import gc
import psutil
import os
from scipy import stats


@dataclass
class MemoryUsage:
    """メモリ使用量データ"""
    rss: int  # 実使用メモリ (bytes)
    vms: int  # 仮想メモリ (bytes)
    percent: float  # プロセスメモリ使用率
    system_total: int  # システム総メモリ
    system_available: int  # システム利用可能メモリ
    system_used: int  # システム使用メモリ
    timestamp: datetime
    
    @property
    def rss_gb(self) -> float:
        """実使用メモリをGBで返却"""
        return self.rss / (1024 ** 3)
    
    @property
    def vms_gb(self) -> float:
        """仮想メモリをGBで返却"""
        return self.vms / (1024 ** 3)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返却"""
        return {
            'rss_gb': round(self.rss_gb, 3),
            'vms_gb': round(self.vms_gb, 3),
            'percent': round(self.percent, 2),
            'system_total_gb': round(self.system_total / (1024 ** 3), 3),
            'system_available_gb': round(self.system_available / (1024 ** 3), 3),
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class MemoryLeakResult:
    """メモリリーク検知結果"""
    leak_detected: bool
    slope: float = 0.0  # bytes/second
    correlation: float = 0.0  # 相関係数
    p_value: float = 1.0  # p値
    growth_rate_mb_per_sec: float = 0.0  # MB/秒
    estimated_time_to_limit: Optional[float] = None  # 上限到達予測時間（秒）
    reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返却"""
        return {
            'leak_detected': self.leak_detected,
            'growth_rate_mb_per_sec': round(self.growth_rate_mb_per_sec, 3),
            'correlation': round(self.correlation, 3),
            'p_value': round(self.p_value, 4),
            'estimated_time_to_limit_hours': round(self.estimated_time_to_limit / 3600, 2) if self.estimated_time_to_limit else None,
            'reason': self.reason
        }


@dataclass
class GCStats:
    """ガベージコレクション統計"""
    collections: List[int]  # 世代別回収回数
    collected: List[int]    # 世代別回収オブジェクト数
    uncollectable: int      # 回収不可オブジェクト数
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返却"""
        return {
            'gen0_collections': self.collections[0] if len(self.collections) > 0 else 0,
            'gen1_collections': self.collections[1] if len(self.collections) > 1 else 0,
            'gen2_collections': self.collections[2] if len(self.collections) > 2 else 0,
            'gen0_collected': self.collected[0] if len(self.collected) > 0 else 0,
            'gen1_collected': self.collected[1] if len(self.collected) > 1 else 0,
            'gen2_collected': self.collected[2] if len(self.collected) > 2 else 0,
            'uncollectable': self.uncollectable
        }


class MemoryProfiler:
    """
    メモリ使用量監視・プロファイラー
    
    監視項目:
    - 総メモリ使用量（20GB上限監視）
    - Agent別メモリ使用量
    - メモリリーク検知
    - ガベージコレクション効率
    
    性能要件:
    - 監視オーバーヘッド: 5ms以下
    - 監視間隔: 1秒
    - 履歴保持: 1時間分（3600記録）
    """
    
    def __init__(self, data_bus=None):
        """
        初期化
        
        Args:
            data_bus: Agent間通信用データバス
        """
        # 制限・閾値設定
        self.memory_limit = 20 * 1024 ** 3  # 20GB (bytes)
        self.warning_threshold = 18 * 1024 ** 3  # 18GB警告
        self.critical_threshold = 16 * 1024 ** 3  # 16GB注意
        
        # 監視設定
        self.monitoring_interval = 1.0  # 1秒間隔
        self.memory_history = deque(maxlen=3600)  # 1時間分記録
        
        # スレッド制御
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_monitoring = False
        self._lock = threading.Lock()
        
        # Data Bus接続
        self.data_bus = data_bus
        
        # プロセス情報
        self.process = psutil.Process(os.getpid())
        
        # tracemalloc設定
        self.tracemalloc_enabled = False
        
        # GC統計
        self._previous_gc_stats = None
        
    def start_monitoring(self):
        """メモリ監視開始"""
        with self._lock:
            if self.is_monitoring:
                return
                
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_worker,
                name="MemoryProfiler-Monitor"
            )
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
    def stop_monitoring(self):
        """メモリ監視停止"""
        with self._lock:
            if not self.is_monitoring:
                return
                
            self.is_monitoring = False
            
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
            
    def enable_detailed_tracking(self):
        """詳細メモリ追跡有効化"""
        if not self.tracemalloc_enabled:
            tracemalloc.start()
            self.tracemalloc_enabled = True
            
    def disable_detailed_tracking(self):
        """詳細メモリ追跡無効化"""
        if self.tracemalloc_enabled:
            tracemalloc.stop()
            self.tracemalloc_enabled = False
            
    def get_current_memory_usage(self) -> MemoryUsage:
        """
        現在メモリ使用量取得
        
        Returns:
            MemoryUsage: 現在のメモリ使用状況
        """
        try:
            memory_info = self.process.memory_info()
            system_memory = psutil.virtual_memory()
            
            return MemoryUsage(
                rss=memory_info.rss,
                vms=memory_info.vms,
                percent=self.process.memory_percent(),
                system_total=system_memory.total,
                system_available=system_memory.available,
                system_used=system_memory.used,
                timestamp=datetime.now()
            )
        except psutil.Error as e:
            raise RuntimeError(f"Failed to get memory usage: {e}")
            
    def detect_memory_leak(self, window_size: int = 300) -> MemoryLeakResult:
        """
        メモリリーク検知（5分間ウィンドウ）
        
        Args:
            window_size: 検知ウィンドウサイズ（秒）
            
        Returns:
            MemoryLeakResult: リーク検知結果
        """
        if len(self.memory_history) < window_size:
            return MemoryLeakResult(
                leak_detected=False,
                reason=f"Insufficient data: {len(self.memory_history)}/{window_size}"
            )
            
        # 最近の記録を分析
        recent_usage = list(self.memory_history)[-window_size:]
        memory_values = [usage.rss for usage in recent_usage]
        
        # 線形回帰で傾向分析
        x = list(range(len(memory_values)))
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, memory_values)
        except Exception as e:
            return MemoryLeakResult(
                leak_detected=False,
                reason=f"Regression analysis failed: {e}"
            )
            
        # リーク判定基準
        leak_threshold = 1024 * 1024  # 1MB/秒
        correlation_threshold = 0.7
        significance_threshold = 0.05
        
        leak_detected = (
            slope > leak_threshold and       # 十分な増加率
            r_value > correlation_threshold and  # 高い相関
            p_value < significance_threshold     # 統計的有意性
        )
        
        # 上限到達予測時間
        estimated_time = None
        if slope > 0:
            current_memory = memory_values[-1]
            remaining_memory = self.memory_limit - current_memory
            if remaining_memory > 0:
                estimated_time = remaining_memory / slope  # 秒
        
        return MemoryLeakResult(
            leak_detected=leak_detected,
            slope=slope,
            correlation=r_value,
            p_value=p_value,
            growth_rate_mb_per_sec=slope / (1024 * 1024),
            estimated_time_to_limit=estimated_time,
            reason="Analysis completed"
        )
        
    def get_gc_statistics(self) -> GCStats:
        """
        ガベージコレクション統計取得
        
        Returns:
            GCStats: GC統計情報
        """
        gc_stats = gc.get_stats()
        
        collections = [stat.get('collections', 0) for stat in gc_stats]
        collected = [stat.get('collected', 0) for stat in gc_stats]
        uncollectable = len(gc.garbage)
        
        return GCStats(
            collections=collections,
            collected=collected,
            uncollectable=uncollectable
        )
        
    def force_garbage_collection(self) -> int:
        """
        強制ガベージコレクション実行
        
        Returns:
            int: 回収されたオブジェクト数
        """
        return gc.collect()
        
    def get_memory_statistics(self) -> Dict[str, Any]:
        """
        メモリ統計取得
        
        Returns:
            Dict[str, Any]: メモリ統計情報
        """
        if not self.memory_history:
            return {}
            
        current_usage = self.memory_history[-1]
        memory_values = [usage.rss for usage in self.memory_history]
        
        stats_dict = {
            'current_usage': current_usage.to_dict(),
            'history_length': len(self.memory_history),
            'max_usage_gb': max(memory_values) / (1024 ** 3),
            'min_usage_gb': min(memory_values) / (1024 ** 3),
            'avg_usage_gb': sum(memory_values) / len(memory_values) / (1024 ** 3),
            'limit_gb': self.memory_limit / (1024 ** 3),
            'usage_ratio': current_usage.rss / self.memory_limit,
            'gc_stats': self.get_gc_statistics().to_dict()
        }
        
        return stats_dict
        
    def get_top_memory_consumers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        メモリ消費上位オブジェクト取得（tracemalloc必須）
        
        Args:
            limit: 取得件数
            
        Returns:
            List[Dict[str, Any]]: メモリ消費上位オブジェクト
        """
        if not self.tracemalloc_enabled:
            return []
            
        try:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            consumers = []
            for stat in top_stats[:limit]:
                consumers.append({
                    'filename': stat.traceback.format()[0],
                    'size_mb': stat.size / (1024 * 1024),
                    'count': stat.count
                })
                
            return consumers
        except Exception:
            return []
            
    def _monitoring_worker(self):
        """メモリ監視ワーカー"""
        while self.is_monitoring:
            try:
                start_time = time.perf_counter()
                
                # メモリ使用量記録
                memory_usage = self.get_current_memory_usage()
                self.memory_history.append(memory_usage)
                
                # 警告チェック
                self._check_and_emit_warnings(memory_usage)
                
                # リークチェック（5分毎）
                if len(self.memory_history) % 300 == 0:
                    leak_result = self.detect_memory_leak()
                    if leak_result.leak_detected:
                        self._emit_memory_leak_alert(leak_result)
                        
                # 監視オーバーヘッド制御
                elapsed_time = time.perf_counter() - start_time
                sleep_time = max(0, self.monitoring_interval - elapsed_time)
                time.sleep(sleep_time)
                
            except Exception as e:
                self._log_monitoring_error(e)
                time.sleep(self.monitoring_interval)
                
    def _check_and_emit_warnings(self, memory_usage: MemoryUsage):
        """
        警告チェック・発信
        
        Args:
            memory_usage: メモリ使用量データ
        """
        severity = self._determine_memory_severity(memory_usage.rss)
        
        if severity and self.data_bus:
            warning_data = {
                "metric_name": "memory_usage",
                "value": memory_usage.rss,
                "threshold": self.memory_limit,
                "usage_gb": memory_usage.rss_gb,
                "limit_gb": self.memory_limit / (1024 ** 3),
                "usage_ratio": memory_usage.rss / self.memory_limit,
                "severity": severity,
                "timestamp": memory_usage.timestamp.isoformat()
            }
            
            self.data_bus.publish("performance_warning", warning_data)
            
    def _emit_memory_leak_alert(self, leak_result: MemoryLeakResult):
        """
        メモリリークアラート発信
        
        Args:
            leak_result: リーク検知結果
        """
        if self.data_bus:
            alert_data = {
                "metric_name": "memory_leak",
                "severity": "error",
                "leak_details": leak_result.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            self.data_bus.publish("performance_warning", alert_data)
            
    def _determine_memory_severity(self, memory_bytes: int) -> Optional[str]:
        """
        メモリ使用量重要度判定
        
        Args:
            memory_bytes: メモリ使用量（バイト）
            
        Returns:
            Optional[str]: 重要度
        """
        if memory_bytes > self.memory_limit:
            return "error"
        elif memory_bytes > self.warning_threshold:
            return "warning"
        elif memory_bytes > self.critical_threshold:
            return "info"
        else:
            return None
            
    def _log_monitoring_error(self, error: Exception):
        """
        監視エラーログ記録
        
        Args:
            error: 発生した例外
        """
        # 簡易エラーログ（DebugLoggerがあれば連携）
        print(f"MemoryProfiler error: {error}")
        
    def get_monitoring_overhead(self) -> float:
        """
        監視オーバーヘッド測定
        
        Returns:
            float: 監視オーバーヘッド（ミリ秒）
        """
        start_time = time.perf_counter()
        _ = self.get_current_memory_usage()
        end_time = time.perf_counter()
        
        return (end_time - start_time) * 1000  # ms