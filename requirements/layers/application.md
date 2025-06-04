# Agent2: Application Layer 詳細仕様書（ビジネスロジック統合Agent）

## 🎯 Agent2 Application の使命
**ワークフロー制御・ビジネスロジック統合** - UI操作をドメイン処理に橋渡し

## 📋 Agent2開始時の必須確認項目

### 開発開始前チェックリスト
- [ ] CLAUDE.md読了（Agent2責任範囲確認）
- [ ] requirement.yaml確認（アプリケーション要件理解）
- [ ] config/performance_targets.yaml確認（処理性能目標10ms）
- [ ] config/layer_interfaces.yaml確認（Presentation・Domain層連携）
- [ ] tests/requirements/unit/application-unit-tests.md確認（テスト要件）

### Agent2専門領域
```
責任範囲: ワークフロー制御・ビジネスロジック統合・操作検証
技術領域: サービス層、コントローラー、バリデーター、ワークフロー
実装場所: src/application/
テスト場所: tests/unit/test_application/
```

## 🏗️ 実装すべきコンポーネント詳細

### 1. services/ - アプリケーションサービス
```
src/application/services/
├── __init__.py
├── annotation_service.py   # アノテーション統合処理
├── tracking_service.py     # 追跡制御サービス
├── project_service.py      # プロジェクト管理サービス
└── workflow_service.py     # ワークフロー制御サービス
```

#### annotation_service.py 仕様
```python
class AnnotationService:
    """
    アノテーション統合処理サービス
    
    性能要件:
    - BB作成処理: 10ms以下
    - BB削除処理: 5ms以下
    - BB更新処理: 8ms以下
    - 一括処理: 効率的バッチ処理
    """
    
    def __init__(self, domain_service, data_bus):
        self.domain_service = domain_service
        self.data_bus = data_bus
        
    def create_bounding_box(self, x: float, y: float, w: float, h: float,
                           individual_id: int, action_id: int, 
                           confidence: float = 1.0) -> BBEntity:
        """
        BB作成統合処理（10ms以下必達）
        
        フロー:
        1. 座標検証（Domain層）
        2. BBエンティティ生成（Domain層）
        3. 重複チェック（Domain層）
        4. 作成イベント発行（Data Bus）
        
        Args:
            x, y, w, h: BB座標（ピクセル）
            individual_id: 個体ID（0-15）
            action_id: 行動ID（0-4）
            confidence: 信頼度（0.0-1.0）
            
        Returns:
            BBEntity: 作成されたBBエンティティ
        """
        
    def delete_bounding_box(self, bb_id: str, frame_id: str) -> bool:
        """
        BB削除統合処理（5ms以下必達）
        
        Returns:
            bool: 削除成功フラグ
        """
        
    def update_bounding_box(self, bb_id: str, properties: dict) -> BBEntity:
        """
        BB更新統合処理（8ms以下必達）
        
        Args:
            bb_id: 更新対象BB ID
            properties: 更新プロパティ
            
        Returns:
            BBEntity: 更新後BBエンティティ
        """
        
    def batch_create_bounding_boxes(self, bb_data_list: List[dict]) -> List[BBEntity]:
        """一括BB作成（効率的バッチ処理）"""
```

#### tracking_service.py 仕様
```python
class TrackingService:
    """
    追跡制御サービス
    
    性能要件:
    - IOU追跡処理: 5ms以下
    - ID継承判定: 3ms以下
    - 追跡断絶検知: 2ms以下
    - 後続フレーム更新: バッチ処理最適化
    """
    
    def start_tracking(self, source_frame_id: str, target_frame_id: str,
                      individual_ids: List[int] = None) -> TrackingResult:
        """
        追跡処理開始（5ms以下必達）
        
        Args:
            source_frame_id: 追跡元フレーム
            target_frame_id: 追跡先フレーム
            individual_ids: 追跡対象ID（None時は全個体）
            
        Returns:
            TrackingResult: 追跡結果
        """
        
    def apply_tracking_results(self, tracking_result: TrackingResult) -> int:
        """
        追跡結果適用（後続フレーム一括更新）
        
        Returns:
            int: 更新フレーム数
        """
        
    def detect_tracking_break(self, frame_id: str) -> List[TrackingBreak]:
        """
        追跡断絶検知（2ms以下必達）
        
        Returns:
            List[TrackingBreak]: 断絶検知結果
        """
```

#### project_service.py 仕様
```python
class ProjectService:
    """
    プロジェクト管理サービス
    
    機能:
    - プロジェクト作成・読み込み・保存
    - 設定管理・メタデータ管理
    - 進捗状況管理・統計情報
    """
    
    def create_project(self, project_name: str, video_path: str,
                      config: ProjectConfig) -> Project:
        """新規プロジェクト作成"""
        
    def load_project(self, project_path: str) -> Project:
        """既存プロジェクト読み込み"""
        
    def save_project(self, project: Project) -> bool:
        """プロジェクト保存"""
        
    def get_project_statistics(self, project: Project) -> ProjectStats:
        """プロジェクト統計情報取得"""
```

