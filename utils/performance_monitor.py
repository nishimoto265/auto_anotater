import os
import time
import json
import threading
import psutil
import GPUtil
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import deque
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

from utils.logger import Logger


@dataclass
class PerformanceMetrics:
    timestamp: float
    frame_switch_time: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    gpu_percent: Optional[float] = None
    gpu_memory_mb: Optional[float] = None
    process_memory_mb: Optional[float] = None
    thread_count: Optional[int] = None


@dataclass
class BottleneckAlert:
    timestamp: float
    alert_type: str
    severity: str  # 'warning', 'critical'
    message: str
    value: float
    threshold: float


class PerformanceMonitor:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.logger = Logger()
            
            # 設定可能なしきい値
            self.thresholds = {
                'frame_switch_time_ms': 100,  # ミリ秒
                'memory_usage_mb': 2048,      # MB
                'cpu_percent': 80,            # %
                'gpu_percent': 90,            # %
                'gpu_memory_mb': 4096         # MB
            }
            
            # メトリクスの保存
            self.metrics_history = deque(maxlen=1000)  # 最新1000件を保持
            self.alerts_history = deque(maxlen=100)    # 最新100件のアラート
            
            # フレーム切り替え時間の計測用
            self._frame_switch_start = None
            self._last_frame_index = None
            
            # モニタリングスレッド
            self._monitoring_thread = None
            self._stop_monitoring = threading.Event()
            self._monitoring_interval = 1.0  # 秒
            
            # GPU情報のキャッシュ
            self._has_gpu = len(GPUtil.getGPUs()) > 0
            self._process = psutil.Process()
            
            # エクスポート用
            self._export_lock = threading.Lock()
            
            self.logger.info("PerformanceMonitor initialized")
    
    def start_monitoring(self):
        """リアルタイムモニタリングを開始"""
        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._stop_monitoring.clear()
            self._monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitoring_thread.start()
            self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """モニタリングを停止"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5)
            self.logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """バックグラウンドでメトリクスを収集"""
        while not self._stop_monitoring.is_set():
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                self._check_bottlenecks(metrics)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
            
            self._stop_monitoring.wait(self._monitoring_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """現在のパフォーマンスメトリクスを収集"""
        metrics = PerformanceMetrics(timestamp=time.time())
        
        try:
            # CPU使用率
            metrics.cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # メモリ使用量
            memory_info = psutil.virtual_memory()
            metrics.memory_usage_mb = memory_info.used / (1024 ** 2)
            
            # プロセス固有のメモリ
            process_memory = self._process.memory_info()
            metrics.process_memory_mb = process_memory.rss / (1024 ** 2)
            
            # スレッド数
            metrics.thread_count = self._process.num_threads()
            
            # GPU情報（利用可能な場合）
            if self._has_gpu:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]  # 最初のGPUを使用
                        metrics.gpu_percent = gpu.load * 100
                        metrics.gpu_memory_mb = gpu.memoryUsed
                except Exception as e:
                    self.logger.debug(f"GPU metrics collection failed: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
        
        return metrics
    
    def start_frame_switch(self, frame_index: int):
        """フレーム切り替えの開始を記録"""
        self._frame_switch_start = time.time()
        self._last_frame_index = frame_index
    
    def end_frame_switch(self, frame_index: int):
        """フレーム切り替えの終了を記録し、時間を計測"""
        if self._frame_switch_start is None:
            return
        
        switch_time = time.time() - self._frame_switch_start
        self._frame_switch_start = None
        
        # メトリクスを作成して保存
        metrics = self._collect_metrics()
        metrics.frame_switch_time = switch_time
        self.metrics_history.append(metrics)
        
        # ボトルネックをチェック
        self._check_bottlenecks(metrics)
        
        self.logger.debug(f"Frame switch {self._last_frame_index} -> {frame_index}: {switch_time*1000:.2f}ms")
    
    def _check_bottlenecks(self, metrics: PerformanceMetrics):
        """ボトルネックを検出してアラートを生成"""
        alerts = []
        
        # フレーム切り替え時間のチェック
        if metrics.frame_switch_time is not None:
            switch_time_ms = metrics.frame_switch_time * 1000
            if switch_time_ms > self.thresholds['frame_switch_time_ms']:
                severity = 'critical' if switch_time_ms > self.thresholds['frame_switch_time_ms'] * 2 else 'warning'
                alerts.append(BottleneckAlert(
                    timestamp=metrics.timestamp,
                    alert_type='frame_switch_slow',
                    severity=severity,
                    message=f"Frame switch time exceeded threshold: {switch_time_ms:.2f}ms",
                    value=switch_time_ms,
                    threshold=self.thresholds['frame_switch_time_ms']
                ))
        
        # メモリ使用量のチェック
        if metrics.process_memory_mb is not None:
            if metrics.process_memory_mb > self.thresholds['memory_usage_mb']:
                severity = 'critical' if metrics.process_memory_mb > self.thresholds['memory_usage_mb'] * 1.5 else 'warning'
                alerts.append(BottleneckAlert(
                    timestamp=metrics.timestamp,
                    alert_type='high_memory_usage',
                    severity=severity,
                    message=f"Memory usage exceeded threshold: {metrics.process_memory_mb:.2f}MB",
                    value=metrics.process_memory_mb,
                    threshold=self.thresholds['memory_usage_mb']
                ))
        
        # CPU使用率のチェック
        if metrics.cpu_percent is not None:
            if metrics.cpu_percent > self.thresholds['cpu_percent']:
                severity = 'critical' if metrics.cpu_percent > 95 else 'warning'
                alerts.append(BottleneckAlert(
                    timestamp=metrics.timestamp,
                    alert_type='high_cpu_usage',
                    severity=severity,
                    message=f"CPU usage exceeded threshold: {metrics.cpu_percent:.1f}%",
                    value=metrics.cpu_percent,
                    threshold=self.thresholds['cpu_percent']
                ))
        
        # GPU使用率のチェック
        if metrics.gpu_percent is not None:
            if metrics.gpu_percent > self.thresholds['gpu_percent']:
                alerts.append(BottleneckAlert(
                    timestamp=metrics.timestamp,
                    alert_type='high_gpu_usage',
                    severity='warning',
                    message=f"GPU usage exceeded threshold: {metrics.gpu_percent:.1f}%",
                    value=metrics.gpu_percent,
                    threshold=self.thresholds['gpu_percent']
                ))
        
        # アラートを保存してログ出力
        for alert in alerts:
            self.alerts_history.append(alert)
            if alert.severity == 'critical':
                self.logger.warning(alert.message)
            else:
                self.logger.debug(alert.message)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """最新のメトリクスを取得"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_summary(self, duration_seconds: float = 60) -> Dict[str, Any]:
        """指定期間のメトリクスサマリーを取得"""
        current_time = time.time()
        cutoff_time = current_time - duration_seconds
        
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        if not recent_metrics:
            return {}
        
        summary = {
            'duration_seconds': duration_seconds,
            'sample_count': len(recent_metrics),
            'frame_switch_times': {
                'avg_ms': None,
                'max_ms': None,
                'min_ms': None
            },
            'memory_usage': {
                'avg_mb': None,
                'max_mb': None,
                'current_mb': None
            },
            'cpu_usage': {
                'avg_percent': None,
                'max_percent': None,
                'current_percent': None
            },
            'gpu_usage': {
                'avg_percent': None,
                'max_percent': None,
                'current_percent': None
            }
        }
        
        # フレーム切り替え時間の統計
        switch_times = [m.frame_switch_time * 1000 for m in recent_metrics if m.frame_switch_time is not None]
        if switch_times:
            summary['frame_switch_times']['avg_ms'] = sum(switch_times) / len(switch_times)
            summary['frame_switch_times']['max_ms'] = max(switch_times)
            summary['frame_switch_times']['min_ms'] = min(switch_times)
        
        # メモリ使用量の統計
        memory_values = [m.process_memory_mb for m in recent_metrics if m.process_memory_mb is not None]
        if memory_values:
            summary['memory_usage']['avg_mb'] = sum(memory_values) / len(memory_values)
            summary['memory_usage']['max_mb'] = max(memory_values)
            summary['memory_usage']['current_mb'] = memory_values[-1]
        
        # CPU使用率の統計
        cpu_values = [m.cpu_percent for m in recent_metrics if m.cpu_percent is not None]
        if cpu_values:
            summary['cpu_usage']['avg_percent'] = sum(cpu_values) / len(cpu_values)
            summary['cpu_usage']['max_percent'] = max(cpu_values)
            summary['cpu_usage']['current_percent'] = cpu_values[-1]
        
        # GPU使用率の統計
        gpu_values = [m.gpu_percent for m in recent_metrics if m.gpu_percent is not None]
        if gpu_values:
            summary['gpu_usage']['avg_percent'] = sum(gpu_values) / len(gpu_values)
            summary['gpu_usage']['max_percent'] = max(gpu_values)
            summary['gpu_usage']['current_percent'] = gpu_values[-1]
        
        return summary
    
    def export_performance_report(self, filepath: str, format: str = 'json'):
        """パフォーマンスレポートをエクスポート"""
        with self._export_lock:
            try:
                report = {
                    'export_time': datetime.now().isoformat(),
                    'thresholds': self.thresholds,
                    'summary': {
                        'last_minute': self.get_metrics_summary(60),
                        'last_5_minutes': self.get_metrics_summary(300),
                        'last_15_minutes': self.get_metrics_summary(900)
                    },
                    'metrics_history': [asdict(m) for m in self.metrics_history],
                    'alerts_history': [asdict(a) for a in self.alerts_history]
                }
                
                if format == 'json':
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(report, f, indent=2, ensure_ascii=False)
                elif format == 'csv':
                    # CSV形式でのエクスポート（メトリクスのみ）
                    import csv
                    csv_filepath = filepath.replace('.json', '.csv')
                    with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
                        if self.metrics_history:
                            fieldnames = list(asdict(self.metrics_history[0]).keys())
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            for metric in self.metrics_history:
                                writer.writerow(asdict(metric))
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                self.logger.info(f"Performance report exported to {filepath}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to export performance report: {e}")
                return False
    
    def set_threshold(self, metric_name: str, value: float):
        """しきい値を設定"""
        if metric_name in self.thresholds:
            old_value = self.thresholds[metric_name]
            self.thresholds[metric_name] = value
            self.logger.info(f"Threshold '{metric_name}' changed from {old_value} to {value}")
        else:
            self.logger.warning(f"Unknown threshold metric: {metric_name}")
    
    def get_alerts(self, severity: Optional[str] = None) -> List[BottleneckAlert]:
        """アラート履歴を取得"""
        if severity:
            return [a for a in self.alerts_history if a.severity == severity]
        return list(self.alerts_history)
    
    def clear_history(self):
        """履歴をクリア"""
        self.metrics_history.clear()
        self.alerts_history.clear()
        self.logger.info("Performance history cleared")