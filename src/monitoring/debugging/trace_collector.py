"""
Trace Collector - トレース情報収集

実行トレース・デバッグ情報・パフォーマンス分析
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import deque


@dataclass
class TraceEvent:
    """トレースイベント"""
    timestamp: datetime
    agent_name: str
    operation: str
    duration: float
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'agent_name': self.agent_name,
            'operation': self.operation,
            'duration': self.duration,
            'details': self.details
        }


class TraceCollector:
    """トレース情報収集"""
    
    def __init__(self, max_traces: int = 10000):
        self.max_traces = max_traces
        self.traces = deque(maxlen=max_traces)
        self._lock = threading.Lock()
        
    def record_trace(self, agent_name: str, operation: str,
                    duration: float, details: Optional[Dict[str, Any]] = None):
        """トレース記録"""
        with self._lock:
            trace = TraceEvent(
                timestamp=datetime.now(),
                agent_name=agent_name,
                operation=operation,
                duration=duration,
                details=details or {}
            )
            self.traces.append(trace)
            
    def get_slow_operations(self, threshold_ms: float = 50.0) -> List[TraceEvent]:
        """遅い操作取得"""
        with self._lock:
            return [trace for trace in self.traces if trace.duration > threshold_ms]