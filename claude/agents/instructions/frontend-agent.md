# Frontend Agent 指示書

## 役割・責務
PyQt6/PySide6によるユーザーインターフェース実装を担当する専門Agent。高速・直感的なUIの提供とユーザーエクスペリエンス最適化。

## 主要タスク

### 1. UI実装
- **メインウィンドウ**: レイアウト・パネル配置
- **フレームビューア**: 画像表示・ズーム・パン機能
- **BBエディタ**: マウス操作によるBB編集
- **コントロールパネル**: ID選択・行動選択・ナビゲーション

### 2. UX最適化
- **応答性**: 16ms以下でのUI描画更新
- **操作性**: 直感的なマウス・キーボード操作
- **視認性**: 白黒モダンデザインの実装
- **アクセシビリティ**: キーボードショートカット

### 3. パフォーマンス最適化
- **描画効率**: 差分更新による高速描画
- **メモリ効率**: UI リソースの効率的管理
- **イベント処理**: 非同期イベント処理

## 実装方針

### UI アーキテクチャ
```python
# フロントエンド構成
claude/implementation/src/frontend/
├── components/           # UIコンポーネント
│   ├── main_window.py   # メインウィンドウ
│   ├── frame_viewer.py  # フレーム表示エリア
│   ├── bbox_overlay.py  # BB描画オーバーレイ
│   ├── control_panel.py # 右側制御パネル
│   ├── navigation.py    # 下部ナビゲーション
│   └── dialogs/         # ダイアログコンポーネント
├── pages/               # 画面・ページ
│   ├── startup_page.py  # 起動選択画面
│   ├── main_page.py     # メインアノテーション画面
│   └── settings_page.py # 設定画面
├── services/            # UIサービス
│   ├── ui_state.py      # UI状態管理
│   ├── event_bus.py     # イベント管理
│   ├── theme_manager.py # テーマ・スタイル管理
│   └── shortcut_manager.py # ショートカット管理
└── styles/              # スタイルシート
    ├── main.qss         # メインスタイル
    ├── dark_theme.qss   # ダークテーマ
    └── light_theme.qss  # ライトテーマ
```

### 開発フロー
```bash
# 1. ワークツリーでの UI開発
cd workspace/worktrees/ui-feature
# implementation/src/frontend/ で実装

# 2. リアルタイムUI確認
python implementation/src/frontend/main.py --dev-mode

# 3. UI テスト実行
pytest implementation/src/frontend/tests/

# 4. backend-agentとの統合テスト
pytest tests/integration/ui_backend_integration/
```

## 技術仕様

### 1. メインウィンドウ実装
```python
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                            QVBoxLayout, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut

class MainWindow(QMainWindow):
    """メインアプリケーションウィンドウ"""
    
    # シグナル定義
    frame_changed = pyqtSignal(int)  # フレーム変更シグナル
    bbox_created = pyqtSignal(object)  # BB作成シグナル
    bbox_modified = pyqtSignal(str, object)  # BB変更シグナル
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("オートアノテーションツール")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_style()
        
    def setup_ui(self):
        """UIレイアウト構築"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト（水平分割）
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側：フレーム表示エリア
        self.frame_viewer = FrameViewer()
        frame_widget = self.create_frame_widget()
        
        # 右側：制御パネル
        self.control_panel = ControlPanel()
        
        # 下部：ナビゲーション
        self.navigation = Navigation()
        
        # レイアウト組み立て
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(frame_widget, stretch=1)
        left_layout.addWidget(self.navigation)
        
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(self.control_panel)
        main_splitter.setStretchFactor(0, 3)  # 左側3:右側1
        main_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(main_splitter)
        
    def setup_shortcuts(self):
        """ショートカット設定"""
        shortcuts = {
            'A': self.prev_frame,
            'D': self.next_frame,
            'W': self.toggle_bbox_mode,
            'S': self.delete_selected_bbox,
            'Ctrl+Z': self.undo_action,
            'Shift+A': self.prev_change_frame,
            'Shift+D': self.next_change_frame,
        }
        
        for key, method in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(method)
```

