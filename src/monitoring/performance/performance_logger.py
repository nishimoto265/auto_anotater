"""
Performance Logger - パフォーマンスログ記録

フレーム切り替え・メモリ使用量・システム性能の統合ログ記録
Agent8 Monitoring の統合ログシステム
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class PerformanceMetric:
    """パフォーマンスメトリクス"""
    metric_name: str
    value: float
    unit: str
    agent_name: str
    timestamp: datetime
    severity: str = "info"
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返却"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class PerformanceLogger:
    """
    パフォーマンスログ記録
    
    機能:
    - 構造化性能ログ記録
    - Agent別ログ分離
    - リアルタイム性能監視
    - 性能統計レポート生成
    
    性能要件:
    - ログ記録時間: 5ms以下
    - ファイルI/O: 非同期処理
    - ディスク使用量: 効率的ローテーション
    """
    
    def __init__(self, log_dir: str = "logs", max_file_size_mb: int = 100):
        """
        初期化
        
        Args:
            log_dir: ログディレクトリ
            max_file_size_mb: ファイル最大サイズ（MB）
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.max_file_size = max_file_size_mb * 1024 * 1024  # bytes
        self.current_date = datetime.now().date()
        
        # ログファイル管理
        self.log_files = {}
        self._setup_log_files()
        
    def _setup_log_files(self):
        """ログファイル設定"""
        date_str = self.current_date.strftime("%Y%m%d")
        
        # Agent別ログファイル
        agent_names = [
            'cache', 'presentation', 'application', 'domain',
            'infrastructure', 'data_bus', 'persistence', 'monitoring'
        ]
        
        for agent in agent_names:
            log_file = self.log_dir / f"{agent}_performance_{date_str}.log"
            self.log_files[agent] = log_file
            
        # 統合ログファイル
        self.log_files['system'] = self.log_dir / f"system_performance_{date_str}.log"
        
    def log_frame_switching(self, frame_id: str, total_time: float,
                           cache_time: Optional[float] = None,
                           ui_time: Optional[float] = None,
                           success: bool = True):
        """
        フレーム切り替え性能ログ
        
        Args:
            frame_id: フレームID
            total_time: 総時間（ms）
            cache_time: Cache時間（ms）
            ui_time: UI時間（ms）
            success: 成功フラグ
        """
        severity = "info" if success and total_time <= 50.0 else "warning"
        if total_time > 50.0:
            severity = "error"
            
        details = {
            "frame_id": frame_id,
            "cache_time": cache_time,
            "ui_time": ui_time,
            "success": success,
            "threshold_50ms": total_time <= 50.0
        }
        
        metric = PerformanceMetric(
            metric_name="frame_switching",
            value=total_time,
            unit="ms",
            agent_name="cache",
            timestamp=datetime.now(),
            severity=severity,
            details=details
        )
        
        self._write_log(metric, "cache")
        self._write_log(metric, "system")
        
    def log_memory_usage(self, usage_gb: float, limit_gb: float = 20.0,
                        agent_name: str = "monitoring"):
        """
        メモリ使用量ログ
        
        Args:
            usage_gb: 使用量（GB）
            limit_gb: 上限（GB）
            agent_name: 関連Agent名
        """
        usage_ratio = usage_gb / limit_gb
        severity = "info"
        
        if usage_ratio > 0.9:  # 90%超過
            severity = "error"
        elif usage_ratio > 0.8:  # 80%超過
            severity = "warning"
            
        details = {
            "limit_gb": limit_gb,
            "usage_ratio": usage_ratio,
            "threshold_warning": usage_ratio > 0.8,
            "threshold_critical": usage_ratio > 0.9
        }
        
        metric = PerformanceMetric(
            metric_name="memory_usage",
            value=usage_gb,
            unit="GB",
            agent_name=agent_name,
            timestamp=datetime.now(),
            severity=severity,
            details=details
        )
        
        self._write_log(metric, agent_name)
        self._write_log(metric, "system")
        
    def log_cache_performance(self, hit_rate: float, access_time: float,
                             agent_name: str = "cache"):
        """
        Cache性能ログ
        
        Args:
            hit_rate: ヒット率（0.0-1.0）
            access_time: アクセス時間（ms）
            agent_name: Agent名
        """
        severity = "info"
        if hit_rate < 0.95:  # 95%未満
            severity = "warning"
        if hit_rate < 0.90:  # 90%未満
            severity = "error"
            
        details = {
            "hit_rate": hit_rate,
            "access_time": access_time,
            "target_hit_rate": 0.95,
            "meets_target": hit_rate >= 0.95
        }
        
        metric = PerformanceMetric(
            metric_name="cache_hit_rate",
            value=hit_rate,
            unit="ratio",
            agent_name=agent_name,
            timestamp=datetime.now(),
            severity=severity,
            details=details
        )
        
        self._write_log(metric, agent_name)
        self._write_log(metric, "system")
        
    def log_agent_performance(self, agent_name: str, operation: str,
                             duration: float, success: bool = True,
                             details: Optional[Dict[str, Any]] = None):
        """
        Agent性能ログ
        
        Args:
            agent_name: Agent名
            operation: 操作名
            duration: 実行時間（ms）
            success: 成功フラグ
            details: 詳細情報
        """
        severity = "info" if success else "error"
        
        # Agent別性能閾値チェック
        thresholds = {
            "presentation": 16.0,  # BB描画16ms以下
            "application": 10.0,   # ビジネスロジック10ms以下
            "domain": 1.0,         # IOU計算1ms以下
            "infrastructure": 50.0, # 画像処理50ms以下
            "data_bus": 1.0,       # イベント配信1ms以下
            "persistence": 100.0,  # ファイル保存100ms以下
            "monitoring": 10.0     # 監視処理10ms以下
        }
        
        threshold = thresholds.get(agent_name, 100.0)
        if duration > threshold:
            severity = "warning"
            
        log_details = {
            "operation": operation,
            "success": success,
            "threshold": threshold,
            "exceeds_threshold": duration > threshold
        }
        
        if details:
            log_details.update(details)
            
        metric = PerformanceMetric(
            metric_name=f"{agent_name}_{operation}",
            value=duration,
            unit="ms",
            agent_name=agent_name,
            timestamp=datetime.now(),
            severity=severity,
            details=log_details
        )
        
        self._write_log(metric, agent_name)
        self._write_log(metric, "system")
        
    def log_system_health(self, component: str, status: str,
                         metrics: Dict[str, Any]):
        """
        システム健全性ログ
        
        Args:
            component: コンポーネント名
            status: ステータス（healthy/warning/critical）
            metrics: メトリクス情報
        """
        severity_map = {
            "healthy": "info",
            "warning": "warning",
            "critical": "error"
        }
        
        metric = PerformanceMetric(
            metric_name="system_health",
            value=1.0 if status == "healthy" else 0.0,
            unit="status",
            agent_name="monitoring",
            timestamp=datetime.now(),
            severity=severity_map.get(status, "info"),
            details={
                "component": component,
                "status": status,
                "metrics": metrics
            }
        )
        
        self._write_log(metric, "monitoring")
        self._write_log(metric, "system")
        
    def _write_log(self, metric: PerformanceMetric, log_target: str):
        """
        ログ書き込み
        
        Args:
            metric: パフォーマンスメトリクス
            log_target: ログ対象（agent名またはsystem）
        """
        try:
            start_time = time.perf_counter()
            
            # 日付チェック・ログローテーション
            self._check_log_rotation()
            
            log_file = self.log_files.get(log_target)
            if not log_file:
                return
                
            # JSON形式でログ記録
            log_entry = metric.to_dict()
            log_line = json.dumps(log_entry, ensure_ascii=False) + "\n"
            
            # ファイル書き込み
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
                
            # 書き込み時間チェック（5ms以下要件）
            elapsed_time = (time.perf_counter() - start_time) * 1000
            if elapsed_time > 5.0:
                print(f"Warning: Log write took {elapsed_time:.2f}ms (>5ms)")
                
        except Exception as e:
            print(f"Failed to write log: {e}")
            
    def _check_log_rotation(self):
        """ログローテーションチェック"""
        current_date = datetime.now().date()
        
        # 日付変更チェック
        if current_date != self.current_date:
            self.current_date = current_date
            self._setup_log_files()
            
        # ファイルサイズチェック
        for log_target, log_file in self.log_files.items():
            if log_file.exists() and log_file.stat().st_size > self.max_file_size:
                # ファイルローテーション実行
                timestamp = datetime.now().strftime("%H%M%S")
                rotated_file = log_file.with_suffix(f".{timestamp}.log")
                log_file.rename(rotated_file)
                
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """
        性能サマリー取得
        
        Args:
            hours: 集計時間（時間）
            
        Returns:
            Dict[str, Any]: 性能サマリー
        """
        # 簡易実装（実際はログファイル解析が必要）
        return {
            "period_hours": hours,
            "frame_switching": {
                "average_time": 0.0,
                "success_rate": 0.0,
                "under_50ms_rate": 0.0
            },
            "memory_usage": {
                "average_gb": 0.0,
                "peak_gb": 0.0,
                "warning_events": 0
            },
            "cache_performance": {
                "average_hit_rate": 0.0,
                "cache_misses": 0
            },
            "system_health": {
                "healthy_ratio": 0.0,
                "warning_events": 0,
                "critical_events": 0
            }
        }
        
    def cleanup_old_logs(self, days: int = 7):
        """
        古いログファイル削除
        
        Args:
            days: 保持日数
        """
        cutoff_date = datetime.now().date()
        cutoff_timestamp = time.time() - (days * 24 * 3600)
        
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_timestamp:
                try:
                    log_file.unlink()
                except Exception as e:
                    print(f"Failed to delete old log {log_file}: {e}")
                    
    def get_log_files_info(self) -> Dict[str, Dict[str, Any]]:
        """
        ログファイル情報取得
        
        Returns:
            Dict[str, Dict[str, Any]]: ログファイル情報
        """
        info = {}
        
        for log_target, log_file in self.log_files.items():
            if log_file.exists():
                stat = log_file.stat()
                info[log_target] = {
                    "file_path": str(log_file),
                    "size_mb": stat.st_size / (1024 * 1024),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                info[log_target] = {
                    "file_path": str(log_file),
                    "size_mb": 0.0,
                    "modified": None
                }
                
        return info