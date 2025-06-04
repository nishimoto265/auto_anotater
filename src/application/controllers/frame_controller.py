"""
FrameController - Agent2 Application Layer
フレーム制御コントローラー

性能要件:
- フレーム切り替え制御: 5ms以下（Cache連携部分除く）
- フレーム検証: 1ms以下
- 自動保存制御: 非同期実行
"""

import time
import re
import threading
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor


class FrameControllerError(Exception):
    """フレームコントローラーエラー基底クラス"""
    pass


class FrameValidationError(FrameControllerError):
    """フレーム検証エラー"""
    pass


class FrameSwitchError(FrameControllerError):
    """フレーム切り替えエラー"""
    pass


@dataclass
class FrameSwitchRequest:
    """フレーム切り替え要求"""
    current_frame_id: str
    target_frame_id: str
    auto_save: bool = True
    preload_next: bool = True


@dataclass
class FrameSwitchResult:
    """フレーム切り替え結果"""
    success: bool
    current_frame_id: str
    target_frame_id: str
    switch_time: float  # ms
    cache_hit: bool = False
    auto_save_started: bool = False
    error_message: Optional[str] = None


class PerformanceMonitor:
    """性能監視ヘルパー"""
    
    def __init__(self):
        self._times = {}
        self._lock = threading.Lock()
    
    def measure_time(self, operation_name: str):
        """実行時間測定デコレータ"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end = time.perf_counter()
                    exec_time = (end - start) * 1000  # ms
                    
                    with self._lock:
                        if operation_name not in self._times:
                            self._times[operation_name] = []
                        self._times[operation_name].append(exec_time)
            return wrapper
        return decorator
    
    def get_stats(self, operation_name: str) -> Dict[str, float]:
        """統計情報取得"""
        with self._lock:
            times = self._times.get(operation_name, [])
            if not times:
                return {}
            
            return {
                "count": len(times),
                "avg": sum(times) / len(times),
                "max": max(times),
                "min": min(times),
                "latest": times[-1] if times else 0
            }


class FrameController:
    """
    フレーム制御コントローラー
    
    性能要件:
    - フレーム切り替え制御: 5ms以下（Cache連携部分除く）
    - フレーム検証: 1ms以下
    - 自動保存制御: 非同期実行
    """
    
    def __init__(self, cache_service, persistence_service, data_bus, 
                 performance_monitor=None, thread_pool_size=2):
        """
        初期化
        
        Args:
            cache_service: Cache層サービス
            persistence_service: Persistence層サービス
            data_bus: Data Bus通信
            performance_monitor: 性能監視（オプション）
            thread_pool_size: 非同期処理用スレッドプールサイズ
        """
        self.cache_service = cache_service
        self.persistence_service = persistence_service
        self.data_bus = data_bus
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self._lock = threading.RLock()
        
        # 非同期処理用スレッドプール
        self._thread_pool = ThreadPoolExecutor(max_workers=thread_pool_size)
        
        # フレームID検証パターン（コンパイル済み）
        self._frame_id_pattern = re.compile(r'^\d{6}$')
        
        # キャッシュ
        self._validation_cache = {}
        self._navigation_cache = {}
        
        # 統計情報
        self._stats = {
            "switch_frame": {"times": [], "count": 0},
            "validate_frame": {"times": [], "count": 0},
            "navigation": {"times": [], "count": 0}
        }
    
    def _measure_time(self, operation_name: str):
        """時間測定デコレータ"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end = time.perf_counter()
                    exec_time = (end - start) * 1000  # ms
                    
                    with self._lock:
                        if operation_name in self._stats:
                            self._stats[operation_name]["times"].append(exec_time)
                            self._stats[operation_name]["count"] += 1
            return wrapper
        return decorator
    
    def _publish_frame_event(self, event_type: str, **event_data):
        """フレームイベント発行"""
        try:
            event_data.update({"timestamp": time.time()})
            self.data_bus.publish(event_type, **event_data)
        except Exception as e:
            print(f"Warning: Failed to publish {event_type} event: {e}")
    
    def _async_auto_save(self, frame_id: str):
        """非同期自動保存"""
        def save_task():
            try:
                self.persistence_service.auto_save_async(frame_id)
            except Exception as e:
                print(f"Warning: Auto-save failed for frame {frame_id}: {e}")
        
        self._thread_pool.submit(save_task)
    
    @lru_cache(maxsize=10000)
    def _validate_frame_id_cached(self, frame_id: str) -> bool:
        """フレームID検証（キャッシュ付き）"""
        if not frame_id:
            return False
        
        # 正規表現による高速検証
        return bool(self._frame_id_pattern.match(frame_id))
    
    @_measure_time("switch_frame")
    def switch_to_frame(self, request: FrameSwitchRequest) -> FrameSwitchResult:
        """
        フレーム切り替え制御（5ms以下必達）
        
        フロー:
        1. フレームID検証（1ms以下）
        2. 現フレーム自動保存指示（非同期）
        3. Cache層フレーム要求（別途50ms目標）
        4. フレーム切り替えイベント発行
        
        Args:
            request: フレーム切り替え要求
            
        Returns:
            FrameSwitchResult: 切り替え結果
        """
        start_time = time.perf_counter()
        
        try:
            with self._lock:
                # フレームID検証（高速）
                if not self.validate_frame_id(request.target_frame_id):
                    return FrameSwitchResult(
                        success=False,
                        current_frame_id=request.current_frame_id,
                        target_frame_id=request.target_frame_id,
                        switch_time=0.0,
                        error_message=f"Invalid target frame ID: {request.target_frame_id}"
                    )
                
                # 現フレーム自動保存（非同期）
                auto_save_started = False
                if request.auto_save:
                    self._async_auto_save(request.current_frame_id)
                    auto_save_started = True
                
                # Cache層からフレーム取得（実際の時間はCache層の責任）
                cache_hit = False
                try:
                    frame_data = self.cache_service.get_frame(request.target_frame_id)
                    cache_hit = True
                except Exception as e:
                    # Cache層エラー時の処理
                    switch_time = (time.perf_counter() - start_time) * 1000
                    return FrameSwitchResult(
                        success=False,
                        current_frame_id=request.current_frame_id,
                        target_frame_id=request.target_frame_id,
                        switch_time=switch_time,
                        auto_save_started=auto_save_started,
                        error_message=f"Cache layer error: {str(e)}"
                    )
                
                # 次フレーム先読み指示（非同期）
                if request.preload_next:
                    next_frame_id = self.get_next_frame_id(request.target_frame_id)
                    if next_frame_id:
                        try:
                            self.cache_service.preload_frames([next_frame_id])
                        except:
                            pass  # 先読みエラーは無視
                
                switch_time = (time.perf_counter() - start_time) * 1000
                
                # フレーム切り替えイベント発行
                self._publish_frame_event("frame_changed",
                                        current_frame_id=request.current_frame_id,
                                        target_frame_id=request.target_frame_id,
                                        switch_time=switch_time)
                
                return FrameSwitchResult(
                    success=True,
                    current_frame_id=request.current_frame_id,
                    target_frame_id=request.target_frame_id,
                    switch_time=switch_time,
                    cache_hit=cache_hit,
                    auto_save_started=auto_save_started
                )
                
        except Exception as e:
            switch_time = (time.perf_counter() - start_time) * 1000
            return FrameSwitchResult(
                success=False,
                current_frame_id=request.current_frame_id,
                target_frame_id=request.target_frame_id,
                switch_time=switch_time,
                error_message=f"Frame switch failed: {str(e)}"
            )
    
    @_measure_time("validate_frame")
    def validate_frame_id(self, frame_id: str) -> bool:
        """
        フレームID検証（1ms以下必達）
        
        Args:
            frame_id: 検証対象フレームID
            
        Returns:
            bool: 検証結果
        """
        try:
            return self._validate_frame_id_cached(frame_id)
        except Exception:
            return False
    
    @_measure_time("navigation")
    @lru_cache(maxsize=1000)
    def get_next_frame_id(self, current_frame_id: str) -> Optional[str]:
        """
        次フレームID取得（1ms以下）
        
        Args:
            current_frame_id: 現在フレームID
            
        Returns:
            Optional[str]: 次フレームID（存在しない場合はNone）
        """
        try:
            if not self.validate_frame_id(current_frame_id):
                return None
            
            frame_num = int(current_frame_id)
            
            # 上限チェック（999999まで）
            if frame_num >= 999999:
                return None
            
            next_frame_num = frame_num + 1
            return f"{next_frame_num:06d}"
            
        except Exception:
            return None
    
    @_measure_time("navigation")
    @lru_cache(maxsize=1000)
    def get_previous_frame_id(self, current_frame_id: str) -> Optional[str]:
        """
        前フレームID取得（1ms以下）
        
        Args:
            current_frame_id: 現在フレームID
            
        Returns:
            Optional[str]: 前フレームID（存在しない場合はNone）
        """
        try:
            if not self.validate_frame_id(current_frame_id):
                return None
            
            frame_num = int(current_frame_id)
            
            # 下限チェック（000000まで）
            if frame_num <= 0:
                return None
            
            prev_frame_num = frame_num - 1
            return f"{prev_frame_num:06d}"
            
        except Exception:
            return None
    
    def get_frame_range(self, start_frame_id: str, end_frame_id: str) -> List[str]:
        """
        フレーム範囲取得
        
        Args:
            start_frame_id: 開始フレームID
            end_frame_id: 終了フレームID
            
        Returns:
            List[str]: フレームIDリスト
        """
        try:
            if not (self.validate_frame_id(start_frame_id) and 
                   self.validate_frame_id(end_frame_id)):
                return []
            
            start_num = int(start_frame_id)
            end_num = int(end_frame_id)
            
            if start_num > end_num:
                return []
            
            # 大量範囲の制限（メモリ保護）
            if end_num - start_num > 10000:
                return []
            
            return [f"{i:06d}" for i in range(start_num, end_num + 1)]
            
        except Exception:
            return []
    
    def jump_to_frame(self, target_frame_id: str, current_frame_id: Optional[str] = None) -> FrameSwitchResult:
        """
        フレームジャンプ（大幅移動）
        
        Args:
            target_frame_id: ジャンプ先フレームID
            current_frame_id: 現在フレームID（オプション）
            
        Returns:
            FrameSwitchResult: ジャンプ結果
        """
        request = FrameSwitchRequest(
            current_frame_id=current_frame_id or "unknown",
            target_frame_id=target_frame_id,
            auto_save=True,
            preload_next=True
        )
        
        return self.switch_to_frame(request)
    
    def batch_frame_validation(self, frame_ids: List[str]) -> Dict[str, bool]:
        """
        一括フレーム検証
        
        Args:
            frame_ids: 検証対象フレームIDリスト
            
        Returns:
            Dict[str, bool]: 検証結果マップ
        """
        results = {}
        
        for frame_id in frame_ids:
            results[frame_id] = self.validate_frame_id(frame_id)
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """性能統計情報取得"""
        with self._lock:
            stats = {}
            
            for operation, data in self._stats.items():
                times = data["times"]
                if times:
                    stats[operation] = {
                        "count": data["count"],
                        "avg": sum(times) / len(times),
                        "max": max(times),
                        "min": min(times),
                        "latest": times[-1] if times else 0
                    }
                else:
                    stats[operation] = {"count": 0, "avg": 0, "max": 0, "min": 0, "latest": 0}
            
            return stats
    
    def clear_cache(self):
        """キャッシュクリア"""
        with self._lock:
            self._validation_cache.clear()
            self._navigation_cache.clear()
            self._validate_frame_id_cached.cache_clear()
            self.get_next_frame_id.cache_clear()
            self.get_previous_frame_id.cache_clear()
    
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        stats = self.get_performance_stats()
        
        health_status = {
            "status": "healthy",
            "thread_pool_active": self._thread_pool._threads,
            "cache_size": {
                "validation": len(self._validation_cache),
                "navigation": len(self._navigation_cache)
            },
            "performance": {},
            "warnings": []
        }
        
        # 性能チェック
        targets = {"switch_frame": 5, "validate_frame": 1, "navigation": 1}
        
        for operation, stat in stats.items():
            target = targets.get(operation, 5)
            avg_time = stat.get("avg", 0)
            max_time = stat.get("max", 0)
            
            health_status["performance"][operation] = {
                "avg_time": avg_time,
                "max_time": max_time,
                "target": target,
                "meets_target": avg_time <= target
            }
            
            if avg_time > target:
                health_status["warnings"].append(
                    f"{operation} average time {avg_time:.2f}ms exceeds target {target}ms"
                )
        
        if health_status["warnings"]:
            health_status["status"] = "degraded"
        
        return health_status
    
    def __del__(self):
        """デストラクタ"""
        try:
            if hasattr(self, '_thread_pool'):
                self._thread_pool.shutdown(wait=False)
        except:
            pass