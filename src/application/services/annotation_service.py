"""
AnnotationService - Agent2 Application Layer
BB作成・削除・更新統合処理サービス

性能要件:
- BB作成処理: 10ms以下
- BB削除処理: 5ms以下
- BB更新処理: 8ms以下
- 一括処理: 効率的バッチ処理
"""

import time
import uuid
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor


class AnnotationError(Exception):
    """アノテーション処理エラー基底クラス"""
    pass


class ValidationError(AnnotationError):
    """検証エラー"""
    pass


class ServiceError(AnnotationError):
    """サービス処理エラー"""
    pass


@dataclass
class BBCreationRequest:
    """BB作成要求"""
    x: float
    y: float
    w: float
    h: float
    individual_id: int
    action_id: int
    confidence: float = 1.0
    frame_id: Optional[str] = None


@dataclass
class BBUpdateRequest:
    """BB更新要求"""
    bb_id: str
    properties: Dict[str, Any]
    frame_id: Optional[str] = None


@dataclass
class BBDeletionRequest:
    """BB削除要求"""
    bb_id: str
    frame_id: str


@dataclass
class BBEntity:
    """BBエンティティ（簡易版）"""
    id: str
    x: float
    y: float
    w: float
    h: float
    individual_id: int
    action_id: int
    confidence: float
    frame_id: str
    created_at: float
    updated_at: Optional[float] = None


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


