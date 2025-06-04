# Agent3: Domain Layer 詳細仕様書（ドメインロジック Agent）

## 🎯 Agent3 Domain の使命
**ビジネスオブジェクト・ルール・アルゴリズム** - 純粋ドメインロジック実装

## 📋 Agent3開始時の必須確認項目

### 開発開始前チェックリスト
- [ ] CLAUDE.md読了（Agent3責任範囲確認）
- [ ] requirement.yaml確認（ドメイン要件理解）
- [ ] config/performance_targets.yaml確認（計算性能目標）
- [ ] config/layer_interfaces.yaml確認（他層依存なし原則）
- [ ] tests/requirements/unit/domain-unit-tests.md確認（テスト要件）

### Agent3専門領域
```
責任範囲: ビジネスオブジェクト・ルール・アルゴリズム・計算処理
技術領域: エンティティ、値オブジェクト、ドメインサービス、アルゴリズム
実装場所: src/domain/
テスト場所: tests/unit/test_domain/
依存関係: 他層依存なし（純粋ドメインロジック）
```

## 🏗️ 実装すべきコンポーネント詳細

### 1. entities/ - ドメインエンティティ
```
src/domain/entities/
├── __init__.py
├── bb_entity.py           # BBエンティティ
├── frame_entity.py        # フレームエンティティ
├── project_entity.py      # プロジェクトエンティティ
├── id_entity.py          # 個体IDエンティティ
└── action_entity.py      # 行動エンティティ
```

#### bb_entity.py 仕様
```python
@dataclass
class BBEntity:
    """
    バウンディングボックスエンティティ
    
    ドメインルール:
    - 座標: YOLO正規化座標（0.0-1.0）
    - 個体ID: 0-15の範囲
    - 行動ID: 0-4の範囲（sit/stand/milk/water/food）
    - 信頼度: 0.0-1.0の範囲
    """
    
    id: str                    # 一意識別子
    frame_id: str             # 所属フレームID
    individual_id: int        # 個体ID（0-15）
    action_id: int           # 行動ID（0-4）
    coordinates: Coordinates  # YOLO正規化座標
    confidence: float        # 信頼度（0.0-1.0）
    created_at: datetime     # 作成日時
    updated_at: datetime     # 更新日時
    
    def __post_init__(self):
        """エンティティ検証"""
        self._validate_individual_id()
        self._validate_action_id()
        self._validate_confidence()
        
    def _validate_individual_id(self):
        """個体ID検証（0-15範囲）"""
        if not 0 <= self.individual_id <= 15:
            raise DomainError(f"Individual ID must be 0-15: {self.individual_id}")
            
    def _validate_action_id(self):
        """行動ID検証（0-4範囲）"""
        if not 0 <= self.action_id <= 4:
            raise DomainError(f"Action ID must be 0-4: {self.action_id}")
            
    def _validate_confidence(self):
        """信頼度検証（0.0-1.0範囲）"""
        if not 0.0 <= self.confidence <= 1.0:
            raise DomainError(f"Confidence must be 0.0-1.0: {self.confidence}")
            
    def get_area(self) -> float:
        """BB面積計算（YOLO座標）"""
        return self.coordinates.w * self.coordinates.h
        
    def get_center(self) -> Tuple[float, float]:
        """BB中心座標取得"""
        return (self.coordinates.x, self.coordinates.y)
        
    def overlaps_with(self, other: 'BBEntity') -> bool:
        """他BBとの重複判定"""
        return self.coordinates.overlaps_with(other.coordinates)
```

#### frame_entity.py 仕様
```python
@dataclass
class FrameEntity:
    """
    フレームエンティティ
    
    ドメインルール:
    - フレームID: 6桁ゼロパディング（000000-999999）
    - 解像度: 4K基準（3840x2160）
    - BB数: 個体数上限16個体対応
    """
    
    id: str                          # フレームID（000000形式）
    image_path: str                  # 画像ファイルパス
    annotation_path: str             # アノテーションファイルパス
    width: int                       # 画像幅
    height: int                      # 画像高さ
    bounding_boxes: List[BBEntity]   # BB一覧
    created_at: datetime            # 作成日時
    
    def add_bounding_box(self, bb: BBEntity) -> None:
        """BB追加（重複チェック付き）"""
        if self._has_duplicate_bb(bb):
            raise DomainError(f"Duplicate BB detected: {bb.id}")
        self.bounding_boxes.append(bb)
        
    def remove_bounding_box(self, bb_id: str) -> bool:
        """BB削除"""
        original_count = len(self.bounding_boxes)
        self.bounding_boxes = [bb for bb in self.bounding_boxes if bb.id != bb_id]
        return len(self.bounding_boxes) < original_count
        
    def get_bounding_boxes_by_individual(self, individual_id: int) -> List[BBEntity]:
        """個体ID別BB取得"""
        return [bb for bb in self.bounding_boxes if bb.individual_id == individual_id]
        
    def _has_duplicate_bb(self, new_bb: BBEntity) -> bool:
        """BB重複チェック（同一個体・高重複度）"""
        for existing_bb in self.bounding_boxes:
            if (existing_bb.individual_id == new_bb.individual_id and
                existing_bb.coordinates.iou_with(new_bb.coordinates) > 0.8):
                return True
        return False
```