### 2. controllers/ - コントローラー層
```
src/application/controllers/
├── __init__.py
├── frame_controller.py     # フレーム制御
├── bb_controller.py        # BB制御
└── navigation_controller.py # ナビゲーション制御
```

#### frame_controller.py 仕様
```python
class FrameController:
    """
    フレーム制御コントローラー
    
    性能要件:
    - フレーム切り替え制御: 5ms以下（Cache連携部分除く）
    - フレーム検証: 1ms以下
    - 自動保存制御: 非同期実行
    """
    
    def switch_to_frame(self, frame_id: str) -> FrameSwitchResult:
        """
        フレーム切り替え制御（5ms以下必達）
        
        フロー:
        1. フレームID検証（1ms以下）
        2. 現フレーム自動保存指示（非同期）
        3. Cache層フレーム要求（別途50ms目標）
        4. フレーム切り替えイベント発行
        
        Returns:
            FrameSwitchResult: 切り替え結果
        """
        
    def get_next_frame_id(self, current_frame_id: str) -> str:
        """次フレームID取得（1ms以下）"""
        
    def get_previous_frame_id(self, current_frame_id: str) -> str:
        """前フレームID取得（1ms以下）"""
        
    def validate_frame_id(self, frame_id: str) -> bool:
        """フレームID検証（1ms以下）"""
```

#### bb_controller.py 仕様
```python
class BBController:
    """
    BB制御コントローラー
    
    性能要件:
    - BB操作制御: 3ms以下
    - 検証処理: 1ms以下
    - 状態管理: リアルタイム
    """
    
    def handle_bb_creation(self, creation_request: BBCreationRequest) -> BBCreationResult:
        """
        BB作成制御（3ms以下必達）
        
        フロー:
        1. 作成要求検証（1ms以下）
        2. AnnotationService呼び出し
        3. 結果検証・エラーハンドリング
        
        Returns:
            BBCreationResult: 作成結果
        """
        
    def handle_bb_deletion(self, deletion_request: BBDeletionRequest) -> bool:
        """BB削除制御（2ms以下必達）"""
        
    def handle_bb_selection(self, bb_id: str) -> BBEntity:
        """BB選択制御（1ms以下）"""
```

### 3. validators/ - バリデーター
```
src/application/validators/
├── __init__.py
├── bb_validator.py         # BB検証
└── coordinate_validator.py # 座標検証
```

#### bb_validator.py 仕様
```python
class BBValidator:
    """
    BB検証クラス
    
    性能要件:
    - 基本検証: 1ms以下
    - 複合検証: 3ms以下
    - バッチ検証: 効率的処理
    """
    
    def validate_bb_creation(self, bb_data: dict) -> ValidationResult:
        """
        BB作成検証（1ms以下必達）
        
        検証項目:
        - 座標範囲（0.0-1.0 for YOLO）
        - 個体ID範囲（0-15）
        - 行動ID範囲（0-4）
        - 信頼度範囲（0.0-1.0）
        """
        
    def validate_bb_overlap(self, new_bb: BBEntity, 
                           existing_bbs: List[BBEntity]) -> ValidationResult:
        """BB重複検証（3ms以下）"""
        
    def validate_batch_bbs(self, bb_list: List[dict]) -> List[ValidationResult]:
        """一括BB検証（効率的処理）"""
```

## ⚡ パフォーマンス要件詳細

### 処理性能目標
```yaml
business_logic:
  target: "10ms以下"
  breakdown:
    bb_validation: "3ms以下"
    id_assignment: "2ms以下"
    tracking_control: "3ms以下"
    state_update: "2ms以下"
    
workflow_control:
  target: "5ms以下"
  operations:
    - "BB作成フロー"
    - "追跡フロー"  
    - "保存フロー"
    
operation_validation:
  target: "1ms以下"
  validations:
    - "座標範囲"
    - "ID重複"
    - "行動整合性"
```

### 処理効率最適化
```python
# 検証処理の最適化
@lru_cache(maxsize=1000)
def validate_coordinate_range(x: float, y: float, w: float, h: float) -> bool:
    """座標検証結果キャッシュ"""
    
# バッチ処理最適化
class BatchProcessor:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.pending_operations = []
        
    def add_operation(self, operation):
        """操作をバッチに追加"""
        
    def execute_batch(self):
        """バッチ実行（効率的処理）"""
```

## 🔗 他Agent連携インターフェース

### Presentation層との連携
```python
class PresentationApplicationBridge:
    """Presentation→Application連携"""
    
    def handle_ui_bb_creation(self, ui_event: UIBBCreationEvent) -> BBCreationResult:
        """UI BB作成イベント処理"""
        
    def handle_ui_frame_switch(self, ui_event: UIFrameSwitchEvent) -> FrameSwitchResult:
        """UI フレーム切り替えイベント処理"""
        
    def handle_ui_tracking_request(self, ui_event: UITrackingEvent) -> TrackingResult:
        """UI 追跡要求イベント処理"""
```