### 2. フレームビューア実装
```python
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush
import numpy as np

class FrameViewer(QGraphicsView):
    """高速フレーム表示ビューア（50ms以下切り替え）"""
    
    bbox_created = pyqtSignal(object)
    bbox_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 描画最適化設定
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing)
        
        # 状態管理
        self.current_frame = None
        self.bboxes = []
        self.selected_bbox = None
        self.drawing_bbox = False
        self.bbox_start_point = None
        
        # 性能測定用
        self.frame_switch_timer = QTimer()
        self.frame_switch_timer.setSingleShot(True)
        
    def display_frame(self, frame_data: np.ndarray, frame_index: int):
        """高速フレーム表示（50ms以下目標）"""
        start_time = time.time()
        
        # 前のフレームをクリア（差分更新）
        self.scene.clear()
        
        # 画像をQPixmapに変換
        height, width, channel = frame_data.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame_data.data, width, height, 
                        bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # シーンに追加
        self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(pixmap.rect())
        
        # BBを再描画
        self.redraw_bboxes()
        
        # 性能測定
        elapsed = (time.time() - start_time) * 1000
        if elapsed > 50:  # 50ms超過時は警告
            print(f"Warning: Frame display took {elapsed:.1f}ms")
            
    def redraw_bboxes(self):
        """BB再描画（16ms以下目標）"""
        start_time = time.time()
        
        for bbox in self.bboxes:
            self.draw_bbox(bbox)
            
        elapsed = (time.time() - start_time) * 1000
        if elapsed > 16:
            print(f"Warning: BBox redraw took {elapsed:.1f}ms")
            
    def draw_bbox(self, bbox):
        """単一BB描画"""
        # 座標変換（YOLO → ピクセル）
        scene_rect = self.scene.sceneRect()
        x = bbox.x * scene_rect.width() - (bbox.w * scene_rect.width() / 2)
        y = bbox.y * scene_rect.height() - (bbox.h * scene_rect.height() / 2)
        w = bbox.w * scene_rect.width()
        h = bbox.h * scene_rect.height()
        
        # 色設定（ID別）
        color = self.get_bbox_color(bbox.individual_id)
        pen = QPen(color, 2)
        
        # 矩形描画
        rect_item = self.scene.addRect(x, y, w, h, pen)
        rect_item.setData(0, bbox.id)  # BB IDを保存
        
        # ラベル描画
        if bbox.individual_id is not None:
            text = f"ID:{bbox.individual_id}"
            if bbox.action_id is not None:
                text += f" {bbox.action_id}"
            text_item = self.scene.addText(text)
            text_item.setPos(x, y - 20)
            
    def mousePressEvent(self, event):
        """マウスプレス（BB作成開始）"""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            
            # 既存BBの選択チェック
            clicked_item = self.scene.itemAt(scene_pos, self.transform())
            if clicked_item and clicked_item.data(0):  # BB選択
                self.select_bbox(clicked_item.data(0))
            else:  # 新規BB作成開始
                self.start_bbox_creation(scene_pos)
                
        super().mousePressEvent(event)
```

### 3. コントロールパネル実装
```python
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QButtonGroup, QCheckBox)

class ControlPanel(QWidget):
    """右側制御パネル"""
    
    individual_id_changed = pyqtSignal(int)
    action_id_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(250)
        self.setup_ui()
        
    def setup_ui(self):
        """制御パネルレイアウト"""
        layout = QVBoxLayout(self)
        
        # 現在選択中表示
        self.current_selection = QLabel("選択中: なし")
        layout.addWidget(self.current_selection)
        
        # 個体ID選択（0-15）
        layout.addWidget(QLabel("個体ID選択"))
        self.individual_buttons = self.create_id_buttons(16)
        layout.addLayout(self.individual_buttons)
        
        # 行動ID選択
        layout.addWidget(QLabel("行動選択"))
        self.action_buttons = self.create_action_buttons()
        layout.addLayout(self.action_buttons)
        
        # 現在フレームBB一覧
        layout.addWidget(QLabel("現在フレームBB"))
        self.bbox_list = self.create_bbox_list()
        layout.addWidget(self.bbox_list)
        
        # 機能ボタン
        self.create_function_buttons(layout)
        
    def create_id_buttons(self, count: int):
        """個体IDボタングループ作成"""
        layout = QVBoxLayout()
        self.id_button_group = QButtonGroup()
        
        # 2行5列でボタン配置
        for row in range((count + 4) // 5):
            row_layout = QHBoxLayout()
            for col in range(5):
                id_num = row * 5 + col
                if id_num >= count:
                    break
                    
                button = QPushButton(str(id_num))
                button.setCheckable(True)
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.get_id_color(id_num)};
                        border: 1px solid #333;
                        border-radius: 3px;
                        padding: 5px;
                    }}
                    QPushButton:checked {{
                        border: 2px solid #fff;
                        font-weight: bold;
                    }}
                """)
                
                self.id_button_group.addButton(button, id_num)
                row_layout.addWidget(button)
                
            layout.addLayout(row_layout)
            
        # シグナル接続
        self.id_button_group.idClicked.connect(self.individual_id_changed.emit)
        
        return layout
        
    def create_action_buttons(self):
        """行動選択ボタン作成"""
        layout = QVBoxLayout()
        self.action_button_group = QButtonGroup()
        
        default_actions = ["sit", "stand", "milk", "water", "food"]
        
        for i, action in enumerate(default_actions):
            button = QPushButton(action)
            button.setCheckable(True)
            self.action_button_group.addButton(button, i)
            layout.addWidget(button)
            
        # カスタム行動追加ボタン
        add_button = QPushButton("[+追加]")
        add_button.clicked.connect(self.add_custom_action)
        layout.addWidget(add_button)
        
        return layout
```

