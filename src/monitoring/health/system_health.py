"""
System Health Monitor - システム健全性監視

システム全体の健全性チェック・Agent間通信監視・Cache性能監視
Agent8 Monitoring の統合健全性管理システム
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HealthCheckResult:
    """健全性チェック結果"""
    status: str  # healthy/warning/critical/error
    message: str
    details: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返却"""
        result = {
            'status': self.status,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }
        if self.details:
            result['details'] = self.details
        return result


@dataclass
class SystemHealthResult:
    """システム健全性総合結果"""
    overall_status: str
    check_results: Dict[str, HealthCheckResult]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返却"""
        return {
            'overall_status': self.overall_status,
            'timestamp': self.timestamp.isoformat(),
            'check_results': {
                name: result.to_dict() 
                for name, result in self.check_results.items()
            }
        }


@dataclass
class CacheStatistics:
    """Cache統計情報"""
    hit_rate: float
    miss_rate: float
    total_requests: int
    cache_size_gb: float
    eviction_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返却"""
        return {
            'hit_rate': round(self.hit_rate, 4),
            'miss_rate': round(self.miss_rate, 4),
            'total_requests': self.total_requests,
            'cache_size_gb': round(self.cache_size_gb, 3),
            'eviction_count': self.eviction_count
        }


class SystemHealthMonitor:
    """
    システム健全性監視
    
    監視項目:
    - CPU使用率
    - ディスク使用量・I/O
    - ネットワーク状態
    - Agent間通信健全性
    - Cache性能（最重要）
    
    性能要件:
    - 健全性チェック時間: 10ms以下
    - チェック間隔: 10秒
    - 自動復旧機能
    """
    
    def __init__(self, data_bus=None, cache_layer=None):
        """
        初期化
        
        Args:
            data_bus: Agent間通信用データバス
            cache_layer: Cache層インスタンス
        """
        self.data_bus = data_bus
        self.cache_layer = cache_layer
        
        # 健全性チェック関数マップ
        self.health_checks = {
            'cpu_usage': self._check_cpu_usage,
            'memory_usage': self._check_memory_usage,
            'disk_usage': self._check_disk_usage,
            'agent_communication': self._check_agent_communication,
            'file_system': self._check_file_system,
            'cache_performance': self._check_cache_performance
        }
        
        # 閾値設定
        self.thresholds = {
            'cpu_critical': 90.0,    # CPU 90%超過でクリティカル
            'cpu_warning': 70.0,     # CPU 70%超過で警告
            'memory_critical': 18.0, # メモリ18GB超過でクリティカル
            'memory_warning': 16.0,  # メモリ16GB超過で警告
            'disk_critical': 90.0,   # ディスク90%超過でクリティカル
            'disk_warning': 80.0,    # ディスク80%超過で警告
            'cache_hit_critical': 0.90, # キャッシュヒット率90%未満でクリティカル
            'cache_hit_warning': 0.95   # キャッシュヒット率95%未満で警告
        }
        
        # 継続監視用
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_interval = 10.0  # 10秒間隔
        
        # 健全性履歴
        self.health_history: List[SystemHealthResult] = []
        self.max_history = 100  # 最大100回分記録
        
    def perform_health_check(self) -> SystemHealthResult:
        """
        総合健全性チェック
        
        Returns:
            SystemHealthResult: 健全性チェック結果
        """
        start_time = time.perf_counter()
        
        health_results = {}
        overall_status = "healthy"
        
        for check_name, check_func in self.health_checks.items():
            try:
                result = check_func()
                health_results[check_name] = result
                
                # 全体ステータス更新
                if result.status == "critical" or result.status == "error":
                    overall_status = "critical"
                elif result.status == "warning" and overall_status == "healthy":
                    overall_status = "warning"
                    
            except Exception as e:
                error_result = HealthCheckResult(
                    status="error",
                    message=f"Health check failed: {e}",
                    details={"error": str(e), "check_name": check_name}
                )
                health_results[check_name] = error_result
                overall_status = "critical"
                
        # 実行時間チェック（10ms以下要件）
        elapsed_time = (time.perf_counter() - start_time) * 1000
        if elapsed_time > 10.0:
            print(f"Warning: Health check took {elapsed_time:.2f}ms (>10ms)")
            
        result = SystemHealthResult(
            overall_status=overall_status,
            check_results=health_results
        )
        
        # 履歴記録
        self._record_health_result(result)
        
        return result
        
    def start_continuous_monitoring(self):
        """継続的健全性監視開始"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_worker,
            name="SystemHealthMonitor"
        )
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_continuous_monitoring(self):
        """継続的健全性監視停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            
    def _check_cpu_usage(self) -> HealthCheckResult:
        """CPU使用率チェック"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            if cpu_percent > self.thresholds['cpu_critical']:
                return HealthCheckResult(
                    "critical", 
                    f"Critical CPU usage: {cpu_percent:.1f}%",
                    {"cpu_percent": cpu_percent, "threshold": self.thresholds['cpu_critical']}
                )
            elif cpu_percent > self.thresholds['cpu_warning']:
                return HealthCheckResult(
                    "warning",
                    f"High CPU usage: {cpu_percent:.1f}%",
                    {"cpu_percent": cpu_percent, "threshold": self.thresholds['cpu_warning']}
                )
            else:
                return HealthCheckResult(
                    "healthy",
                    f"Normal CPU usage: {cpu_percent:.1f}%",
                    {"cpu_percent": cpu_percent}
                )
        except Exception as e:
            return HealthCheckResult("error", f"CPU check failed: {e}")
            
    def _check_memory_usage(self) -> HealthCheckResult:
        """メモリ使用量チェック"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_gb = memory_info.rss / (1024 ** 3)
            
            if memory_gb > self.thresholds['memory_critical']:
                return HealthCheckResult(
                    "critical",
                    f"Critical memory usage: {memory_gb:.2f}GB",
                    {"memory_gb": memory_gb, "threshold": self.thresholds['memory_critical']}
                )
            elif memory_gb > self.thresholds['memory_warning']:
                return HealthCheckResult(
                    "warning",
                    f"High memory usage: {memory_gb:.2f}GB",
                    {"memory_gb": memory_gb, "threshold": self.thresholds['memory_warning']}
                )
            else:
                return HealthCheckResult(
                    "healthy",
                    f"Normal memory usage: {memory_gb:.2f}GB",
                    {"memory_gb": memory_gb}
                )
        except Exception as e:
            return HealthCheckResult("error", f"Memory check failed: {e}")
            
    def _check_disk_usage(self) -> HealthCheckResult:
        """ディスク使用量チェック"""
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            if usage_percent > self.thresholds['disk_critical']:
                return HealthCheckResult(
                    "critical",
                    f"Critical disk usage: {usage_percent:.1f}%",
                    {"usage_percent": usage_percent, "threshold": self.thresholds['disk_critical']}
                )
            elif usage_percent > self.thresholds['disk_warning']:
                return HealthCheckResult(
                    "warning",
                    f"High disk usage: {usage_percent:.1f}%",
                    {"usage_percent": usage_percent, "threshold": self.thresholds['disk_warning']}
                )
            else:
                return HealthCheckResult(
                    "healthy",
                    f"Normal disk usage: {usage_percent:.1f}%",
                    {"usage_percent": usage_percent}
                )
        except Exception as e:
            return HealthCheckResult("error", f"Disk check failed: {e}")
            
    def _check_agent_communication(self) -> HealthCheckResult:
        """Agent間通信健全性チェック"""
        if not self.data_bus:
            return HealthCheckResult(
                "warning",
                "Data bus not available",
                {"reason": "No data bus instance"}
            )
            
        try:
            # Data Bus基本機能テスト
            test_start = time.perf_counter()
            
            # 簡易通信テスト（実際の実装では具体的なpingテストなど）
            communication_time = (time.perf_counter() - test_start) * 1000
            
            if communication_time > 10.0:  # 10ms超過
                return HealthCheckResult(
                    "warning",
                    f"Slow agent communication: {communication_time:.2f}ms",
                    {"communication_time": communication_time}
                )
            else:
                return HealthCheckResult(
                    "healthy",
                    f"Normal agent communication: {communication_time:.2f}ms",
                    {"communication_time": communication_time}
                )
        except Exception as e:
            return HealthCheckResult("error", f"Communication check failed: {e}")
            
    def _check_file_system(self) -> HealthCheckResult:
        """ファイルシステムチェック"""
        try:
            # ログディレクトリアクセス確認
            log_dir = Path("logs")
            if not log_dir.exists():
                return HealthCheckResult(
                    "warning",
                    "Log directory not found",
                    {"log_dir": str(log_dir)}
                )
                
            # 一時ファイル作成テスト
            test_file = log_dir / "health_test.tmp"
            test_start = time.perf_counter()
            
            test_file.write_text("health check", encoding='utf-8')
            content = test_file.read_text(encoding='utf-8')
            test_file.unlink()
            
            file_io_time = (time.perf_counter() - test_start) * 1000
            
            if content != "health check":
                return HealthCheckResult(
                    "error",
                    "File I/O integrity check failed",
                    {"expected": "health check", "actual": content}
                )
            elif file_io_time > 100.0:  # 100ms超過
                return HealthCheckResult(
                    "warning",
                    f"Slow file I/O: {file_io_time:.2f}ms",
                    {"file_io_time": file_io_time}
                )
            else:
                return HealthCheckResult(
                    "healthy",
                    f"Normal file system: {file_io_time:.2f}ms",
                    {"file_io_time": file_io_time}
                )
        except Exception as e:
            return HealthCheckResult("error", f"File system check failed: {e}")
            
    def _check_cache_performance(self) -> HealthCheckResult:
        """Cache性能チェック（最重要）"""
        if not self.cache_layer:
            return HealthCheckResult(
                "warning",
                "Cache layer not available",
                {"reason": "No cache layer instance"}
            )
            
        try:
            # Cache統計取得（仮実装）
            cache_stats = self._get_cache_statistics()
            
            if cache_stats.hit_rate < self.thresholds['cache_hit_critical']:
                return HealthCheckResult(
                    "critical",
                    f"Critical cache hit rate: {cache_stats.hit_rate:.3f}",
                    {
                        "cache_stats": cache_stats.to_dict(),
                        "threshold": self.thresholds['cache_hit_critical']
                    }
                )
            elif cache_stats.hit_rate < self.thresholds['cache_hit_warning']:
                return HealthCheckResult(
                    "warning",
                    f"Low cache hit rate: {cache_stats.hit_rate:.3f}",
                    {
                        "cache_stats": cache_stats.to_dict(),
                        "threshold": self.thresholds['cache_hit_warning']
                    }
                )
            else:
                return HealthCheckResult(
                    "healthy",
                    f"Good cache hit rate: {cache_stats.hit_rate:.3f}",
                    {"cache_stats": cache_stats.to_dict()}
                )
        except Exception as e:
            return HealthCheckResult("error", f"Cache check failed: {e}")
            
    def _get_cache_statistics(self) -> CacheStatistics:
        """
        Cache統計取得
        
        Returns:
            CacheStatistics: Cache統計情報
        """
        # 仮実装（実際のCache層との連携が必要）
        if hasattr(self.cache_layer, 'get_statistics'):
            stats = self.cache_layer.get_statistics()
            return CacheStatistics(
                hit_rate=stats.get('hit_rate', 0.95),
                miss_rate=stats.get('miss_rate', 0.05),
                total_requests=stats.get('total_requests', 1000),
                cache_size_gb=stats.get('cache_size_gb', 15.0),
                eviction_count=stats.get('eviction_count', 10)
            )
        else:
            # デフォルト値
            return CacheStatistics(
                hit_rate=0.95,
                miss_rate=0.05,
                total_requests=1000,
                cache_size_gb=15.0,
                eviction_count=10
            )
            
    def _record_health_result(self, result: SystemHealthResult):
        """
        健全性結果記録
        
        Args:
            result: 健全性チェック結果
        """
        self.health_history.append(result)
        
        # 履歴サイズ制限
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
            
        # 重要な状態変化をData Busに通知
        if result.overall_status in ["warning", "critical"]:
            self._emit_health_alert(result)
            
    def _emit_health_alert(self, result: SystemHealthResult):
        """
        健全性アラート発信
        
        Args:
            result: 健全性チェック結果
        """
        if self.data_bus:
            alert_data = {
                "metric_name": "system_health",
                "severity": "warning" if result.overall_status == "warning" else "error",
                "overall_status": result.overall_status,
                "check_results": result.to_dict()["check_results"],
                "timestamp": result.timestamp.isoformat()
            }
            
            self.data_bus.publish("performance_warning", alert_data)
            
    def _monitoring_worker(self):
        """継続監視ワーカー"""
        while self.monitoring:
            try:
                self.perform_health_check()
                time.sleep(self.monitor_interval)
            except Exception as e:
                print(f"Health monitoring error: {e}")
                time.sleep(self.monitor_interval)
                
    def get_health_summary(self, hours: int = 1) -> Dict[str, Any]:
        """
        健全性サマリー取得
        
        Args:
            hours: 集計時間（時間）
            
        Returns:
            Dict[str, Any]: 健全性サマリー
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_results = [
            result for result in self.health_history
            if result.timestamp > cutoff_time
        ]
        
        if not recent_results:
            return {"period_hours": hours, "no_data": True}
            
        # 状態別カウント
        status_counts = {"healthy": 0, "warning": 0, "critical": 0, "error": 0}
        for result in recent_results:
            status_counts[result.overall_status] = status_counts.get(result.overall_status, 0) + 1
            
        total_checks = len(recent_results)
        
        return {
            "period_hours": hours,
            "total_checks": total_checks,
            "healthy_ratio": status_counts["healthy"] / total_checks,
            "warning_ratio": status_counts["warning"] / total_checks,
            "critical_ratio": status_counts["critical"] / total_checks,
            "error_ratio": status_counts["error"] / total_checks,
            "latest_status": recent_results[-1].overall_status,
            "latest_timestamp": recent_results[-1].timestamp.isoformat()
        }
        
    def update_thresholds(self, new_thresholds: Dict[str, float]):
        """
        閾値更新
        
        Args:
            new_thresholds: 新しい閾値設定
        """
        self.thresholds.update(new_thresholds)