class AnnotationService:
    """
    アノテーション統合処理サービス
    
    性能要件:
    - BB作成処理: 10ms以下
    - BB削除処理: 5ms以下
    - BB更新処理: 8ms以下
    - 一括処理: 効率的バッチ処理
    """
    
    def __init__(self, domain_service, data_bus, performance_monitor=None):
        """
        初期化
        
        Args:
            domain_service: Domain層サービス
            data_bus: Data Bus通信
            performance_monitor: 性能監視（オプション）
        """
        self.domain_service = domain_service
        self.data_bus = data_bus
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self._lock = threading.RLock()
        
        # 性能最適化用キャッシュ
        self._validation_cache = {}
        self._entity_cache = {}
        
    @lru_cache(maxsize=1000)
    def _validate_coordinate_range(self, x: float, y: float, w: float, h: float) -> bool:
        """座標範囲検証（キャッシュ付き）"""
        return (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and 
                0.0 < w <= 1.0 and 0.0 < h <= 1.0 and
                x + w <= 1.0 and y + h <= 1.0)
    
    @lru_cache(maxsize=100)
    def _validate_id_range(self, individual_id: int, action_id: int) -> bool:
        """ID範囲検証（キャッシュ付き）"""
        return (0 <= individual_id <= 15 and 0 <= action_id <= 4)
    
    def _create_bb_entity(self, request: BBCreationRequest) -> BBEntity:
        """BBエンティティ作成"""
        return BBEntity(
            id=f"bb_{uuid.uuid4().hex[:8]}",
            x=request.x,
            y=request.y,
            w=request.w,
            h=request.h,
            individual_id=request.individual_id,
            action_id=request.action_id,
            confidence=request.confidence,
            frame_id=request.frame_id or "current",
            created_at=time.time()
        )
    
    def _publish_bb_event(self, event_type: str, bb: BBEntity, **extra_data):
        """BBイベント発行"""
        try:
            event_data = {
                "bb": bb,
                "frame_id": bb.frame_id,
                "timestamp": time.time(),
                **extra_data
            }
            self.data_bus.publish(event_type, **event_data)
        except Exception as e:
            # イベント発行エラーは警告レベル（処理継続）
            print(f"Warning: Failed to publish {event_type} event: {e}")
    
    @PerformanceMonitor().measure_time("create_bb")
    def create_bounding_box(self, request: BBCreationRequest) -> BBEntity:
        """
        BB作成統合処理（10ms以下必達）
        
        フロー:
        1. 座標検証（Domain層）
        2. BBエンティティ生成（Domain層）
        3. 重複チェック（Domain層）
        4. 作成イベント発行（Data Bus）
        
        Args:
            request: BB作成要求
            
        Returns:
            BBEntity: 作成されたBBエンティティ
            
        Raises:
            ValidationError: 検証エラー
            ServiceError: サービス処理エラー
        """
        try:
            with self._lock:
                # 高速検証（キャッシュ活用）
                if not self._validate_coordinate_range(request.x, request.y, request.w, request.h):
                    raise ValidationError(f"Invalid coordinates: ({request.x}, {request.y}, {request.w}, {request.h})")
                
                if not self._validate_id_range(request.individual_id, request.action_id):
                    raise ValidationError(f"Invalid IDs: individual={request.individual_id}, action={request.action_id}")
                
                # Domain層検証
                if not self.domain_service.validate_bb({
                    "x": request.x, "y": request.y, "w": request.w, "h": request.h,
                    "individual_id": request.individual_id, "action_id": request.action_id
                }):
                    raise ValidationError("Domain validation failed")
                
                # BBエンティティ作成
                bb_entity = self._create_bb_entity(request)
                
                # Domain層でのBB作成
                domain_bb = self.domain_service.create_bb_entity(
                    bb_entity.x, bb_entity.y, bb_entity.w, bb_entity.h,
                    bb_entity.individual_id, bb_entity.action_id, bb_entity.confidence
                )
                
                # 重複チェック
                if self.domain_service.check_bb_overlap(domain_bb):
                    raise ValidationError("BB overlaps with existing BB")
                
                # エンティティキャッシュ更新
                self._entity_cache[bb_entity.id] = bb_entity
                
                # 作成イベント発行（非同期）
                self._publish_bb_event("bb_created", bb_entity)
                
                return bb_entity
                
        except (ValidationError, ServiceError):
            raise
        except Exception as e:
            raise ServiceError(f"BB creation failed: {str(e)}") from e
    
    @PerformanceMonitor().measure_time("delete_bb")
    def delete_bounding_box(self, request: BBDeletionRequest) -> bool:
        """
        BB削除統合処理（5ms以下必達）
        
        Args:
            request: BB削除要求
            
        Returns:
            bool: 削除成功フラグ
            
        Raises:
            ServiceError: 削除処理エラー
        """
        try:
            with self._lock:
                # Domain層での削除
                if not self.domain_service.delete_bb_entity(request.bb_id):
                    raise ServiceError(f"Failed to delete BB: {request.bb_id}")
                
                # キャッシュから削除
                self._entity_cache.pop(request.bb_id, None)
                
                # 削除イベント発行
                self._publish_bb_event("bb_deleted", 
                                     bb_id=request.bb_id, 
                                     frame_id=request.frame_id)
                
                return True
                
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(f"BB deletion failed: {str(e)}") from e
    
    @PerformanceMonitor().measure_time("update_bb")
    def update_bounding_box(self, request: BBUpdateRequest) -> BBEntity:
        """
        BB更新統合処理（8ms以下必達）
        
        Args:
            request: BB更新要求
            
        Returns:
            BBEntity: 更新後BBエンティティ
            
        Raises:
            ValidationError: 検証エラー
            ServiceError: 更新処理エラー
        """
        try:
            with self._lock:
                # 既存BBエンティティ取得
                bb_entity = self._entity_cache.get(request.bb_id)
                if not bb_entity:
                    raise ServiceError(f"BB not found: {request.bb_id}")
                
                # 更新データ検証
                if "x" in request.properties or "y" in request.properties or \
                   "w" in request.properties or "h" in request.properties:
                    x = request.properties.get("x", bb_entity.x)
                    y = request.properties.get("y", bb_entity.y)
                    w = request.properties.get("w", bb_entity.w)
                    h = request.properties.get("h", bb_entity.h)
                    
                    if not self._validate_coordinate_range(x, y, w, h):
                        raise ValidationError("Invalid coordinate update")
                
                # エンティティ更新
                for key, value in request.properties.items():
                    if hasattr(bb_entity, key):
                        setattr(bb_entity, key, value)
                
                bb_entity.updated_at = time.time()
                
                # Domain層更新
                updated_domain_bb = self.domain_service.update_bb_entity(
                    request.bb_id, request.properties
                )
                
                # キャッシュ更新
                self._entity_cache[request.bb_id] = bb_entity
                
                # 更新イベント発行
                self._publish_bb_event("bb_updated", bb_entity, 
                                     properties=request.properties)
                
                return bb_entity
                
        except (ValidationError, ServiceError):
            raise
        except Exception as e:
            raise ServiceError(f"BB update failed: {str(e)}") from e
    
    def batch_create_bounding_boxes(self, requests: List[BBCreationRequest]) -> List[BBEntity]:
        """
        一括BB作成（効率的バッチ処理）
        
        Args:
            requests: BB作成要求リスト
            
        Returns:
            List[BBEntity]: 作成されたBBエンティティリスト
        """
        try:
            results = []
            
            # バッチ処理最適化
            if len(requests) > 50:
                # 並列処理
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [executor.submit(self.create_bounding_box, req) 
                             for req in requests]
                    results = [future.result() for future in futures]
            else:
                # 順次処理
                results = [self.create_bounding_box(req) for req in requests]
            
            return results
            
        except Exception as e:
            raise ServiceError(f"Batch creation failed: {str(e)}") from e
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """性能統計情報取得"""
        return {
            "create_bb": self.performance_monitor.get_stats("create_bb"),
            "delete_bb": self.performance_monitor.get_stats("delete_bb"),
            "update_bb": self.performance_monitor.get_stats("update_bb"),
        }
    
    def clear_cache(self):
        """キャッシュクリア"""
        with self._lock:
            self._validation_cache.clear()
            self._entity_cache.clear()
            self._validate_coordinate_range.cache_clear()
            self._validate_id_range.cache_clear()
    
    def get_cached_bb(self, bb_id: str) -> Optional[BBEntity]:
        """キャッシュされたBB取得"""
        return self._entity_cache.get(bb_id)
    
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        stats = self.get_performance_stats()
        
        health_status = {
            "status": "healthy",
            "cache_size": len(self._entity_cache),
            "performance": {},
            "warnings": []
        }
        
        # 性能チェック
        for operation, stat in stats.items():
            if not stat:
                continue
                
            avg_time = stat.get("avg", 0)
            max_time = stat.get("max", 0)
            
            # 性能目標チェック
            targets = {"create_bb": 10, "delete_bb": 5, "update_bb": 8}
            target = targets.get(operation, 10)
            
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