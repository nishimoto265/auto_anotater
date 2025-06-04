"""
Debug Logger - デバッグログ記録・分析

Agent8 Monitoring のデバッグ支援システム
構造化ログ・Agent別分離・リアルタイム監視
"""

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
import queue


@dataclass
class LogEntry:
    """ログエントリ"""
    timestamp: datetime
    agent_name: str
    level: str
    message: str
    extra_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返却"""
        result = {
            'timestamp': self.timestamp.isoformat(),
            'agent': self.agent_name,
            'level': self.level,
            'message': self.message
        }
        if self.extra_data:
            result.update(self.extra_data)
        return result


class DebugLogger:
    """
    デバッグログ記録・分析
    
    機能:
    - 階層化ログ（DEBUG/INFO/WARNING/ERROR）
    - Agent別ログ分離
    - 構造化ログ（JSON形式）
    - リアルタイムログ監視
    
    性能要件:
    - ログ記録時間: 5ms以下
    - 非同期ログ処理
    - メモリ効率的なバッファリング
    """
    
    def __init__(self, log_level: str = "INFO", log_dir: str = "logs", 
                 max_file_size_mb: int = 50, backup_count: int = 5):
        """
        初期化
        
        Args:
            log_level: ログレベル
            log_dir: ログディレクトリ
            max_file_size_mb: ファイル最大サイズ（MB）
            backup_count: バックアップファイル数
        """
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.backup_count = backup_count
        
        # ログキュー（非同期処理用）
        self.log_queue = queue.Queue(maxsize=1000)
        self.queue_worker: Optional[threading.Thread] = None
        self.is_running = False
        
        # ログハンドラー管理
        self.file_handlers: Dict[str, RotatingFileHandler] = {}
        self.loggers: Dict[str, logging.Logger] = {}
        
        # 構造化ログフォーマット
        self.formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        
        # Agent別ログ設定
        self._setup_agent_loggers()
        
        # コンソールハンドラー（開発時）
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(self.formatter)
        
        # 非同期処理開始
        self.start_async_logging()
        
    def _setup_agent_loggers(self):
        """Agent別ログ設定"""
        agent_names = [
            'cache', 'presentation', 'application', 'domain',
            'infrastructure', 'data_bus', 'persistence', 'monitoring'
        ]
        
        for agent_name in agent_names:
            # Agent別ログファイル
            log_file = self.log_dir / f"{agent_name}_debug.log"
            
            # RotatingFileHandler作成
            handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            handler.setFormatter(self.formatter)
            
            # Logger作成
            logger = logging.getLogger(f"agent.{agent_name}")
            logger.setLevel(self.log_level)
            logger.addHandler(handler)
            
            # 管理用保存
            self.file_handlers[agent_name] = handler
            self.loggers[agent_name] = logger
            
        # システム統合ログ
        system_log_file = self.log_dir / "system_debug.log"
        system_handler = RotatingFileHandler(
            filename=system_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        system_handler.setFormatter(self.formatter)
        
        system_logger = logging.getLogger("system")
        system_logger.setLevel(self.log_level)
        system_logger.addHandler(system_handler)
        
        self.file_handlers['system'] = system_handler
        self.loggers['system'] = system_logger
        
    def start_async_logging(self):
        """非同期ログ処理開始"""
        if self.is_running:
            return
            
        self.is_running = True
        self.queue_worker = threading.Thread(
            target=self._queue_worker,
            name="DebugLogger-Worker"
        )
        self.queue_worker.daemon = True
        self.queue_worker.start()
        
    def stop_async_logging(self):
        """非同期ログ処理停止"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # 残りキュー処理
        try:
            while not self.log_queue.empty():
                time.sleep(0.01)
        except:
            pass
            
        if self.queue_worker:
            self.queue_worker.join(timeout=2.0)
            
    def log_agent_event(self, agent_name: str, level: str, 
                       message: str, extra_data: Optional[Dict[str, Any]] = None):
        """
        Agent別イベントログ
        
        Args:
            agent_name: Agent名
            level: ログレベル
            message: メッセージ
            extra_data: 追加データ
        """
        try:
            start_time = time.perf_counter()
            
            log_entry = LogEntry(
                timestamp=datetime.now(),
                agent_name=agent_name,
                level=level.upper(),
                message=message,
                extra_data=extra_data
            )
            
            # キューに追加（非同期処理）
            try:
                self.log_queue.put_nowait(log_entry)
            except queue.Full:
                # キュー満杯時は古いエントリを削除
                try:
                    self.log_queue.get_nowait()
                    self.log_queue.put_nowait(log_entry)
                except queue.Empty:
                    pass
                    
            # 処理時間チェック（5ms以下要件）
            elapsed_time = (time.perf_counter() - start_time) * 1000
            if elapsed_time > 5.0:
                print(f"Warning: Log entry took {elapsed_time:.2f}ms (>5ms)")
                
        except Exception as e:
            # ログ処理エラーは無視（無限ループ防止）
            print(f"Log error: {e}")
            
    def log_performance_event(self, operation: str, duration: float,
                             agent_name: str, success: bool = True,
                             extra_data: Optional[Dict[str, Any]] = None):
        """
        パフォーマンスイベントログ
        
        Args:
            operation: 操作名
            duration: 実行時間（ms）
            agent_name: Agent名
            success: 成功フラグ
            extra_data: 追加データ
        """
        perf_data = {
            "operation": operation,
            "duration_ms": duration,
            "success": success,
            "performance_category": "timing"
        }
        
        if extra_data:
            perf_data.update(extra_data)
            
        level = "INFO" if success else "WARNING"
        message = f"Performance: {operation} ({duration:.2f}ms)"
        
        self.log_agent_event(agent_name, level, message, perf_data)
        
    def log_error_event(self, agent_name: str, error: Exception,
                       context: Optional[Dict[str, Any]] = None):
        """
        エラーイベントログ
        
        Args:
            agent_name: Agent名
            error: 発生した例外
            context: エラーコンテキスト
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_category": "exception"
        }
        
        if context:
            error_data["context"] = context
            
        message = f"Error: {type(error).__name__}: {error}"
        
        self.log_agent_event(agent_name, "ERROR", message, error_data)
        
    def log_frame_switching_event(self, frame_id: str, total_time: float,
                                 cache_time: Optional[float] = None,
                                 ui_time: Optional[float] = None,
                                 success: bool = True):
        """
        フレーム切り替えイベントログ
        
        Args:
            frame_id: フレームID
            total_time: 総時間（ms）
            cache_time: Cache時間（ms）
            ui_time: UI時間（ms）
            success: 成功フラグ
        """
        frame_data = {
            "frame_id": frame_id,
            "total_time": total_time,
            "cache_time": cache_time,
            "ui_time": ui_time,
            "success": success,
            "meets_50ms_target": total_time <= 50.0,
            "event_category": "frame_switching"
        }
        
        level = "INFO"
        if not success or total_time > 50.0:
            level = "WARNING"
        if total_time > 60.0:
            level = "ERROR"
            
        message = f"Frame switch: {frame_id} ({total_time:.2f}ms)"
        
        self.log_agent_event("cache", level, message, frame_data)
        
    def log_memory_event(self, usage_gb: float, limit_gb: float = 20.0,
                        agent_name: str = "monitoring"):
        """
        メモリ使用量イベントログ
        
        Args:
            usage_gb: 使用量（GB）
            limit_gb: 上限（GB）
            agent_name: Agent名
        """
        usage_ratio = usage_gb / limit_gb
        
        memory_data = {
            "usage_gb": usage_gb,
            "limit_gb": limit_gb,
            "usage_ratio": usage_ratio,
            "event_category": "memory_usage"
        }
        
        level = "INFO"
        if usage_ratio > 0.8:
            level = "WARNING"
        if usage_ratio > 0.9:
            level = "ERROR"
            
        message = f"Memory usage: {usage_gb:.2f}GB ({usage_ratio:.1%})"
        
        self.log_agent_event(agent_name, level, message, memory_data)
        
    def enable_console_logging(self):
        """コンソールログ有効化"""
        for logger in self.loggers.values():
            if self.console_handler not in logger.handlers:
                logger.addHandler(self.console_handler)
                
    def disable_console_logging(self):
        """コンソールログ無効化"""
        for logger in self.loggers.values():
            if self.console_handler in logger.handlers:
                logger.removeHandler(self.console_handler)
                
    def set_log_level(self, level: str):
        """ログレベル設定"""
        new_level = getattr(logging, level.upper())
        self.log_level = new_level
        
        for logger in self.loggers.values():
            logger.setLevel(new_level)
            
    def get_recent_logs(self, agent_name: str, count: int = 100) -> List[str]:
        """
        最近のログ取得
        
        Args:
            agent_name: Agent名
            count: 取得件数
            
        Returns:
            List[str]: ログ行のリスト
        """
        log_file = self.log_dir / f"{agent_name}_debug.log"
        
        if not log_file.exists():
            return []
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-count:] if lines else []
        except Exception:
            return []
            
    def search_logs(self, agent_name: str, keyword: str, 
                   max_results: int = 50) -> List[str]:
        """
        ログ検索
        
        Args:
            agent_name: Agent名
            keyword: 検索キーワード
            max_results: 最大結果数
            
        Returns:
            List[str]: マッチしたログ行
        """
        log_file = self.log_dir / f"{agent_name}_debug.log"
        
        if not log_file.exists():
            return []
            
        results = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if keyword.lower() in line.lower():
                        results.append(line.strip())
                        if len(results) >= max_results:
                            break
        except Exception:
            pass
            
        return results
        
    def get_log_statistics(self) -> Dict[str, Any]:
        """
        ログ統計取得
        
        Returns:
            Dict[str, Any]: ログ統計情報
        """
        stats = {}
        
        for agent_name in self.file_handlers.keys():
            log_file = self.log_dir / f"{agent_name}_debug.log"
            
            if log_file.exists():
                stat = log_file.stat()
                stats[agent_name] = {
                    "file_size_mb": stat.st_size / (1024 * 1024),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                stats[agent_name] = {
                    "file_size_mb": 0.0,
                    "modified": None
                }
                
        # キュー統計
        stats['queue_info'] = {
            "queue_size": self.log_queue.qsize(),
            "queue_maxsize": self.log_queue.maxsize,
            "is_running": self.is_running
        }
        
        return stats
        
    def _queue_worker(self):
        """ログキューワーカー"""
        while self.is_running:
            try:
                # タイムアウト付きでキューから取得
                log_entry = self.log_queue.get(timeout=1.0)
                self._write_log_entry(log_entry)
                self.log_queue.task_done()
                
            except queue.Empty:
                # タイムアウト時は継続
                continue
            except Exception as e:
                print(f"Queue worker error: {e}")
                
    def _write_log_entry(self, log_entry: LogEntry):
        """
        ログエントリ書き込み
        
        Args:
            log_entry: ログエントリ
        """
        try:
            # Agent別ログ
            agent_logger = self.loggers.get(log_entry.agent_name)
            if agent_logger:
                # 構造化データをJSON形式で記録
                log_data = log_entry.to_dict()
                log_message = json.dumps(log_data, ensure_ascii=False)
                
                # レベル別出力
                if log_entry.level == "DEBUG":
                    agent_logger.debug(log_message)
                elif log_entry.level == "INFO":
                    agent_logger.info(log_message)
                elif log_entry.level == "WARNING":
                    agent_logger.warning(log_message)
                elif log_entry.level == "ERROR":
                    agent_logger.error(log_message)
                    
            # システム統合ログ
            system_logger = self.loggers.get('system')
            if system_logger:
                system_message = f"[{log_entry.agent_name}] {log_entry.message}"
                
                if log_entry.level == "DEBUG":
                    system_logger.debug(system_message)
                elif log_entry.level == "INFO":
                    system_logger.info(system_message)
                elif log_entry.level == "WARNING":
                    system_logger.warning(system_message)
                elif log_entry.level == "ERROR":
                    system_logger.error(system_message)
                    
        except Exception as e:
            print(f"Failed to write log entry: {e}")
            
    def cleanup_old_logs(self, days: int = 7):
        """
        古いログファイル削除
        
        Args:
            days: 保持日数
        """
        cutoff_timestamp = time.time() - (days * 24 * 3600)
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                if log_file.stat().st_mtime < cutoff_timestamp:
                    log_file.unlink()
            except Exception as e:
                print(f"Failed to delete old log {log_file}: {e}")
                
    def __del__(self):
        """デストラクタ"""
        self.stop_async_logging()