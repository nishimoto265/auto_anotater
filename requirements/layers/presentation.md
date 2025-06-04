# Agent1: Presentation Layer 詳細仕様書（UI Agent）

## 🎯 Agent1 Presentation の使命
**PyQt6高速UI・BB描画・ユーザー操作** - 50ms以下レスポンス実現

## 📋 Agent1開始時の必須確認項目

### 開発開始前チェックリスト
- [ ] CLAUDE.md読了（Agent1責任範囲確認）
- [ ] requirement.yaml確認（UI要件理解）
- [ ] config/performance_targets.yaml確認（UI性能目標）
- [ ] config/layer_interfaces.yaml確認（Application層連携）
- [ ] tests/requirements/unit/presentation-unit-tests.md確認（テスト要件）

### Agent1専門領域
```
責任範囲: PyQt6 UI・ユーザー操作・BB描画・レスポンス性能
技術領域: PyQt6、QPainter、QGraphicsView、OpenGL、イベント処理
実装場所: src/presentation/
テスト場所: tests/unit/test_presentation/
```

## 🏗️ 実装すべきコンポーネント詳細

### 1. main_window/ - メインウィンドウ（レイアウト管理）
```
src/presentation/main_window/
├── __init__.py
├── main_window.py         # メインウィンドウクラス
├── layout_manager.py      # 70%:30%レイアウト管理
└── window_config.py       # ウィンドウ設定・状態管理
```

#### main_window.py 仕様
```python
class MainWindow(QMainWindow):
    """
    メインアプリケーションウィンドウ
    
    レイアウト:
    - 左70%: フレーム表示・BBキャンバス
    - 右30%: 操作パネル群
    
    性能要件:
    - 起動時間: 3秒以下
    - ウィンドウリサイズ: 100ms以下
    - パネル切り替え: 10ms以下
    """
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_shortcuts()
        self.connect_signals()
        
    def setup_ui(self):
        """UI初期化（70%:30%分割）"""
        
    def setup_shortcuts(self):
        """ショートカットキー設定（A/D/W/S/Ctrl+Z）"""
        
    def resizeEvent(self, event):
        """ウィンドウリサイズ処理（100ms以下）"""
```

#### layout_manager.py 仕様
```python
class LayoutManager:
    """
    レイアウト管理（70%:30%分割最適化）
    
    性能要件:
    - レイアウト更新: 10ms以下
    - サイズ計算: 1ms以下
    - 描画領域最適化: リアルタイム
    """
    
    def update_layout(self, window_size: QSize):
        """レイアウト更新（10ms以下必達）"""
        
    def calculate_canvas_size(self) -> QSize:
        """キャンバスサイズ計算（1ms以下）"""
        
    def calculate_panel_size(self) -> QSize:
        """パネルサイズ計算（1ms以下）"""
```

### 2. bb_canvas/ - BBキャンバス（最重要描画）
```
src/presentation/bb_canvas/
├── __init__.py
├── canvas_widget.py       # メインキャンバスウィジェット
├── bb_renderer.py         # BB描画エンジン
├── mouse_handler.py       # マウス操作処理
└── zoom_controller.py     # ズーム・パン制御
```

#### canvas_widget.py 仕様
```python
class BBCanvas(QGraphicsView):
    """
    バウンディングボックス描画キャンバス
    
    性能要件:
    - フレーム表示更新: 50ms以下（Cache連携）
    - BB描画更新: 16ms以下（60fps維持）
    - マウス応答: 5ms以下
    - ズーム操作: 100ms以下
    """
    
    def __init__(self):
        super().__init__()
        self.setup_graphics_view()
        self.setup_mouse_tracking()
        self.bb_renderer = BBRenderer()
        
    def display_frame(self, frame_data: FrameData):
        """
        フレーム表示（50ms以下必達）
        Cache Agentから受信したフレームを表示
        """
        
    def update_bounding_boxes(self, bb_list: List[BBEntity]):
        """
        BB描画更新（16ms以下必達）
        差分描画で性能最適化
        """
        
    def mousePressEvent(self, event):
        """マウス押下処理（5ms以下）"""
        
    def mouseMoveEvent(self, event):
        """マウスドラッグ処理（5ms以下）"""
```

#### bb_renderer.py 仕様
```python
class BBRenderer:
    """
    高速BB描画エンジン
    
    最適化手法:
    - OpenGL GPU描画活用
    - 差分描画（dirty rectangle）
    - オブジェクトプール活用
    - 色マッピングキャッシュ
    """
    
    def __init__(self, use_opengl: bool = True):
        self.use_opengl = use_opengl
        self.bb_pool = ObjectPool(BBRect, pool_size=100)
        self.color_cache = {}
        
    def render_bbs(self, bb_list: List[BBEntity], 
                   update_mode: str = "differential") -> int:
        """
        BB一括描画（16ms以下必達）
        
        Args:
            bb_list: 描画対象BBリスト
            update_mode: full/differential
            
        Returns:
            int: 描画時間（ms）
        """
        
    def render_single_bb(self, bb: BBEntity) -> None:
        """単一BB描画（1ms以下）"""
        
    def clear_canvas(self):
        """キャンバスクリア（5ms以下）"""
```

