import logging
import logging.handlers
import os
import time
import traceback
from datetime import datetime
from typing import Optional, Dict, List

class Logger:
    _instance = None
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = logging.getLogger('AutoAnnotation')
        self.logger.setLevel(logging.DEBUG)
        
        # ファイル出力設定
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT, self.DATE_FORMAT))
        self.logger.addHandler(file_handler)
        
        # コンソール出力設定
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(self.LOG_FORMAT, self.DATE_FORMAT))
        self.logger.addHandler(console_handler)
        
        self.performance_data: Dict[str, List[float]] = {}
        self.error_stats: Dict[str, int] = {}

    @classmethod
    def setup(cls):
        """Loggerシステムを初期化"""
        cls()  # インスタンスを作成（シングルトン）

    @classmethod
    def critical(cls, message: str, exc_info: Optional[Exception] = None):
        """クリティカルレベルのログを出力"""
        instance = cls()
        if exc_info:
            instance.logger.critical(f"{message}\n{traceback.format_exc()}")
            instance._update_error_stats(type(exc_info).__name__)
        else:
            instance.logger.critical(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str, exc_info: Optional[Exception] = None):
        if exc_info:
            self.logger.error(f"{message}\n{traceback.format_exc()}")
            self._update_error_stats(type(exc_info).__name__)
        else:
            self.logger.error(message)

    def log_ui_action(self, action: str, details: Optional[Dict] = None):
        message = f"UI Action: {action}"
        if details:
            message += f" - {details}"
        self.info(message)

    def log_file_operation(self, operation: str, path: str, status: str):
        self.info(f"File Operation: {operation} - Path: {path} - Status: {status}")

    def start_performance_measurement(self, operation: str):
        if operation not in self.performance_data:
            self.performance_data[operation] = []
        self.performance_data[operation].append(time.perf_counter())

    def end_performance_measurement(self, operation: str) -> float:
        if operation in self.performance_data and self.performance_data[operation]:
            start_time = self.performance_data[operation].pop()
            duration = time.perf_counter() - start_time
            self.debug(f"Performance - {operation}: {duration:.3f}s")
            return duration
        return 0.0

    def _update_error_stats(self, error_type: str):
        self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1

    def get_error_statistics(self) -> Dict[str, int]:
        return self.error_stats.copy()

    def get_performance_summary(self) -> Dict[str, List[float]]:
        return self.performance_data.copy()

    def clear_statistics(self):
        self.performance_data.clear()
        self.error_stats.clear()

    def export_statistics(self, export_path: str):
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(f"Statistics Export - {datetime.now().strftime(self.DATE_FORMAT)}\n\n")
            f.write("Error Statistics:\n")
            for error_type, count in self.error_stats.items():
                f.write(f"{error_type}: {count}\n")
            f.write("\nPerformance Data:\n")
            for operation, times in self.performance_data.items():
                if times:
                    avg_time = sum(times) / len(times)
                    f.write(f"{operation} - Average: {avg_time:.3f}s\n")