### 2. value_objects/ - 値オブジェクト
```
src/domain/value_objects/
├── __init__.py
├── coordinates.py         # 座標値オブジェクト
├── confidence.py         # 信頼度値オブジェクト
└── color_mapping.py      # 色マッピング値オブジェクト
```

#### coordinates.py 仕様
```python
@dataclass(frozen=True)
class Coordinates:
    """
    YOLO正規化座標値オブジェクト
    
    性能要件:
    - 座標変換: 0.5ms以下
    - IOU計算: 1ms以下
    - 重複判定: 0.5ms以下
    """
    
    x: float  # 中心X座標（0.0-1.0）
    y: float  # 中心Y座標（0.0-1.0）
    w: float  # 幅（0.0-1.0）
    h: float  # 高さ（0.0-1.0）
    
    def __post_init__(self):
        """座標検証"""
        for coord_name, coord_value in [('x', self.x), ('y', self.y), 
                                       ('w', self.w), ('h', self.h)]:
            if not 0.0 <= coord_value <= 1.0:
                raise DomainError(f"{coord_name} must be 0.0-1.0: {coord_value}")
                
    def to_pixel_coordinates(self, image_width: int, image_height: int) -> 'PixelCoordinates':
        """
        YOLO→ピクセル座標変換（0.5ms以下必達）
        
        Returns:
            PixelCoordinates: ピクセル座標
        """
        pixel_x = int(self.x * image_width)
        pixel_y = int(self.y * image_height)
        pixel_w = int(self.w * image_width)
        pixel_h = int(self.h * image_height)
        return PixelCoordinates(pixel_x, pixel_y, pixel_w, pixel_h)
        
    def iou_with(self, other: 'Coordinates') -> float:
        """
        IOU計算（1ms以下必達）
        
        Args:
            other: 比較対象座標
            
        Returns:
            float: IOU値（0.0-1.0）
        """
        # 高速化のためNumPy使用
        x1_min, y1_min = self.x - self.w/2, self.y - self.h/2
        x1_max, y1_max = self.x + self.w/2, self.y + self.h/2
        x2_min, y2_min = other.x - other.w/2, other.y - other.h/2
        x2_max, y2_max = other.x + other.w/2, other.y + other.h/2
        
        # 交差領域計算
        intersection_xmin = max(x1_min, x2_min)
        intersection_ymin = max(y1_min, y2_min)
        intersection_xmax = min(x1_max, x2_max)
        intersection_ymax = min(y1_max, y2_max)
        
        if intersection_xmin >= intersection_xmax or intersection_ymin >= intersection_ymax:
            return 0.0
            
        intersection_area = (intersection_xmax - intersection_xmin) * (intersection_ymax - intersection_ymin)
        union_area = (self.w * self.h) + (other.w * other.h) - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0
        
    def overlaps_with(self, other: 'Coordinates', threshold: float = 0.1) -> bool:
        """重複判定（0.5ms以下必達）"""
        return self.iou_with(other) > threshold
```

### 3. algorithms/ - ドメインアルゴリズム
```
src/domain/algorithms/
├── __init__.py
├── iou_calculator.py      # IOU計算アルゴリズム
├── coordinate_transformer.py  # 座標変換アルゴリズム
└── tracking_algorithm.py # 追跡アルゴリズム
```