### 3. control_panels/ - 操作パネル群
```
src/presentation/control_panels/
├── __init__.py
├── id_panel.py            # 個体ID選択パネル
├── action_panel.py        # 行動選択パネル
├── bb_list_panel.py       # BB一覧表示パネル
├── file_list_panel.py     # ファイル一覧パネル
└── navigation_panel.py    # ナビゲーションパネル
```

#### id_panel.py 仕様
```python
class IDPanel(QWidget):
    """
    個体ID選択パネル（0-15、色分け表示）
    
    性能要件:
    - ID切り替え: 1ms以下
    - 色更新: 1ms以下
    - 状態表示: リアルタイム
    """
    
    def __init__(self):
        super().__init__()
        self.setup_id_buttons()  # 16個のIDボタン
        self.setup_color_mapping()
        
    def select_id(self, id_number: int):
        """ID選択（1ms以下必達）"""
        
    def update_id_colors(self, color_mapping: Dict[int, str]):
        """色マッピング更新（1ms以下）"""
```

#### bb_list_panel.py 仕様
```python
class BBListPanel(QTableWidget):
    """
    BB一覧表示・編集パネル
    
    性能要件:
    - リスト更新: 10ms以下
    - 項目選択: 1ms以下
    - 編集操作: 5ms以下
    """
    
    def update_bb_list(self, bb_list: List[BBEntity]):
        """BB一覧更新（10ms以下必達）"""
        
    def select_bb(self, bb_id: str):
        """BB選択（1ms以下）"""
        
    def edit_bb_properties(self, bb_id: str, properties: dict):
        """BBプロパティ編集（5ms以下）"""
```

### 4. shortcuts/ - ショートカット処理
```
src/presentation/shortcuts/
├── __init__.py
├── keyboard_handler.py    # キーボードイベント処理
├── shortcut_manager.py    # ショートカット管理
└── event_processor.py     # イベント処理最適化
```

#### keyboard_handler.py 仕様
```python
class KeyboardHandler:
    """
    キーボードショートカット処理
    
    性能要件:
    - キー検知: 1ms以下
    - 処理実行: 用途別最適化
    - イベント伝播: 最小遅延
    """
    
    # 必須ショートカット
    SHORTCUTS = {
        'A': 'previous_frame',      # 前フレーム（50ms以下）
        'D': 'next_frame',          # 次フレーム（50ms以下）  
        'W': 'create_bb_mode',      # BB作成モード（1ms以下）
        'S': 'delete_bb',           # BB削除（1ms以下）
        'Ctrl+Z': 'undo',           # 元に戻す（10ms以下）
    }
    
    def handle_key_press(self, key: str) -> bool:
        """
        キー処理（1ms以下必達）
        
        Returns:
            bool: 処理成功フラグ
        """
        
    def register_shortcut(self, key: str, action: str, handler: Callable):
        """ショートカット登録"""
```

## ⚡ パフォーマンス要件詳細

### 描画性能目標
```yaml
bb_rendering:
  target: "16ms以下"
  breakdown:
    bb_rect_drawing: "8ms以下"
    color_mapping: "3ms以下"
    overlay_composition: "3ms以下"
    screen_update: "2ms以下"
  optimization:
    - "OpenGL GPU描画"
    - "差分描画（dirty rectangle）"
    - "BBオブジェクトプール"
    
frame_display:
  target: "50ms以下（Cache連携）"
  measurement: "Cache→表示完了"
  dependency: "Cache Agent性能"
  
user_interaction:
  keyboard_response: "1ms以下"
  mouse_response: "5ms以下"
  zoom_operation: "100ms以下"
  panel_update: "10ms以下"
```

### UI応答性最適化
```python
# 60fps描画維持
@frame_rate_limit(60)
def update_display(self):
    """60fps制限付き表示更新"""
    
# 差分描画最適化
class DifferentialRenderer:
    def __init__(self):
        self.dirty_rects = []
        self.last_state = None
        
    def mark_dirty(self, rect: QRect):
        """変更領域マーク"""
        
    def render_dirty_areas(self):
        """変更領域のみ再描画（8ms以下）"""
```

## 🔗 他Agent連携インターフェース