### 4. ナビゲーション実装
```python
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, 
                            QLabel, QLineEdit, QProgressBar)

class Navigation(QWidget):
    """下部ナビゲーションバー"""
    
    frame_changed = pyqtSignal(int)
    jump_to_change = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.current_frame = 0
        self.total_frames = 0
        self.setup_ui()
        
    def setup_ui(self):
        """ナビゲーションUI構築"""
        layout = QHBoxLayout(self)
        
        # フレーム移動ボタン
        self.prev_btn = QPushButton("◀")
        self.prev_btn.clicked.connect(self.prev_frame)
        layout.addWidget(self.prev_btn)
        
        # フレーム番号表示・入力
        self.frame_input = QLineEdit("001")
        self.frame_input.setFixedWidth(60)
        self.frame_input.returnPressed.connect(self.jump_to_frame)
        layout.addWidget(self.frame_input)
        
        layout.addWidget(QLabel("/"))
        
        self.total_label = QLabel("500")
        layout.addWidget(self.total_label)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.clicked.connect(self.next_frame)
        layout.addWidget(self.next_btn)
        
        # BB変化フレーム移動
        self.change_prev_btn = QPushButton("前の変化")
        self.change_prev_btn.clicked.connect(self.prev_change_frame)
        layout.addWidget(self.change_prev_btn)
        
        self.change_next_btn = QPushButton("次の変化")
        self.change_next_btn.clicked.connect(self.next_change_frame)
        layout.addWidget(self.change_next_btn)
        
        # 進捗バー
        layout.addStretch()
        layout.addWidget(QLabel("進捗:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        layout.addWidget(self.progress_bar)
        
    def update_frame(self, frame_index: int):
        """フレーム表示更新"""
        self.current_frame = frame_index
        self.frame_input.setText(f"{frame_index:03d}")
        self.progress_bar.setValue(int(frame_index / self.total_frames * 100))
```

## スタイルシート実装

### メインスタイル（白黒モダンデザイン）
```css
/* styles/main.qss */
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
}

QPushButton {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 12px;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #505050;
    border-color: #777777;
}

QPushButton:pressed {
    background-color: #353535;
    border-color: #333333;
}

QPushButton:checked {
    background-color: #0078d4;
    border-color: #106ebe;
}

QLabel {
    color: #ffffff;
    font-weight: 500;
}

QLineEdit {
    background-color: #333333;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px;
    color: #ffffff;
}

QProgressBar {
    border: 1px solid #555555;
    border-radius: 3px;
    background-color: #333333;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 2px;
}
```

## パフォーマンス最適化

### 描画最適化
```python
class OptimizedPainter:
    """最適化された描画処理"""
    
    @staticmethod
    def fast_bbox_draw(scene, bboxes, viewport_rect):
        """視界内BBのみ描画（カリング）"""
        visible_bboxes = []
        for bbox in bboxes:
            bbox_rect = bbox.get_scene_rect()
            if viewport_rect.intersects(bbox_rect):
                visible_bboxes.append(bbox)
                
        return visible_bboxes
        
    @staticmethod
    def batch_update(scene, items):
        """バッチ更新で描画効率化"""
        scene.blockSignals(True)
        try:
            for item in items:
                scene.addItem(item)
        finally:
            scene.blockSignals(False)
            scene.update()
```

## テスト要件

### UIテスト
```python
# tests/test_ui_components.py
import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

def test_frame_viewer_performance(qtbot):
    """フレーム表示性能テスト"""
    viewer = FrameViewer()
    qtbot.addWidget(viewer)
    
    # 50ms以下でのフレーム切り替えテスト
    start_time = time.time()
    viewer.display_frame(test_frame_data, 100)
    elapsed = (time.time() - start_time) * 1000
    assert elapsed < 50

def test_bbox_creation(qtbot):
    """BB作成テスト"""
    viewer = FrameViewer()
    qtbot.addWidget(viewer)
    
    # マウスドラッグでBB作成
    qtbot.mousePress(viewer, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
    qtbot.mouseMove(viewer, QPoint(200, 200))
    qtbot.mouseRelease(viewer, Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
    
    assert len(viewer.bboxes) == 1
```

## チェックリスト

### UI実装完了チェック
- [ ] メインウィンドウレイアウト完了
- [ ] フレームビューア実装完了
- [ ] BBエディタ実装完了
- [ ] コントロールパネル実装完了
- [ ] ナビゲーション実装完了
- [ ] ショートカット実装完了
- [ ] スタイルシート適用完了
- [ ] 16ms以下でのBB描画達成
- [ ] 50ms以下でのフレーム切り替え達成