### Domain層との連携
```python
class ApplicationDomainBridge:
    """Application→Domain連携"""
    
    def create_domain_entity(self, application_data: dict) -> DomainEntity:
        """アプリケーションデータ→ドメインエンティティ変換"""
        
    def execute_domain_logic(self, domain_operation: str, **kwargs) -> Any:
        """ドメインロジック実行"""
        
    def validate_domain_rules(self, entity: DomainEntity) -> ValidationResult:
        """ドメインルール検証"""
```

## 🧪 テスト要件（TDD必須）

### 単体テスト必須項目
```python
# tests/unit/test_application/test_annotation_service.py
class TestAnnotationService:
    def test_create_bb_10ms(self):
        """BB作成処理10ms以下確認"""
        
    def test_delete_bb_5ms(self):
        """BB削除処理5ms以下確認"""
        
    def test_batch_processing_efficiency(self):
        """バッチ処理効率確認"""

# tests/unit/test_application/test_tracking_service.py
class TestTrackingService:
    def test_iou_tracking_5ms(self):
        """IOU追跡処理5ms以下確認"""
        
    def test_id_inheritance_accuracy(self):
        """ID継承精度確認"""
        
    def test_tracking_break_detection(self):
        """追跡断絶検知確認"""

# tests/unit/test_application/test_validators.py
class TestBBValidator:
    def test_validation_1ms(self):
        """検証処理1ms以下確認"""
        
    def test_validation_accuracy(self):
        """検証精度確認"""
```

### 統合テスト必須項目
```python
# tests/integration/test_application_integration.py
class TestApplicationIntegration:
    def test_presentation_layer_communication(self):
        """Presentation層連携確認"""
        
    def test_domain_layer_communication(self):
        """Domain層連携確認"""
        
    def test_complete_workflow(self):
        """完全ワークフロー確認"""
```

## 🛠️ 実装ガイドライン

### 必須技術スタック
```python
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import asyncio          # 非同期処理
import time            # 性能測定
from functools import lru_cache  # キャッシュ最適化
import uuid            # 一意ID生成
```

### エラーハンドリング
```python
class ApplicationError(Exception):
    """アプリケーション層エラー基底クラス"""
    
class ValidationError(ApplicationError):
    """検証エラー"""
    
class WorkflowError(ApplicationError):
    """ワークフローエラー"""
    
class ServiceError(ApplicationError):
    """サービスエラー"""

def with_error_handling(error_type: type = ApplicationError):
    """エラーハンドリングデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # エラー処理・ログ記録
                raise error_type(str(e)) from e
        return wrapper
    return decorator
```

### 非同期処理最適化
```python
class AsyncOperationManager:
    """非同期操作管理"""
    
    def __init__(self):
        self.background_tasks = []
        
    async def execute_background_save(self, data):
        """バックグラウンド保存"""
        
    async def execute_background_tracking(self, tracking_data):
        """バックグラウンド追跡処理"""
        
    def schedule_background_task(self, coro):
        """バックグラウンドタスクスケジュール"""
```

## 📊 ワークフロー監視

### 処理時間監視
```python
class WorkflowMonitor:
    """ワークフロー監視"""
    
    def measure_operation_time(self, operation_name: str):
        """操作時間測定デコレータ"""
        
    def record_workflow_step(self, step_name: str, duration: float):
        """ワークフローステップ記録"""
        
    def generate_performance_report(self) -> dict:
        """性能レポート生成"""
```

### ワークフロー統計
```python
class WorkflowStatistics:
    """ワークフロー統計"""
    
    def track_bb_operations(self):
        """BB操作統計"""
        
    def track_frame_switches(self):
        """フレーム切り替え統計"""
        
    def track_tracking_accuracy(self):
        """追跡精度統計"""
```

## ✅ Agent2完了条件

### 機能完了チェック
- [ ] AnnotationService（BB作成・削除・更新）
- [ ] TrackingService（IOU追跡・ID継承）
- [ ] ProjectService（プロジェクト管理）
- [ ] WorkflowService（ワークフロー制御）

### 性能完了チェック
- [ ] ビジネスロジック処理10ms以下
- [ ] ワークフロー制御5ms以下
- [ ] 操作検証1ms以下
- [ ] バッチ処理効率最適化

### テスト完了チェック
- [ ] 単体テスト100%通過
- [ ] 統合テスト100%通過
- [ ] 性能テスト100%通過
- [ ] ワークフローテスト100%通過

---

**Agent2 Applicationは、UI操作とドメインロジックを橋渡しする要です。効率的なワークフロー制御により、ユーザーの直感的操作をビジネス価値に変換します。**