### Application層との連携
```python
# UI操作→ビジネスロジック呼び出し
class UIToApplicationBridge:
    
    def create_bb_request(self, x: float, y: float, 
                         w: float, h: float, id: int, action: int):
        """BB作成要求（Application層）"""
        
    def delete_bb_request(self, bb_id: str):
        """BB削除要求（Application層）"""
        
    def frame_change_request(self, frame_id: str):
        """フレーム切り替え要求（Application層）"""
```

### Cache層との連携（重要）
```python
# 高速フレーム表示
class PresentationCacheInterface:
    
    def request_frame_display(self, frame_id: str) -> FrameData:
        """
        フレーム表示要求（50ms以下）
        Cache Agentから高速取得
        """
        
    def prefetch_display_frames(self, frame_ids: List[str]):
        """表示用フレーム先読み要求"""
```

## 🧪 テスト要件（TDD必須）

### 単体テスト必須項目
```python
# tests/unit/test_presentation/test_canvas_widget.py
class TestBBCanvas:
    def test_frame_display_50ms(self):
        """フレーム表示50ms以下確認"""
        
    def test_bb_rendering_16ms(self):
        """BB描画16ms以下確認"""
        
    def test_mouse_response_5ms(self):
        """マウス応答5ms以下確認"""
        
    def test_zoom_operation_100ms(self):
        """ズーム操作100ms以下確認"""

# tests/unit/test_presentation/test_keyboard_handler.py
class TestKeyboardHandler:
    def test_key_response_1ms(self):
        """キー応答1ms以下確認"""
        
    def test_all_shortcuts(self):
        """全ショートカット動作確認"""
```

### UI統合テスト必須項目
```python
# tests/integration/test_ui_integration.py
class TestUIIntegration:
    def test_application_layer_communication(self):
        """Application層連携確認"""
        
    def test_cache_layer_communication(self):
        """Cache層連携確認"""
        
    def test_complete_ui_workflow(self):
        """完全UIワークフロー確認"""
```

## 🛠️ 実装ガイドライン

### 必須技術スタック
```python
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtOpenGL import *     # OpenGL描画
import numpy as np               # 高速数値計算
import time                     # 性能測定
from typing import List, Dict, Optional, Callable
```

### OpenGL最適化実装
```python
class OpenGLCanvas(QOpenGLWidget):
    """OpenGL活用高速描画キャンバス"""
    
    def initializeGL(self):
        """OpenGL初期化"""
        
    def paintGL(self):
        """OpenGL描画（16ms以下）"""
        
    def resizeGL(self, width: int, height: int):
        """OpenGLリサイズ"""
```

### オブジェクトプール最適化
```python
class ObjectPool:
    """描画オブジェクトプール（メモリ効率最適化）"""
    
    def __init__(self, object_class, pool_size: int = 100):
        self.pool = [object_class() for _ in range(pool_size)]
        self.available = deque(self.pool)
        self.in_use = set()
        
    def get(self):
        """オブジェクト取得"""
        
    def release(self, obj):
        """オブジェクト返却"""
```

## 📊 性能監視・プロファイリング

### 描画性能測定
```python
class RenderingProfiler:
    """描画性能プロファイラー"""
    
    def measure_bb_rendering(self, bb_count: int) -> float:
        """BB描画時間測定"""
        
    def measure_frame_display(self) -> float:
        """フレーム表示時間測定"""
        
    def generate_performance_report(self) -> dict:
        """性能レポート生成"""
```

### リアルタイムFPS監視
```python
class FPSMonitor:
    """リアルタイムFPS監視"""
    
    def __init__(self):
        self.frame_times = deque(maxlen=60)
        
    def record_frame(self):
        """フレーム時間記録"""
        
    def get_current_fps(self) -> float:
        """現在FPS取得"""
```

## ✅ Agent1完了条件

### 機能完了チェック
- [ ] PyQt6メインウィンドウ（70%:30%分割）
- [ ] BBキャンバス（ドラッグ・ズーム・描画）
- [ ] 操作パネル（ID・行動・一覧）
- [ ] ショートカット（A/D/W/S/Ctrl+Z等）

### 性能完了チェック
- [ ] **フレーム表示50ms以下（Cache連携）**
- [ ] BB描画16ms以下
- [ ] キーボード応答1ms以下
- [ ] マウス応答5ms以下
- [ ] ズーム操作100ms以下

### テスト完了チェック
- [ ] UI単体テスト100%通過
- [ ] 操作性テスト（全ショートカット）
- [ ] 描画性能テスト（16ms確認）
- [ ] Application・Cache層連携テスト

---

**Agent1 Presentationは、ユーザー体験の要です。Cache Agentとの連携によりフレーム切り替え50ms以下を実現し、直感的で高速な動物行動アノテーション作業を可能にします。**