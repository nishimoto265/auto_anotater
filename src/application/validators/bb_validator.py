"""
BBValidator - Agent2 Application Layer
BB検証クラス

性能要件:
- 基本検証: 1ms以下
- 複合検証: 3ms以下
- バッチ検証: 効率的処理
"""

import time
import threading
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import math


class ValidationError(Exception):
    """検証エラー基底クラス"""
    pass


class CoordinateValidationError(ValidationError):
    """座標検証エラー"""
    pass


class IDValidationError(ValidationError):
    """ID検証エラー"""
    pass


class ErrorSeverity(Enum):
    """エラー重要度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationErrorDetail:
    """検証エラー詳細"""
    field: str
    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    expected: Optional[Any] = None
    actual: Optional[Any] = None


@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool
    errors: List[ValidationErrorDetail] = field(default_factory=list)
    warnings: List[ValidationErrorDetail] = field(default_factory=list)
    validation_time: float = 0.0  # ms
    
    def add_error(self, field: str, message: str, expected=None, actual=None):
        """エラー追加"""
        self.errors.append(ValidationErrorDetail(
            field=field, message=message, severity=ErrorSeverity.ERROR,
            expected=expected, actual=actual
        ))
        self.is_valid = False
    
    def add_warning(self, field: str, message: str, expected=None, actual=None):
        """警告追加"""
        self.warnings.append(ValidationErrorDetail(
            field=field, message=message, severity=ErrorSeverity.WARNING,
            expected=expected, actual=actual
        ))


class PerformanceOptimizer:
    """性能最適化ヘルパー"""
    
    @staticmethod
    @lru_cache(maxsize=10000)
    def cached_coordinate_validation(x: float, y: float, w: float, h: float) -> bool:
        """座標検証（キャッシュ付き）"""
        # 基本範囲チェック
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            return False
        
        # 幅・高さの正の値チェック
        if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
            return False
        
        # 境界チェック（x+w, y+h <= 1.0）
        if not (x + w <= 1.0 and y + h <= 1.0):
            return False
        
        return True
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def cached_id_validation(individual_id: int, action_id: int) -> bool:
        """ID検証（キャッシュ付き）"""
        # individual_id: 0-15
        if not (0 <= individual_id <= 15):
            return False
        
        # action_id: 0-4 (sit=0, stand=1, milk=2, water=3, food=4)
        if not (0 <= action_id <= 4):
            return False
        
        return True
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def cached_confidence_validation(confidence: float) -> bool:
        """信頼度検証（キャッシュ付き）"""
        return 0.0 <= confidence <= 1.0
    
    @staticmethod
    def calculate_iou_fast(bb1: Dict[str, float], bb2: Dict[str, float]) -> float:
        """高速IOU計算"""
        # BB1の座標
        x1, y1, w1, h1 = bb1["x"], bb1["y"], bb1["w"], bb1["h"]
        left1, top1, right1, bottom1 = x1, y1, x1 + w1, y1 + h1
        
        # BB2の座標
        x2, y2, w2, h2 = bb2["x"], bb2["y"], bb2["w"], bb2["h"]
        left2, top2, right2, bottom2 = x2, y2, x2 + w2, y2 + h2
        
        # 交差領域
        intersection_left = max(left1, left2)
        intersection_top = max(top1, top2)
        intersection_right = min(right1, right2)
        intersection_bottom = min(bottom1, bottom2)
        
        # 交差面積
        if intersection_left >= intersection_right or intersection_top >= intersection_bottom:
            intersection_area = 0.0
        else:
            intersection_area = (intersection_right - intersection_left) * (intersection_bottom - intersection_top)
        
        # 各BBの面積
        area1 = w1 * h1
        area2 = w2 * h2
        
        # 和集合面積
        union_area = area1 + area2 - intersection_area
        
        # IOU計算
        return intersection_area / union_area if union_area > 0 else 0.0


class BBValidator:
    """
    BB検証クラス
    
    性能要件:
    - 基本検証: 1ms以下
    - 複合検証: 3ms以下
    - バッチ検証: 効率的処理
    """
    
    def __init__(self, overlap_threshold: float = 0.5, confidence_threshold: float = 0.0):
        """
        初期化
        
        Args:
            overlap_threshold: 重複判定閾値
            confidence_threshold: 信頼度下限閾値
        """
        self.overlap_threshold = overlap_threshold
        self.confidence_threshold = confidence_threshold
        self._lock = threading.RLock()
        
        # 必須フィールド定義
        self.required_fields = {"x", "y", "w", "h", "individual_id", "action_id"}
        self.optional_fields = {"confidence"}
        
        # 統計情報
        self._stats = {
            "basic_validation": {"times": [], "count": 0},
            "overlap_validation": {"times": [], "count": 0},
            "batch_validation": {"times": [], "count": 0}
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
    
    def _validate_required_fields(self, bb_data: Dict[str, Any], result: ValidationResult) -> bool:
        """必須フィールド検証"""
        missing_fields = self.required_fields - set(bb_data.keys())
        
        for field in missing_fields:
            result.add_error(field, f"Required field '{field}' is missing")
        
        return len(missing_fields) == 0
    
    def _validate_field_types(self, bb_data: Dict[str, Any], result: ValidationResult) -> bool:
        """フィールド型検証"""
        type_checks = [
            ("x", (int, float)), ("y", (int, float)), 
            ("w", (int, float)), ("h", (int, float)),
            ("individual_id", int), ("action_id", int)
        ]
        
        if "confidence" in bb_data:
            type_checks.append(("confidence", (int, float)))
        
        all_valid = True
        for field, expected_types in type_checks:
            if field in bb_data:
                value = bb_data[field]
                if not isinstance(value, expected_types):
                    result.add_error(field, f"Field '{field}' must be {expected_types}", 
                                   expected_types, type(value).__name__)
                    all_valid = False
        
        return all_valid
    
    @_measure_time("basic_validation")
    def validate_bb_creation(self, bb_data: Dict[str, Any]) -> ValidationResult:
        """
        BB作成検証（1ms以下必達）
        
        検証項目:
        - 座標範囲（0.0-1.0 for YOLO）
        - 個体ID範囲（0-15）
        - 行動ID範囲（0-4）
        - 信頼度範囲（0.0-1.0）
        
        Args:
            bb_data: 検証対象BBデータ
            
        Returns:
            ValidationResult: 検証結果
        """
        start_time = time.perf_counter()
        result = ValidationResult(is_valid=True)
        
        try:
            # 必須フィールド検証
            if not self._validate_required_fields(bb_data, result):
                result.validation_time = (time.perf_counter() - start_time) * 1000
                return result
            
            # 型検証
            if not self._validate_field_types(bb_data, result):
                result.validation_time = (time.perf_counter() - start_time) * 1000
                return result
            
            # 座標検証（高速キャッシュ使用）
            x, y, w, h = bb_data["x"], bb_data["y"], bb_data["w"], bb_data["h"]
            if not PerformanceOptimizer.cached_coordinate_validation(x, y, w, h):
                result.add_error("coordinates", 
                               f"Invalid coordinates: x={x}, y={y}, w={w}, h={h}. Must be in range [0.0, 1.0] with x+w≤1.0, y+h≤1.0",
                               "0.0 ≤ x,y,w,h ≤ 1.0, x+w≤1.0, y+h≤1.0", f"x={x}, y={y}, w={w}, h={h}")
            
            # ID検証（高速キャッシュ使用）
            individual_id, action_id = bb_data["individual_id"], bb_data["action_id"]
            if not PerformanceOptimizer.cached_id_validation(individual_id, action_id):
                result.add_error("ids", 
                               f"Invalid IDs: individual_id={individual_id}, action_id={action_id}",
                               "individual_id: 0-15, action_id: 0-4", 
                               f"individual_id={individual_id}, action_id={action_id}")
            
            # 信頼度検証（オプション）
            if "confidence" in bb_data:
                confidence = bb_data["confidence"]
                if not PerformanceOptimizer.cached_confidence_validation(confidence):
                    result.add_error("confidence", 
                                   f"Invalid confidence: {confidence}. Must be in range [0.0, 1.0]",
                                   "0.0 ≤ confidence ≤ 1.0", confidence)
                elif confidence < self.confidence_threshold:
                    result.add_warning("confidence", 
                                     f"Low confidence: {confidence} < {self.confidence_threshold}")
            
            result.validation_time = (time.perf_counter() - start_time) * 1000
            return result
            
        except Exception as e:
            result.add_error("validation", f"Validation error: {str(e)}")
            result.validation_time = (time.perf_counter() - start_time) * 1000
            return result
    
    @_measure_time("overlap_validation")
    def validate_bb_overlap(self, new_bb: Dict[str, Any], existing_bbs: List[Dict[str, Any]]) -> ValidationResult:
        """
        BB重複検証（3ms以下）
        
        Args:
            new_bb: 新規BBデータ
            existing_bbs: 既存BBリスト
            
        Returns:
            ValidationResult: 検証結果
        """
        start_time = time.perf_counter()
        result = ValidationResult(is_valid=True)
        
        try:
            # 基本検証先行
            basic_result = self.validate_bb_creation(new_bb)
            if not basic_result.is_valid:
                result.errors.extend(basic_result.errors)
                result.warnings.extend(basic_result.warnings)
                result.validation_time = (time.perf_counter() - start_time) * 1000
                return result
            
            # 重複チェック（高速IOU計算）
            for i, existing_bb in enumerate(existing_bbs):
                try:
                    iou = PerformanceOptimizer.calculate_iou_fast(new_bb, existing_bb)
                    
                    if iou >= self.overlap_threshold:
                        result.add_error("overlap", 
                                       f"BB overlaps with existing BB[{i}] (IOU: {iou:.3f} >= {self.overlap_threshold})",
                                       f"IOU < {self.overlap_threshold}", f"IOU = {iou:.3f}")
                        break  # 最初の重複で終了（性能最適化）
                    elif iou > 0.1:  # 軽微な重複警告
                        result.add_warning("overlap", 
                                         f"Minor overlap with existing BB[{i}] (IOU: {iou:.3f})")
                except:
                    # IOU計算エラーは無視（性能優先）
                    continue
            
            result.validation_time = (time.perf_counter() - start_time) * 1000
            return result
            
        except Exception as e:
            result.add_error("overlap_validation", f"Overlap validation error: {str(e)}")
            result.validation_time = (time.perf_counter() - start_time) * 1000
            return result
    
    @_measure_time("batch_validation")
    def validate_batch_bbs(self, bb_list: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        一括BB検証（効率的処理）
        
        Args:
            bb_list: BBデータリスト
            
        Returns:
            List[ValidationResult]: 検証結果リスト
        """
        try:
            if not bb_list:
                return []
            
            results = []
            
            # 小規模バッチは順次処理
            if len(bb_list) <= 50:
                for bb_data in bb_list:
                    result = self.validate_bb_creation(bb_data)
                    results.append(result)
            else:
                # 大規模バッチは並列処理
                from concurrent.futures import ThreadPoolExecutor
                
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [executor.submit(self.validate_bb_creation, bb_data) 
                             for bb_data in bb_list]
                    results = [future.result() for future in futures]
            
            return results
            
        except Exception as e:
            # エラー時は単一エラー結果返却
            error_result = ValidationResult(is_valid=False)
            error_result.add_error("batch_validation", f"Batch validation error: {str(e)}")
            return [error_result] * len(bb_list)
    
    @lru_cache(maxsize=1000)
    def validate_coordinate_range(self, x: float, y: float, w: float, h: float) -> bool:
        """座標範囲検証（1ms以下、キャッシュ付き）"""
        return PerformanceOptimizer.cached_coordinate_validation(x, y, w, h)
    
    @lru_cache(maxsize=100)
    def validate_id_range(self, individual_id: int, action_id: int) -> bool:
        """ID範囲検証（1ms以下、キャッシュ付き）"""
        return PerformanceOptimizer.cached_id_validation(individual_id, action_id)
    
    def validate_bb_list_consistency(self, bb_list: List[Dict[str, Any]]) -> ValidationResult:
        """
        BBリスト一貫性検証
        
        Args:
            bb_list: BBリスト
            
        Returns:
            ValidationResult: 一貫性検証結果
        """
        result = ValidationResult(is_valid=True)
        
        try:
            # 同一フレーム内でのindividual_id重複チェック
            individual_ids = []
            for i, bb in enumerate(bb_list):
                if "individual_id" in bb:
                    individual_id = bb["individual_id"]
                    if individual_id in individual_ids:
                        result.add_error("consistency", 
                                       f"Duplicate individual_id {individual_id} at position {i}")
                    else:
                        individual_ids.append(individual_id)
            
            # 相互重複チェック（効率的）
            for i in range(len(bb_list)):
                for j in range(i + 1, len(bb_list)):
                    try:
                        iou = PerformanceOptimizer.calculate_iou_fast(bb_list[i], bb_list[j])
                        if iou >= self.overlap_threshold:
                            result.add_error("mutual_overlap", 
                                           f"BBs at positions {i} and {j} overlap (IOU: {iou:.3f})")
                    except:
                        continue
            
            return result
            
        except Exception as e:
            result.add_error("consistency_validation", f"Consistency validation error: {str(e)}")
            return result
    
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
            PerformanceOptimizer.cached_coordinate_validation.cache_clear()
            PerformanceOptimizer.cached_id_validation.cache_clear()
            PerformanceOptimizer.cached_confidence_validation.cache_clear()
            self.validate_coordinate_range.cache_clear()
            self.validate_id_range.cache_clear()
    
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        stats = self.get_performance_stats()
        
        health_status = {
            "status": "healthy",
            "overlap_threshold": self.overlap_threshold,
            "confidence_threshold": self.confidence_threshold,
            "performance": {},
            "warnings": []
        }
        
        # 性能チェック
        targets = {"basic_validation": 1, "overlap_validation": 3, "batch_validation": 100}
        
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