"""
Error Tracker - エラー追跡・分析

エラー発生パターン分析・再発防止・システム安定性向上
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class ErrorEvent:
    """エラーイベント"""
    timestamp: datetime
    agent_name: str
    error_type: str
    error_message: str
    context: Dict[str, Any]
    severity: str = "error"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'agent_name': self.agent_name,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'context': self.context,
            'severity': self.severity
        }


class ErrorTracker:
    """エラー追跡・分析"""
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors = deque(maxlen=max_errors)
        self.error_counts = defaultdict(int)
        self._lock = threading.Lock()
        
    def track_error(self, agent_name: str, error: Exception, 
                   context: Optional[Dict[str, Any]] = None,
                   severity: str = "error"):
        """エラー追跡"""
        with self._lock:
            error_event = ErrorEvent(
                timestamp=datetime.now(),
                agent_name=agent_name,
                error_type=type(error).__name__,
                error_message=str(error),
                context=context or {},
                severity=severity
            )
            
            self.errors.append(error_event)
            self.error_counts[f"{agent_name}:{error_event.error_type}"] += 1
            
    def get_error_summary(self, hours: int = 1) -> Dict[str, Any]:
        """エラーサマリー取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_errors = [
                error for error in self.errors
                if error.timestamp > cutoff_time
            ]
            
        return {
            'total_errors': len(recent_errors),
            'period_hours': hours,
            'error_by_agent': self._count_by_agent(recent_errors),
            'error_by_type': self._count_by_type(recent_errors)
        }
        
    def _count_by_agent(self, errors: List[ErrorEvent]) -> Dict[str, int]:
        """Agent別エラー数"""
        counts = defaultdict(int)
        for error in errors:
            counts[error.agent_name] += 1
        return dict(counts)
        
    def _count_by_type(self, errors: List[ErrorEvent]) -> Dict[str, int]:
        """エラータイプ別数"""
        counts = defaultdict(int)
        for error in errors:
            counts[error.error_type] += 1
        return dict(counts)