#### iou_calculator.py 仕様
```python
class IOUCalculator:
    """
    高速IOU計算エンジン
    
    性能要件:
    - 単体IOU計算: 1ms以下
    - バッチIOU計算: 100ペア/10ms以下
    - メモリ効率: NumPy vectorized計算
    """
    
    @staticmethod
    def calculate_iou(bb1: BBEntity, bb2: BBEntity) -> float:
        """
        単体IOU計算（1ms以下必達）
        
        Returns:
            float: IOU値（0.0-1.0）
        """
        return bb1.coordinates.iou_with(bb2.coordinates)
        
    @staticmethod
    def calculate_iou_matrix(bb_list1: List[BBEntity], 
                           bb_list2: List[BBEntity]) -> np.ndarray:
        """
        IOU行列計算（バッチ処理最適化）
        
        Args:
            bb_list1: BBリスト1
            bb_list2: BBリスト2
            
        Returns:
            np.ndarray: IOU行列（len(bb_list1) x len(bb_list2)）
        """
        # NumPy vectorized計算で高速化
        coords1 = np.array([[bb.coordinates.x, bb.coordinates.y, 
                           bb.coordinates.w, bb.coordinates.h] 
                          for bb in bb_list1])
        coords2 = np.array([[bb.coordinates.x, bb.coordinates.y,
                           bb.coordinates.w, bb.coordinates.h] 
                          for bb in bb_list2])
        
        return IOUCalculator._vectorized_iou_calculation(coords1, coords2)
        
    @staticmethod
    def _vectorized_iou_calculation(coords1: np.ndarray, 
                                  coords2: np.ndarray) -> np.ndarray:
        """NumPy vectorized IOU計算"""
        # 高速化実装（詳細省略）
        pass
        
    @staticmethod
    def find_best_matches(source_bbs: List[BBEntity], 
                         target_bbs: List[BBEntity],
                         iou_threshold: float = 0.5) -> List[Tuple[str, str, float]]:
        """
        最適マッチング検索（追跡用）
        
        Returns:
            List[Tuple[source_id, target_id, iou_score]]: マッチング結果
        """
```

#### tracking_algorithm.py 仕様
```python
class SimpleIOUTracker:
    """
    シンプルIOU追跡アルゴリズム
    
    アルゴリズム:
    1. フレーム間IOU計算
    2. 閾値以上の最高IOUペアを対応付け
    3. 対応なしBBは新規ID割り当て
    4. 消失BBは追跡断絶記録
    
    性能要件:
    - 追跡処理: 5ms以下
    - 精度: 一般的使用で90%以上
    """
    
    def __init__(self, iou_threshold: float = 0.5):
        self.iou_threshold = iou_threshold
        
    def track_between_frames(self, source_frame: FrameEntity,
                           target_frame: FrameEntity) -> TrackingResult:
        """
        フレーム間追跡（5ms以下必達）
        
        Args:
            source_frame: 追跡元フレーム
            target_frame: 追跡先フレーム
            
        Returns:
            TrackingResult: 追跡結果
        """
        source_bbs = source_frame.bounding_boxes
        target_bbs = target_frame.bounding_boxes
        
        # IOU行列計算
        iou_matrix = IOUCalculator.calculate_iou_matrix(source_bbs, target_bbs)
        
        # 最適マッチング検索
        matches = self._find_optimal_matching(source_bbs, target_bbs, iou_matrix)
        
        # 追跡結果生成
        return self._generate_tracking_result(matches, source_bbs, target_bbs)
        
    def _find_optimal_matching(self, source_bbs: List[BBEntity],
                             target_bbs: List[BBEntity],
                             iou_matrix: np.ndarray) -> List[TrackingMatch]:
        """最適マッチング検索（貪欲アルゴリズム）"""
        
    def _generate_tracking_result(self, matches: List[TrackingMatch],
                                source_bbs: List[BBEntity],
                                target_bbs: List[BBEntity]) -> TrackingResult:
        """追跡結果生成"""
```

### 4. repositories/ - リポジトリインターフェース
```
src/domain/repositories/
├── __init__.py
├── bb_repository.py       # BBリポジトリ
├── frame_repository.py    # フレームリポジトリ
└── project_repository.py  # プロジェクトリポジトリ
```

#### bb_repository.py 仕様
```python
from abc import ABC, abstractmethod

class BBRepository(ABC):
    """
    BBリポジトリインターフェース
    （実装はPersistence層で提供）
    """
    
    @abstractmethod
    def save_bb(self, bb: BBEntity) -> bool:
        """BB保存"""
        
    @abstractmethod
    def load_bbs_by_frame(self, frame_id: str) -> List[BBEntity]:
        """フレーム別BB読み込み"""
        
    @abstractmethod
    def delete_bb(self, bb_id: str) -> bool:
        """BB削除"""
        
    @abstractmethod
    def find_bbs_by_individual(self, individual_id: int) -> List[BBEntity]:
        """個体別BB検索"""
```

