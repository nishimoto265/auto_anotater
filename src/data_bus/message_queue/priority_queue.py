"""
PriorityQueue - 優先度付きキュー
高速メッセージ処理のための優先度制御
"""
import heapq
import threading
import time
from typing import Any, Optional, Tuple, List
from collections import defaultdict
import logging

from .message_serializer import Message


class PriorityQueue:
    """
    優先度付きキュー
    高速メッセージ処理のための最適化実装
    """
    
    # 優先度レベル（数値が小さいほど高優先度）
    PRIORITY_HIGH = 1
    PRIORITY_NORMAL = 2
    PRIORITY_LOW = 3
    
    PRIORITY_MAP = {
        "high": PRIORITY_HIGH,
        "normal": PRIORITY_NORMAL,
        "low": PRIORITY_LOW
    }
    
    def __init__(self, max_size: int = 10000):
        self._heap: List[Tuple[int, float, int, Message]] = []
        self._max_size = max_size
        self._counter = 0  # メッセージの挿入順序保持用
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self._stats = {
            'total_enqueued': 0,
            'total_dequeued': 0,
            'high_priority_count': 0,
            'normal_priority_count': 0,
            'low_priority_count': 0,
            'peak_size': 0,
            'avg_wait_time': 0.0
        }
        self._logger = logging.getLogger(__name__)
    
    def put(self, message: Message, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        メッセージをキューに追加
        
        Args:
            message: 追加するメッセージ
            block: ブロッキングモード
            timeout: タイムアウト（秒）
            
        Returns:
            bool: 追加成功フラグ
        """
        with self._not_full:
            # キューサイズチェック
            if len(self._heap) >= self._max_size:
                if not block:
                    return False
                if timeout is not None:
                    if not self._not_full.wait(timeout):
                        return False
                else:
                    self._not_full.wait()
            
            # 優先度マッピング
            priority_level = self.PRIORITY_MAP.get(message.priority, self.PRIORITY_NORMAL)
            
            # ヒープに追加（優先度、タイムスタンプ、カウンタ、メッセージ）
            heapq.heappush(self._heap, (
                priority_level,
                message.timestamp,
                self._counter,
                message
            ))
            
            self._counter += 1
            
            # 統計更新
            self._update_stats_put(message.priority)
            
            # 待機中のconsumerに通知
            self._not_empty.notify()
            
            return True
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Message]:
        """
        メッセージをキューから取得
        
        Args:
            block: ブロッキングモード
            timeout: タイムアウト（秒）
            
        Returns:
            Message: 取得したメッセージ（None if timeout）
        """
        with self._not_empty:
            # キューが空の場合の処理
            while not self._heap:
                if not block:
                    return None
                if timeout is not None:
                    if not self._not_empty.wait(timeout):
                        return None
                else:
                    self._not_empty.wait()
            
            # 最高優先度メッセージ取得
            priority_level, timestamp, counter, message = heapq.heappop(self._heap)
            
            # 統計更新
            wait_time = time.perf_counter() - timestamp
            self._update_stats_get(wait_time)
            
            # 待機中のproducerに通知
            self._not_full.notify()
            
            return message
    
    def peek(self) -> Optional[Message]:
        """キューの先頭メッセージを覗く（取得はしない）"""
        with self._lock:
            if not self._heap:
                return None
            return self._heap[0][3]
    
    def size(self) -> int:
        """キューサイズ取得"""
        with self._lock:
            return len(self._heap)
    
    def empty(self) -> bool:
        """キューが空か確認"""
        with self._lock:
            return len(self._heap) == 0
    
    def full(self) -> bool:
        """キューが満杯か確認"""
        with self._lock:
            return len(self._heap) >= self._max_size
    
    def clear(self) -> int:
        """キュークリア"""
        with self._lock:
            count = len(self._heap)
            self._heap.clear()
            self._not_full.notify_all()
            return count
    
    def get_stats(self) -> dict:
        """統計情報取得"""
        with self._lock:
            stats = self._stats.copy()
            stats['current_size'] = len(self._heap)
            return stats
    
    def reset_stats(self):
        """統計リセット"""
        with self._lock:
            self._stats = {
                'total_enqueued': 0,
                'total_dequeued': 0,
                'high_priority_count': 0,
                'normal_priority_count': 0,
                'low_priority_count': 0,
                'peak_size': 0,
                'avg_wait_time': 0.0
            }
    
    def get_priority_distribution(self) -> dict:
        """優先度別メッセージ分布取得"""
        with self._lock:
            distribution = defaultdict(int)
            for priority_level, _, _, _ in self._heap:
                if priority_level == self.PRIORITY_HIGH:
                    distribution['high'] += 1
                elif priority_level == self.PRIORITY_NORMAL:
                    distribution['normal'] += 1
                elif priority_level == self.PRIORITY_LOW:
                    distribution['low'] += 1
            return dict(distribution)
    
    def _update_stats_put(self, priority: str):
        """put統計更新"""
        self._stats['total_enqueued'] += 1
        self._stats[f'{priority}_priority_count'] += 1
        current_size = len(self._heap)
        self._stats['peak_size'] = max(self._stats['peak_size'], current_size)
    
    def _update_stats_get(self, wait_time: float):
        """get統計更新"""
        self._stats['total_dequeued'] += 1
        
        # 平均待機時間更新
        dequeued = self._stats['total_dequeued']
        if dequeued == 1:
            self._stats['avg_wait_time'] = wait_time
        else:
            current_avg = self._stats['avg_wait_time']
            self._stats['avg_wait_time'] = (current_avg * (dequeued - 1) + wait_time) / dequeued


class FastQueue:
    """
    高速キュー（優先度なし）
    フレーム切り替えなどの超高速処理用
    """
    
    def __init__(self, max_size: int = 1000):
        self._queue: List[Message] = []
        self._max_size = max_size
        self._head = 0
        self._tail = 0
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
    
    def put_nowait(self, message: Message) -> bool:
        """非ブロッキング追加"""
        with self._lock:
            if self._tail - self._head >= self._max_size:
                return False
            
            # リスト拡張が必要な場合
            if self._tail >= len(self._queue):
                self._queue.extend([None] * max(100, self._max_size // 10))
            
            self._queue[self._tail] = message
            self._tail += 1
            
            self._not_empty.notify()
            return True
    
    def get_nowait(self) -> Optional[Message]:
        """非ブロッキング取得"""
        with self._lock:
            if self._head >= self._tail:
                return None
            
            message = self._queue[self._head]
            self._queue[self._head] = None  # メモリ解放
            self._head += 1
            
            # キューのリセット（メモリ効率化）
            if self._head > 1000:
                self._queue = self._queue[self._head:]
                self._tail -= self._head
                self._head = 0
            
            self._not_full.notify()
            return message
    
    def size(self) -> int:
        """キューサイズ"""
        with self._lock:
            return self._tail - self._head
    
    def empty(self) -> bool:
        """空確認"""
        with self._lock:
            return self._head >= self._tail