## ⚡ パフォーマンス要件詳細

### 計算性能目標
```yaml
iou_calculation:
  target: "1ms以下"
  measurement: "単体IOU計算時間"
  test_cases: "1000ペア計算"
  optimization: "NumPy vectorized計算"
  
coordinate_transform:
  target: "0.5ms以下"
  measurement: "YOLO↔ピクセル変換時間"
  batch_size: "100BB一括変換"
  
entity_operation:
  target: "1ms以下"
  operations: ["作成", "更新", "削除", "検索"]
  
business_rules:
  target: "2ms以下"
  rules: ["ID範囲チェック", "BB重複チェック", "追跡ルール"]
```

### 計算最適化戦略
```python
# NumPy vectorized計算
import numpy as np

class OptimizedCalculations:
    """最適化された計算処理"""
    
    @staticmethod
    @lru_cache(maxsize=10000)
    def cached_iou_calculation(coords1: Tuple, coords2: Tuple) -> float:
        """キャッシュ付きIOU計算"""
        
    @staticmethod
    def batch_coordinate_transform(coordinates_list: List[Coordinates],
                                 image_width: int, image_height: int) -> List[PixelCoordinates]:
        """一括座標変換（NumPy活用）"""
        coords_array = np.array([[c.x, c.y, c.w, c.h] for c in coordinates_list])
        # vectorized変換処理
        return transformed_coords
```

## 🧪 テスト要件（TDD必須）

### 単体テスト必須項目
```python
# tests/unit/test_domain/test_bb_entity.py
class TestBBEntity:
    def test_entity_validation(self):
        """エンティティ検証確認"""
        
    def test_bb_overlap_detection(self):
        """BB重複検知確認"""
        
    def test_entity_immutability(self):
        """エンティティ不変性確認"""

# tests/unit/test_domain/test_coordinates.py
class TestCoordinates:
    def test_coordinate_transform_0_5ms(self):
        """座標変換0.5ms以下確認"""
        
    def test_iou_calculation_1ms(self):
        """IOU計算1ms以下確認"""
        
    def test_coordinate_validation(self):
        """座標検証確認"""

# tests/unit/test_domain/test_tracking_algorithm.py
class TestTrackingAlgorithm:
    def test_tracking_accuracy_90_percent(self):
        """追跡精度90%以上確認"""
        
    def test_tracking_performance_5ms(self):
        """追跡処理5ms以下確認"""
```

## 🛠️ 実装ガイドライン

### 必須技術スタック
```python
import numpy as np          # 高速数値計算
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
import uuid
from functools import lru_cache
```

### ドメインエラー定義
```python
class DomainError(Exception):
    """ドメイン層エラー基底クラス"""
    
class ValidationError(DomainError):
    """検証エラー"""
    
class BusinessRuleViolationError(DomainError):
    """ビジネスルール違反エラー"""
    
class EntityNotFoundError(DomainError):
    """エンティティ未発見エラー"""
```

### 不変性・純粋性原則
```python
# 値オブジェクトは不変
@dataclass(frozen=True)
class ValueObject:
    """値オブジェクト基底クラス"""
    
# エンティティの状態変更は新インスタンス生成
def update_bb_coordinates(bb: BBEntity, new_coords: Coordinates) -> BBEntity:
    """BB座標更新（新インスタンス生成）"""
    return BBEntity(
        id=bb.id,
        frame_id=bb.frame_id,
        individual_id=bb.individual_id,
        action_id=bb.action_id,
        coordinates=new_coords,  # 更新
        confidence=bb.confidence,
        created_at=bb.created_at,
        updated_at=datetime.now()  # 更新
    )
```

## ✅ Agent3完了条件

### 機能完了チェック
- [ ] BBエンティティ（検証・操作・計算）
- [ ] フレームエンティティ（BB管理・検索）
- [ ] 座標値オブジェクト（変換・IOU・重複判定）
- [ ] 追跡アルゴリズム（IOU追跡・マッチング）

### 性能完了チェック
- [ ] IOU計算1ms以下
- [ ] 座標変換0.5ms以下
- [ ] エンティティ操作1ms以下
- [ ] ビジネスルール適用2ms以下

### テスト完了チェック
- [ ] 単体テスト100%通過
- [ ] 計算精度テスト100%通過
- [ ] 性能テスト100%通過
- [ ] ビジネスルールテスト100%通過

---

**Agent3 Domainは、アプリケーションの核心的ビジネスロジックを担います。高速で正確な計算処理により、動物行動アノテーションの品質と効率を保証します。**