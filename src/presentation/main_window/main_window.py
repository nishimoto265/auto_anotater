"""
Agent1 Presentation - MainWindow
PyQt6 メインウィンドウ・70%:30%レイアウト・高速レスポンス

性能要件:
- 起動時間: 3秒以下
- ウィンドウリサイズ: 100ms以下
- パネル切り替え: 10ms以下
"""

import os
import time
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QFrame, QApplication, QMenuBar, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QKeySequence, QAction

from .layout_manager import LayoutManager
from .window_config import WindowConfig
from ..bb_canvas.canvas_widget import BBCanvas
from ..control_panels.id_panel import IDPanel
from ..control_panels.action_panel import ActionPanel
from ..control_panels.bb_list_panel import BBListPanel
from ..control_panels.file_list_panel import FileListPanel
from ..control_panels.color_mode_panel import ColorModePanel
from ..control_panels.modify_panel import ModifyPanel
from ..control_panels.continuous_mode_panel import ContinuousModePanel
from ..shortcuts.keyboard_handler import KeyboardHandler

# 追跡機能用インポート
from utils.simple_tracker import SimpleTracker


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
    
    # シグナル定義
    frame_change_requested = pyqtSignal(str)  # フレーム切り替え要求
    bb_creation_requested = pyqtSignal(float, float, float, float, int, int)  # BB作成要求
    bb_deletion_requested = pyqtSignal(str)  # BB削除要求
    
    def __init__(self, parent: Optional[QWidget] = None, project_info: Optional[tuple] = None):
        super().__init__(parent)
        
        # 性能測定用
        self.startup_timer = time.perf_counter()
        
        # プロジェクト情報
        self.project_info = project_info
        self.project_type = project_info[0] if project_info else None
        self.project_path = project_info[1] if project_info else None
        self.project_config = project_info[2] if project_info else {}
        
        # 設定管理
        self.config = WindowConfig()
        self.layout_manager = LayoutManager()
        
        # UI初期化
        self.setup_ui()
        self.setup_shortcuts()
        self.connect_signals()
        
        # 初期フレーム設定
        self.current_frame = 0
        
        # アノテーション管理
        self.current_annotations = []  # 現在フレームのBBリスト
        self.annotation_output_dir = None  # アノテーション保存先
        
        # 追跡システム初期化
        self.tracker = SimpleTracker(iou_threshold=0.5)
            
        # 前フレームのBB記録（追跡用）
        self.previous_frame_bbs = []
        
        # プロジェクト初期化
        if self.project_info:
            self.initialize_project()
        
        # 初期化完了時間記録
        startup_time = (time.perf_counter() - self.startup_timer) * 1000
        print(f"MainWindow startup time: {startup_time:.2f}ms")
        
        # プロジェクト情報をタイトルに表示
        if self.project_config.get('name'):
            self.setWindowTitle(f"Fast Auto-Annotation System - {self.project_config['name']}")
        
    def setup_ui(self):
        """UI初期化（70%:30%分割）"""
        start_time = time.perf_counter()
        
        # メインウィンドウ設定
        self.setWindowTitle("Fast Auto-Annotation System - Agent1 Presentation")
        self.setMinimumSize(1200, 800)
        self.resize(1920, 1080)  # デフォルトサイズ
        
        # メニューバー作成
        self.create_menu_bar()
        
        # ステータスバー作成
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Frame: 0/0")
        
        # 中央ウィジェット作成
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインスプリッター（70%:30%分割）
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側: キャンバス領域（70%）
        self.canvas_frame = self.create_canvas_frame()
        
        # 右側: 操作パネル領域（30%）
        self.panel_frame = self.create_panel_frame()
        
        # スプリッター設定
        self.main_splitter.addWidget(self.canvas_frame)
        self.main_splitter.addWidget(self.panel_frame)
        self.main_splitter.setSizes([1344, 576])  # 70%:30% for 1920px width
        self.main_splitter.setStretchFactor(0, 7)  # キャンバス優先
        self.main_splitter.setStretchFactor(1, 3)
        
        # レイアウト設定
        layout = QHBoxLayout(central_widget)
        layout.addWidget(self.main_splitter)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 初期化時間記録
        init_time = (time.perf_counter() - start_time) * 1000
        print(f"UI setup time: {init_time:.2f}ms")
        
    def create_canvas_frame(self) -> QFrame:
        """キャンバスフレーム作成"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setLineWidth(1)
        
        # BBキャンバス作成
        self.bb_canvas = BBCanvas()
        
        # レイアウト
        layout = QVBoxLayout(frame)
        layout.addWidget(self.bb_canvas)
        layout.setContentsMargins(2, 2, 2, 2)
        
        return frame
        
    def create_panel_frame(self) -> QFrame:
        """操作パネルフレーム作成"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setLineWidth(1)
        frame.setFixedWidth(400)  # 固定幅
        
        # 操作パネル作成
        self.id_panel = IDPanel()
        self.action_panel = ActionPanel()
        
        # 新しいパネルを追加
        from ..control_panels.color_mode_panel import ColorModePanel
        from ..control_panels.modify_panel import ModifyPanel
        from ..control_panels.continuous_mode_panel import ContinuousModePanel
        
        self.color_mode_panel = ColorModePanel()
        self.modify_panel = ModifyPanel()
        self.continuous_mode_panel = ContinuousModePanel()
        
        self.bb_list_panel = BBListPanel()
        self.file_list_panel = FileListPanel()
        
        # スクロールエリアを作成してパネルを収納
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # パネルを追加
        scroll_layout.addWidget(self.id_panel)
        scroll_layout.addWidget(self.action_panel)
        scroll_layout.addWidget(self.color_mode_panel)
        scroll_layout.addWidget(self.modify_panel)
        scroll_layout.addWidget(self.continuous_mode_panel)
        scroll_layout.addWidget(self.bb_list_panel)
        scroll_layout.addWidget(self.file_list_panel)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        # メインレイアウト
        layout = QVBoxLayout(frame)
        layout.addWidget(scroll_area)
        layout.setContentsMargins(5, 5, 5, 5)
        
        return frame
        
    def create_menu_bar(self):
        """メニューバー作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open Project', self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        file_menu.addAction(open_action)
        
        save_action = QAction('&Save', self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu('&View')
        
        zoom_in_action = QAction('Zoom &In', self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom &Out', self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        view_menu.addAction(zoom_out_action)
        
        reset_view_action = QAction('&Reset View', self)
        reset_view_action.setShortcut('Ctrl+0')
        view_menu.addAction(reset_view_action)
        
    def setup_shortcuts(self):
        """ショートカットキー設定（A/D/W/S/Ctrl+Z）"""
        self.keyboard_handler = KeyboardHandler(self)
        
        # 必須ショートカット登録
        shortcuts = {
            'A': self.previous_frame,
            'D': self.next_frame,
            'W': self.toggle_bb_creation_mode,
            'S': self.delete_selected_bb,
            'Ctrl+Z': self.undo_action,
            'Escape': self.cancel_current_action,
            # 新機能用ショートカット
            'Shift+W': self.toggle_continuous_mode,
        }
        
        # ID変更用ショートカット (Alt + 0-9, A-F)
        for i in range(10):
            shortcuts[f'Alt+{i}'] = lambda id=i: self.set_selected_bb_id_only(id)
        shortcuts['Alt+A'] = lambda: self.set_selected_bb_id_only(10)
        shortcuts['Alt+B'] = lambda: self.set_selected_bb_id_only(11)
        shortcuts['Alt+C'] = lambda: self.set_selected_bb_id_only(12)
        shortcuts['Alt+D'] = lambda: self.set_selected_bb_id_only(13)
        shortcuts['Alt+E'] = lambda: self.set_selected_bb_id_only(14)
        shortcuts['Alt+F'] = lambda: self.set_selected_bb_id_only(15)
        
        # 行動変更用ショートカット (Shift + 1-5)
        for i in range(5):
            shortcuts[f'Shift+{i+1}'] = lambda action=i: self.set_selected_bb_action_only(action)
        
        for key, handler in shortcuts.items():
            self.keyboard_handler.register_shortcut(key, handler, handler.__name__ if hasattr(handler, '__name__') else key)
            
    def connect_signals(self):
        """シグナル・スロット接続"""
        # キャンバスからの信号
        self.bb_canvas.bb_created.connect(self.on_bb_created)
        self.bb_canvas.bb_selected.connect(self.on_bb_selected)
        self.bb_canvas.zoom_changed.connect(self.on_zoom_changed)
        
        # 操作パネルからの信号
        self.id_panel.id_selected.connect(self.on_id_selected)
        self.action_panel.action_selected.connect(self.on_action_selected)
        self.bb_list_panel.bb_selected.connect(self.on_bb_list_selected)
        self.file_list_panel.frame_selected.connect(self.on_frame_selected)
        
        # 新しいパネルからの信号
        self.color_mode_panel.color_mode_changed.connect(self.on_color_mode_changed)
        self.modify_panel.apply_changes.connect(self.on_apply_changes)
        self.continuous_mode_panel.continuous_mode_changed.connect(self.on_continuous_mode_changed)
        self.continuous_mode_panel.copy_bb_to_range.connect(self.on_copy_bb_to_range)
        self.continuous_mode_panel.track_forward.connect(self.on_track_forward)
        
    # ==================== ショートカットハンドラー ====================
    
    def previous_frame(self):
        """前フレーム（Aキー・50ms以下必達）"""
        start_time = time.perf_counter()
        
        current_frame = self.get_current_frame_id()
        if current_frame > 0:
            new_frame_id = f"frame_{current_frame - 1:06d}"
            self.current_frame = current_frame - 1
            # ファイルリストパネルも更新
            if hasattr(self, 'file_list_panel'):
                self.file_list_panel.select_frame(new_frame_id)
            # 直接フレーム選択処理を実行
            self.on_frame_selected(new_frame_id)
            self.frame_change_requested.emit(new_frame_id)
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 50:
            print(f"WARNING: Previous frame took {elapsed:.2f}ms (>50ms)")
            
    def next_frame(self):
        """次フレーム（Dキー・50ms以下必達）"""
        start_time = time.perf_counter()
        
        current_frame = self.get_current_frame_id()
        max_frame = self.get_max_frame_id()
        if current_frame < max_frame:
            new_frame_id = f"frame_{current_frame + 1:06d}"
            self.current_frame = current_frame + 1
            # ファイルリストパネルも更新
            if hasattr(self, 'file_list_panel'):
                self.file_list_panel.select_frame(new_frame_id)
            # 直接フレーム選択処理を実行
            self.on_frame_selected(new_frame_id)
            self.frame_change_requested.emit(new_frame_id)
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 50:
            print(f"WARNING: Next frame took {elapsed:.2f}ms (>50ms)")
            
    def toggle_bb_creation_mode(self):
        """BB作成モード切り替え（Wキー・1ms以下）"""
        start_time = time.perf_counter()
        
        print("BB creation mode toggle triggered")
        self.bb_canvas.toggle_creation_mode()
        creation_mode = getattr(self.bb_canvas, 'creation_mode', False)
        print(f"BB creation mode is now: {creation_mode}")
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: BB creation mode toggle took {elapsed:.2f}ms (>1ms)")
            
    def delete_selected_bb(self):
        """選択BB削除（Sキー・1ms以下）"""
        start_time = time.perf_counter()
        
        print("BB deletion triggered")
        selected_bb = self.bb_canvas.get_selected_bb()
        print(f"Selected BB: {selected_bb}")
        if selected_bb:
            print(f"Deleting BB: {selected_bb.id}")
            # current_annotationsから削除
            self.current_annotations = [bb for bb in self.current_annotations if bb.get('id') != selected_bb.id]
            # BBキャンバスを更新
            self.bb_canvas.update_bounding_boxes(self.current_annotations)
            # BB一覧も更新
            self.update_bb_list_panel()
            # ファイルに保存
            self.save_current_annotations()
            self.bb_deletion_requested.emit(selected_bb.id)
        else:
            print("No BB selected for deletion")
            # 代替案: 最新のBBを削除
            if self.current_annotations:
                deleted_bb = self.current_annotations.pop()
                print(f"Deleted latest BB: {deleted_bb['id']}")
                # BBキャンバスを更新
                self.bb_canvas.update_bounding_boxes(self.current_annotations)
                # BB一覧も更新
                self.update_bb_list_panel()
                # ファイルに保存
                self.save_current_annotations()
            else:
                print("No BBs to delete")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: BB deletion took {elapsed:.2f}ms (>1ms)")
            
    def undo_action(self):
        """元に戻す（Ctrl+Z・10ms以下）"""
        start_time = time.perf_counter()
        
        # TODO: Implement undo functionality
        print("Undo action triggered")
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 10:
            print(f"WARNING: Undo action took {elapsed:.2f}ms (>10ms)")
            
    def cancel_current_action(self):
        """現在のアクションキャンセル（Escape）"""
        self.bb_canvas.cancel_current_action()
        
    def toggle_continuous_mode(self):
        """連続モード切り替え（Shift+W）"""
        if hasattr(self, 'continuous_mode_panel'):
            self.continuous_mode_panel.toggle_continuous_mode()
            
    def set_selected_bb_id_only(self, individual_id: int):
        """選択BBのIDのみ変更（Alt+0-9,A-F）"""
        selected_bb = self.bb_canvas.get_selected_bb()
        if selected_bb:
            # current_annotationsを更新
            for bb in self.current_annotations:
                if bb['id'] == selected_bb.id:
                    bb['individual_id'] = individual_id
                    break
                    
            # UI更新
            self.bb_canvas.update_bounding_boxes(self.current_annotations)
            self.update_bb_list_panel()
            self.save_current_annotations()
            
            # IDパネルも更新
            if hasattr(self, 'id_panel'):
                self.id_panel.set_selected_id(individual_id)
                
            self.status_bar.showMessage(f"IDを {individual_id} に変更しました", 2000)
        else:
            # 選択されていない場合は、IDパネルの選択を変更
            if hasattr(self, 'id_panel'):
                self.id_panel.set_selected_id(individual_id)
                self.status_bar.showMessage(f"IDを {individual_id} に選択しました", 2000)
                
    def set_selected_bb_action_only(self, action_id: int):
        """選択BBの行動のみ変更（Shift+1-5）"""
        selected_bb = self.bb_canvas.get_selected_bb()
        if selected_bb:
            # current_annotationsを更新
            for bb in self.current_annotations:
                if bb['id'] == selected_bb.id:
                    bb['action_id'] = action_id
                    break
                    
            # UI更新
            self.bb_canvas.update_bounding_boxes(self.current_annotations)
            self.update_bb_list_panel()
            self.save_current_annotations()
            
            # 行動パネルも更新
            if hasattr(self, 'action_panel'):
                self.action_panel.set_selected_action(action_id)
                
            action_names = {0: "Sit", 1: "Stand", 2: "Milk", 3: "Water", 4: "Food"}
            action_name = action_names.get(action_id, "Unknown")
            self.status_bar.showMessage(f"行動を {action_name} に変更しました", 2000)
        else:
            # 選択されていない場合は、行動パネルの選択を変更
            if hasattr(self, 'action_panel'):
                self.action_panel.set_selected_action(action_id)
                action_names = {0: "Sit", 1: "Stand", 2: "Milk", 3: "Water", 4: "Food"}
                action_name = action_names.get(action_id, "Unknown")
                self.status_bar.showMessage(f"行動を {action_name} に選択しました", 2000)
        
    # ==================== イベントハンドラー ====================
    
    def on_bb_created(self, x: float, y: float, w: float, h: float):
        """BB作成時の処理"""
        try:
            current_id = self.id_panel.get_selected_id() if hasattr(self, 'id_panel') else 0
            current_action = self.action_panel.get_selected_action() if hasattr(self, 'action_panel') else 0
        except:
            current_id = 0
            current_action = 0
        
        print(f"Creating BB: x={x:.3f}, y={y:.3f}, w={w:.3f}, h={h:.3f}, id={current_id}, action={current_action}")
        
        # 新しいBBエンティティ作成
        bb_entity = {
            'id': f"bb_{len(self.current_annotations)}_{int(time.time())}",
            'x': x, 'y': y, 'w': w, 'h': h,
            'individual_id': current_id,
            'action_id': current_action,
            'confidence': 1.0
        }
        
        # 現在フレームのアノテーションに追加
        self.current_annotations.append(bb_entity)
        
        # BBキャンバスを更新
        self.bb_canvas.update_bounding_boxes(self.current_annotations)
        
        # BB一覧も更新
        self.update_bb_list_panel()
        
        # ファイルに保存
        self.save_current_annotations()
        
        # 連続モードの場合、最後のBBテンプレートを保存
        if hasattr(self, 'continuous_mode') and self.continuous_mode:
            self.last_bb_template = bb_entity.copy()
        
        self.bb_creation_requested.emit(x, y, w, h, current_id, current_action)
        
    def on_bb_selected(self, bb_id: str):
        """BB選択時の処理"""
        # bb_list_panelのselect_bbはシグナルをブロックするため循環参照は起きない
        if hasattr(self, 'bb_list_panel'):
            self.bb_list_panel.select_bb(bb_id)
        
    def on_zoom_changed(self, zoom_level: float):
        """ズーム変更時の処理"""
        self.status_bar.showMessage(f"Zoom: {zoom_level:.1f}x")
        
    def on_id_selected(self, id_number: int):
        """ID選択時の処理"""
        self.bb_canvas.set_current_id(id_number)
        
    def on_action_selected(self, action_id: int):
        """行動選択時の処理"""
        self.bb_canvas.set_current_action(action_id)
        
    def on_bb_list_selected(self, bb_id: str):
        """BB一覧選択時の処理"""
        self.bb_canvas.select_bb(bb_id)
        
    def on_frame_selected(self, frame_id: str):
        """フレーム選択時の処理"""
        # フレームIDからファイルパスを取得
        frame_path = self.get_frame_path_by_id(frame_id)
        if frame_path:
            # BBCanvasに画像を直接ロード
            if self.bb_canvas.load_frame(frame_path):
                # 現在フレーム更新（frame_idから直接計算）
                try:
                    # frame_000000 形式からインデックス抽出
                    self.current_frame = int(frame_id.split('_')[1])
                except (ValueError, IndexError):
                    # フォールバック
                    if hasattr(self, 'file_list_panel'):
                        self.current_frame = self.file_list_panel.get_current_frame_index()
                
                # 現在フレームのアノテーションを読み込み・表示
                self.load_current_annotations()
                
                # 連続モードの場合、最後のBBテンプレートから新しいBBを作成
                if hasattr(self, 'continuous_mode') and self.continuous_mode and hasattr(self, 'last_bb_template'):
                    # IOU計算用のインポート
                    from utils.iou_calculator import has_high_overlap
                    
                    # 重複チェック
                    template_bb = self.last_bb_template
                    has_overlap, max_iou = has_high_overlap(
                        template_bb, 
                        self.current_annotations,
                        template_bb['individual_id'],
                        iou_threshold=0.8
                    )
                    
                    if not has_overlap:
                        # 重複がない場合のみBBを作成（同じ位置・同じIDで）
                        new_bb = template_bb.copy()
                        new_bb['id'] = f"bb_{frame_id}_{len(self.current_annotations)}"
                        
                        self.current_annotations.append(new_bb)
                        self.save_current_annotations()
                        
                        self.status_bar.showMessage(
                            f"連続BBを作成しました (ID: {new_bb['individual_id']})", 
                            2000
                        )
                    else:
                        # 重複がある場合はスキップ
                        self.status_bar.showMessage(
                            f"既存BBとの重複のため、BB作成をスキップしました (IOU: {max_iou:.2f})", 
                            2000
                        )
                
                # 現在のフレームBBを記録（次フレームの追跡用）
                self.previous_frame_bbs = self.current_annotations.copy()
                    
                self.bb_canvas.update_bounding_boxes(self.current_annotations)
                self.update_bb_list_panel()
                    
                # ステータス更新
                annotation_count = len(self.current_annotations)
                self.update_status(f"Frame: {self.current_frame + 1}/{self.total_frames} | BBs: {annotation_count}")
            else:
                print(f"Failed to load frame: {frame_path}")
        
        self.frame_change_requested.emit(frame_id)
        
    # ==================== ユーティリティメソッド ====================
    
    def get_current_frame_id(self) -> int:
        """現在フレームID取得"""
        return getattr(self, 'current_frame', 0)
        
    def get_max_frame_id(self) -> int:
        """最大フレームID取得"""
        return getattr(self, 'total_frames', 0) - 1
        
    def get_frame_path_by_id(self, frame_id: str) -> str:
        """フレームIDからファイルパスを取得"""
        try:
            # frame_000000 形式からインデックス抽出
            frame_index = int(frame_id.split('_')[1])
            
            # frame_pathsが存在する場合はそれを使用
            if hasattr(self, 'frame_paths') and frame_index < len(self.frame_paths):
                return self.frame_paths[frame_index]
            
            # プロジェクトタイプに応じてパス構築（フォールバック）
            if self.project_type in ["video", "images"]:
                # 出力ディレクトリまたはフォールバック
                output_dir = self.project_config.get('output_directory', '')
                if output_dir and hasattr(self, 'frame_files') and frame_index < len(self.frame_files):
                    return os.path.join(output_dir, self.frame_files[frame_index])
                else:
                    # フォールバック: data/frames/
                    return f"/media/thithilab/volume/auto_anotatation/data/frames/{frame_index:06d}.jpg"
            elif self.project_type == "existing":
                # 既存プロジェクトの場合
                if hasattr(self, 'frame_files') and frame_index < len(self.frame_files):
                    return self.frame_files[frame_index]
                    
        except (ValueError, IndexError) as e:
            print(f"Error parsing frame_id {frame_id}: {e}")
            
        return ""
    
    def save_current_annotations(self):
        """現在フレームのアノテーションを保存"""
        if not self.annotation_output_dir:
            # 保存先ディレクトリを設定
            self.setup_annotation_output_dir()
            
        if not self.annotation_output_dir:
            print("No annotation output directory set")
            return
            
        frame_id = f"{self.current_frame:06d}"
        
        try:
            # TXTハンドラーを使用してYOLO形式で保存
            from persistence.file_io.txt_handler import YOLOTxtHandler, BBEntity, Coordinates
            from datetime import datetime
            
            handler = YOLOTxtHandler()
            
            # BBエンティティに変換
            bb_entities = []
            for bb_data in self.current_annotations:
                bb_entity = BBEntity(
                    id=bb_data['id'],
                    frame_id=frame_id,
                    individual_id=bb_data['individual_id'],
                    action_id=bb_data['action_id'],
                    coordinates=Coordinates(
                        x=bb_data['x'],
                        y=bb_data['y'],
                        w=bb_data['w'],
                        h=bb_data['h']
                    ),
                    confidence=bb_data['confidence'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                bb_entities.append(bb_entity)
            
            # 保存実行
            success = handler.save_annotations(frame_id, bb_entities, self.annotation_output_dir)
            if success:
                print(f"Saved {len(bb_entities)} annotations to {frame_id}.txt")
            else:
                print(f"Failed to save annotations for frame {frame_id}")
                
        except Exception as e:
            print(f"Error saving annotations: {e}")
            
    def load_current_annotations(self):
        """現在フレームのアノテーションを読み込み"""
        if not self.annotation_output_dir:
            self.current_annotations = []
            return
            
        frame_id = f"{self.current_frame:06d}"
        annotation_file = os.path.join(self.annotation_output_dir, f"{frame_id}.txt")
        
        if not os.path.exists(annotation_file):
            self.current_annotations = []
            return
            
        try:
            # YOLOファイルを読み込み
            from persistence.file_io.txt_handler import YOLOTxtHandler
            
            handler = YOLOTxtHandler()
            bb_entities = handler.load_annotations(frame_id, self.annotation_output_dir)
            
            # 内部形式に変換
            self.current_annotations = []
            for bb in bb_entities:
                bb_data = {
                    'id': bb.id,
                    'x': bb.coordinates.x,
                    'y': bb.coordinates.y,
                    'w': bb.coordinates.w,
                    'h': bb.coordinates.h,
                    'individual_id': bb.individual_id,
                    'action_id': bb.action_id,
                    'confidence': bb.confidence
                }
                self.current_annotations.append(bb_data)
                
            print(f"Loaded {len(self.current_annotations)} annotations from {frame_id}.txt")
            
        except Exception as e:
            print(f"Error loading annotations: {e}")
            self.current_annotations = []
            
    def setup_annotation_output_dir(self):
        """アノテーション保存先ディレクトリを設定"""
        from PyQt6.QtWidgets import QFileDialog
        
        # プロジェクト設定にある場合はそれを使用
        if self.project_config.get('annotation_directory'):
            self.annotation_output_dir = self.project_config['annotation_directory']
            return
            
        # デフォルト保存先: プロジェクトディレクトリ/annotations
        if hasattr(self, 'images_directory'):
            default_dir = os.path.join(os.path.dirname(self.images_directory), 'annotations')
        else:
            default_dir = os.path.join(os.getcwd(), 'annotations')
            
        # ユーザーに選択させる
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "アノテーション保存先を選択",
            default_dir
        )
        
        if selected_dir:
            self.annotation_output_dir = selected_dir
            os.makedirs(selected_dir, exist_ok=True)
            print(f"Annotation output directory set to: {selected_dir}")
        else:
            # キャンセルされた場合はデフォルトを使用
            self.annotation_output_dir = default_dir
            os.makedirs(default_dir, exist_ok=True)
            print(f"Using default annotation directory: {default_dir}")
            
    # ==================== 新機能ハンドラー ====================
    
    def on_color_mode_changed(self, mode: str):
        """色分けモード変更処理"""
        print(f"Color mode changed to: {mode}")
        
        # BBレンダラーの色モードを更新
        if hasattr(self.bb_canvas, 'bb_renderer'):
            self.bb_canvas.bb_renderer.set_color_mode(mode)
            
            # 現在のBBを再描画
            self.bb_canvas.update_bounding_boxes(self.current_annotations)
            
    def on_apply_changes(self, change_id: bool, change_action: bool):
        """選択BBの属性変更（チェックボックスで選択された属性のみ）"""
        selected_bb = self.bb_canvas.get_selected_bb()
        if selected_bb is None:
            self.status_bar.showMessage("BBが選択されていません", 2000)
            return
            
        # 変更メッセージ用リスト
        changes = []
        
        # 選択BBのデータを更新
        for bb in self.current_annotations:
            if bb['id'] == selected_bb.id:
                # IDの変更
                if change_id:
                    current_id = self.id_panel.get_selected_id()
                    if current_id is not None:
                        bb['individual_id'] = current_id
                        changes.append(f"ID: {current_id}")
                
                # 行動の変更
                if change_action:
                    current_action = self.action_panel.get_selected_action()
                    if current_action is not None:
                        bb['action_id'] = current_action
                        action_names = {0: "Sit", 1: "Stand", 2: "Milk", 3: "Water", 4: "Food"}
                        action_name = action_names.get(current_action, "Unknown")
                        changes.append(f"行動: {action_name}")
                break
                
        # 変更がある場合は再描画
        if changes:
            self.bb_canvas.update_bounding_boxes(self.current_annotations)
            self.update_bb_list_panel()
            self.save_current_annotations()
            self.status_bar.showMessage(f"変更: {', '.join(changes)}", 2000)
        else:
            self.status_bar.showMessage("変更する属性が選択されていません", 2000)
        
    def on_continuous_mode_changed(self, enabled: bool):
        """連続モード変更処理"""
        self.continuous_mode = enabled
        status = "ON" if enabled else "OFF"
        self.status_bar.showMessage(f"連続生成モード: {status}", 2000)
        
        # 連続モード用の最後のBBを記録
        if enabled and self.current_annotations:
            self.last_bb_template = self.current_annotations[-1].copy()
            
    def on_copy_bb_to_range(self, start_frame: int, end_frame: int):
        """BBを指定範囲にコピー"""
        if not hasattr(self, 'selected_bb') or self.selected_bb is None:
            self.status_bar.showMessage("BBが選択されていません", 2000)
            return
            
        # 選択BBを取得
        selected_bb_data = None
        for bb in self.current_annotations:
            if bb['id'] == self.selected_bb.id:
                selected_bb_data = bb.copy()
                break
                
        if not selected_bb_data:
            return
            
        # 範囲内の各フレームにコピー
        copied_count = 0
        for frame_num in range(start_frame, end_frame + 1):
            if frame_num == self.current_frame:
                continue  # 現在フレームはスキップ
                
            # フレームのアノテーションファイルパス
            frame_id = f"{frame_num:06d}"
            annotation_file = os.path.join(self.annotation_output_dir, f"{frame_id}.txt")
            
            # 既存のアノテーションを読み込み
            existing_annotations = []
            if os.path.exists(annotation_file):
                try:
                    from persistence.file_io.txt_handler import YOLOTxtHandler
                    handler = YOLOTxtHandler()
                    existing_bbs = handler.load_annotations(frame_id, self.annotation_output_dir)
                    for bb in existing_bbs:
                        existing_annotations.append({
                            'id': bb.id,
                            'x': bb.coordinates.x,
                            'y': bb.coordinates.y,
                            'w': bb.coordinates.w,
                            'h': bb.coordinates.h,
                            'individual_id': bb.individual_id,
                            'action_id': bb.action_id,
                            'confidence': bb.confidence
                        })
                except Exception as e:
                    print(f"Error loading annotations for frame {frame_id}: {e}")
                    
            # IOU計算用のインポート
            from utils.iou_calculator import has_high_overlap
            
            # 重複チェック
            has_overlap, max_iou = has_high_overlap(
                selected_bb_data,
                existing_annotations,
                selected_bb_data['individual_id'],
                iou_threshold=0.8
            )
            
            if not has_overlap:
                # 新しいBBを追加
                new_bb = selected_bb_data.copy()
                new_bb['id'] = f"bb_{frame_id}_{len(existing_annotations)}"
                existing_annotations.append(new_bb)
                
                # 保存
                self.save_annotations_to_file(frame_id, existing_annotations)
                copied_count += 1
            else:
                print(f"Frame {frame_id}: Skipped due to overlap (IOU: {max_iou:.2f})")
            
        self.status_bar.showMessage(f"{copied_count}フレームにBBをコピーしました", 3000)
        
    def on_track_forward(self):
        """追跡での連続ID付（既存BBのIDを変更）"""
        selected_bb = self.bb_canvas.get_selected_bb()
        if not selected_bb:
            self.status_bar.showMessage("BBが選択されていません", 2000)
            return
            
        # 選択BBのデータを取得
        selected_bb_data = None
        for bb in self.current_annotations:
            if bb['id'] == selected_bb.id:
                selected_bb_data = bb.copy()
                break
                
        if not selected_bb_data:
            return
            
        # 追跡実行（デフォルト30フレーム）
        num_frames = 30
        tracked_count = 0
        lost_at_frame = None
        modified_frames = []
        
        current_bb = selected_bb_data
        target_id = selected_bb_data['individual_id']  # 付けるID
        
        for i in range(1, num_frames + 1):
            next_frame = self.current_frame + i
            if next_frame >= self.total_frames:
                break
                
            # 次フレームのアノテーションを読み込み
            frame_id = f"{next_frame:06d}"
            annotation_file = os.path.join(self.annotation_output_dir, f"{frame_id}.txt")
            
            # 既存のアノテーションを読み込み
            existing_annotations = []
            if os.path.exists(annotation_file):
                try:
                    from persistence.file_io.txt_handler import YOLOTxtHandler
                    handler = YOLOTxtHandler()
                    existing_bbs = handler.load_annotations(frame_id, self.annotation_output_dir)
                    for bb in existing_bbs:
                        existing_annotations.append({
                            'id': bb.id,
                            'x': bb.coordinates.x,
                            'y': bb.coordinates.y,
                            'w': bb.coordinates.w,
                            'h': bb.coordinates.h,
                            'individual_id': bb.individual_id,
                            'action_id': bb.action_id,
                            'confidence': bb.confidence
                        })
                except Exception as e:
                    print(f"Error loading annotations for frame {frame_id}: {e}")
                    
            if not existing_annotations:
                # BBがないフレームでは追跡終了
                lost_at_frame = next_frame
                break
                
            # 追跡によるマッチング
            best_match, best_iou = self.tracker.find_best_match(current_bb, existing_annotations)
            
            if best_match and best_iou > 0.3:  # 追跡用の低めの閾値
                # マッチしたBBのIDを変更
                original_id = best_match['individual_id']
                best_match['individual_id'] = target_id
                
                # アノテーションを更新して保存
                self.save_annotations_to_file(frame_id, existing_annotations)
                
                # 次の追跡用に現在BBを更新
                current_bb = best_match
                tracked_count += 1
                modified_frames.append(next_frame)
                
                print(f"Frame {frame_id}: Changed ID from {original_id} to {target_id} (IOU: {best_iou:.2f})")
            else:
                # 追跡断絶
                lost_at_frame = next_frame
                break
                
        # 結果をステータスバーに表示
        if lost_at_frame:
            self.status_bar.showMessage(
                f"追跡でID {target_id} を{tracked_count}フレームの既存BBに付けました。フレーム{lost_at_frame}で追跡断絶", 
                3000
            )
        else:
            self.status_bar.showMessage(
                f"追跡でID {target_id} を{tracked_count}フレームの既存BBに付けました", 
                3000
            )
        
    def save_annotations_to_file(self, frame_id: str, annotations: list):
        """アノテーションをファイルに保存"""
        try:
            from persistence.file_io.txt_handler import YOLOTxtHandler, BBEntity, Coordinates
            from datetime import datetime
            
            handler = YOLOTxtHandler()
            
            # BBエンティティに変換
            bb_entities = []
            for bb_data in annotations:
                bb_entity = BBEntity(
                    id=bb_data['id'],
                    frame_id=frame_id,
                    individual_id=bb_data['individual_id'],
                    action_id=bb_data['action_id'],
                    coordinates=Coordinates(
                        x=bb_data['x'],
                        y=bb_data['y'],
                        w=bb_data['w'],
                        h=bb_data['h']
                    ),
                    confidence=bb_data['confidence'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                bb_entities.append(bb_entity)
            
            # 保存実行
            handler.save_annotations(frame_id, bb_entities, self.annotation_output_dir)
            
        except Exception as e:
            print(f"Error saving annotations: {e}")
        
    def update_status(self, message: str):
        """ステータス更新"""
        self.status_bar.showMessage(message)
        
    def update_bb_list_panel(self):
        """BB一覧パネルを更新"""
        if hasattr(self, 'bb_list_panel'):
            # BBEntityオブジェクトのリストを作成
            bb_entities = []
            for ann in self.current_annotations:
                from presentation.bb_canvas.canvas_widget import BBEntity
                bb_entity = BBEntity(
                    id=ann.get('id', ''),
                    x=ann.get('x', 0.5),
                    y=ann.get('y', 0.5),
                    w=ann.get('w', 0.1),
                    h=ann.get('h', 0.1),
                    individual_id=ann.get('individual_id', 0),
                    action_id=ann.get('action_id', 0),
                    confidence=ann.get('confidence', 1.0),
                    color=self.bb_canvas.ID_COLORS[ann.get('individual_id', 0) % 16]
                )
                bb_entities.append(bb_entity)
            self.bb_list_panel.update_bb_list(bb_entities)
        
    def resizeEvent(self, event):
        """ウィンドウリサイズ処理（100ms以下必達）"""
        start_time = time.perf_counter()
        
        super().resizeEvent(event)
        
        # レイアウト更新
        if hasattr(self, 'layout_manager'):
            self.layout_manager.update_layout(self.size())
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 100:
            print(f"WARNING: Window resize took {elapsed:.2f}ms (>100ms)")
            
    def initialize_project(self):
        """プロジェクト初期化"""
        print(f"Initializing project: {self.project_type}")
        
        if self.project_type == "video":
            self.initialize_video_project()
        elif self.project_type == "images":
            self.initialize_image_project() 
        elif self.project_type == "existing":
            self.initialize_existing_project()
            
        # ステータス更新
        project_name = self.project_config.get('name', 'Unknown Project')
        self.update_status(f"Project loaded: {project_name}")
        
    def initialize_video_project(self):
        """動画プロジェクト初期化"""
        video_path = self.project_path
        output_dir = self.project_config.get('output_directory', '')
        print(f"Video project: {video_path}")
        print(f"Output directory: {output_dir}")
        
        # アノテーション保存先を設定
        if output_dir:
            self.annotation_output_dir = os.path.join(output_dir, 'annotations')
            os.makedirs(self.annotation_output_dir, exist_ok=True)
        
        # Agent4 Infrastructureで処理済みのフレームを読み込み
        try:
            from infrastructure.video.frame_extractor import FrameExtractor
            from infrastructure.image.image_processor import ImageProcessor
            
            # フレーム抽出器初期化
            self.frame_extractor = FrameExtractor()
            self.image_processor = ImageProcessor()
            
            # 出力フォルダからフレーム一覧取得
            if output_dir and os.path.exists(output_dir):
                self.load_processed_frames(output_dir)
            else:
                print("Warning: No output directory specified or doesn't exist")
                self.total_frames = 0
                
        except ImportError as e:
            print(f"Agent4 Infrastructure not available: {e}")
            # フォールバック: 出力ディレクトリまたはdata/frames/から読み込み
            if output_dir and os.path.exists(output_dir):
                self.load_processed_frames(output_dir)
            else:
                self.load_fallback_frames()
            
        self.current_frame = 0
        
    def initialize_image_project(self):
        """画像フォルダプロジェクト初期化"""
        image_folder = self.project_path
        output_dir = self.project_config.get('output_directory', '')
        print(f"Image project: {image_folder}")
        print(f"Output directory: {output_dir}")
        
        # アノテーション保存先を設定
        if output_dir:
            self.annotation_output_dir = os.path.join(output_dir, 'annotations')
        else:
            # 画像フォルダの隣にannotationsフォルダを作成
            self.annotation_output_dir = os.path.join(os.path.dirname(image_folder), 'annotations')
        os.makedirs(self.annotation_output_dir, exist_ok=True)
        
        # Agent4 Infrastructureで処理済みの画像を読み込み
        try:
            from infrastructure.image.image_processor import ImageProcessor
            
            self.image_processor = ImageProcessor()
            
            # 出力フォルダからフレーム一覧取得
            if output_dir:
                self.load_processed_frames(output_dir)
            else:
                # 入力フォルダから直接読み込み
                self.load_image_folder(image_folder)
                
        except ImportError as e:
            print(f"Agent4 Infrastructure not available: {e}")
            # フォールバック: 直接読み込み
            self.load_image_folder(image_folder)
            
        self.current_frame = 0
        
    def initialize_existing_project(self):
        """既存プロジェクト初期化"""
        # 新形式: アノテーションディレクトリと画像ディレクトリ
        annotations_dir = self.project_config.get('annotations_directory', self.project_path)
        images_dir = self.project_config.get('images_directory', '')
        output_dir = self.project_config.get('output_directory', '')
        print(f"Existing annotations: {annotations_dir}")
        print(f"Images directory: {images_dir}")
        print(f"Output directory: {output_dir}")
        
        # アノテーション保存先を設定
        self.annotation_output_dir = annotations_dir
        
        # 画像ディレクトリからフレーム読み込み
        if images_dir:
            self.load_image_folder(images_dir)
            
            # 初回フレームのアノテーション読み込み
            if self.total_frames > 0:
                self.current_frame = 0
                self.load_current_annotations()
                self.bb_canvas.update_bounding_boxes(self.current_annotations)
                self.update_bb_list_panel()
        else:
            print("Warning: No images directory specified")
            self.total_frames = 0
            
        self.current_frame = 0

    def load_processed_frames(self, output_dir: str):
        """処理済みフレーム読み込み"""
        import os
        
        if not os.path.exists(output_dir):
            print(f"Output directory not found: {output_dir}")
            self.total_frames = 0
            return
            
        # 画像ファイル一覧取得（完全パス付き）
        image_files = []
        frame_paths = []
        for file in os.listdir(output_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                image_files.append(file)
                frame_paths.append(os.path.join(output_dir, file))
                
        self.total_frames = len(image_files)
        self.frame_files = sorted(image_files)
        self.frame_paths = sorted(frame_paths)
        print(f"Loaded {self.total_frames} frames from {output_dir}")
        
        # ファイルリストパネル更新（完全パスで）
        if hasattr(self, 'file_list_panel'):
            self.file_list_panel.load_frame_list(self.frame_paths)
            
            # 初回フレーム表示
            if self.frame_paths:
                first_frame_id = "frame_000000"
                self.file_list_panel.select_frame(first_frame_id)
            
    def load_image_folder(self, image_folder: str):
        """画像フォルダ読み込み"""
        import os
        
        if not os.path.exists(image_folder):
            print(f"Image folder not found: {image_folder}")
            self.total_frames = 0
            return
            
        # 画像ファイル一覧取得（完全パス付き）
        image_files = []
        frame_paths = []
        for file in os.listdir(image_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                image_files.append(file)
                frame_paths.append(os.path.join(image_folder, file))
                
        self.total_frames = len(image_files)
        self.frame_files = sorted(image_files)
        self.frame_paths = sorted(frame_paths)
        self.images_directory = image_folder
        print(f"Loaded {self.total_frames} images from {image_folder}")
        
        # ファイルリストパネル更新（完全パスで）
        if hasattr(self, 'file_list_panel'):
            self.file_list_panel.load_frame_list(self.frame_paths)
            
            # 初回フレーム表示
            if self.frame_paths:
                first_frame_id = "frame_000000"
                self.file_list_panel.select_frame(first_frame_id)
            
    def load_fallback_frames(self):
        """フォールバック: data/frames/から読み込み"""
        fallback_dirs = [
            "data/frames",
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "frames")
        ]
        
        for fallback_dir in fallback_dirs:
            if os.path.exists(fallback_dir):
                self.load_processed_frames(fallback_dir)
                return
                
        print("No fallback frames directory found, creating empty project")
        self.total_frames = 0
        self.frame_files = []
        
        # ステータス更新
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage("Ready - No frames loaded. Please process video first.")
            
    def load_fallback_project(self, project_file: str, images_dir: str):
        """フォールバック: 簡単なJSON読み込み"""
        import json
        import os
        
        try:
            if os.path.exists(project_file):
                with open(project_file, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                    print(f"Loaded project config: {project_data.get('name', 'Unknown')}")
                    
            if images_dir and os.path.exists(images_dir):
                self.load_image_folder(images_dir)
            else:
                self.total_frames = 0
                
        except Exception as e:
            print(f"Error loading fallback project: {e}")
            self.total_frames = 0
            
    def load_annotations(self, annotations_data: dict):
        """アノテーションデータ読み込み"""
        # TODO: Agent3 Domainでアノテーションデータ処理
        print(f"Loading annotations: {len(annotations_data)} frames")
        
    def load_frame(self, frame_index: int):
        """指定フレーム読み込みと表示"""
        if not hasattr(self, 'frame_files') or frame_index >= len(self.frame_files):
            return
            
        frame_file = self.frame_files[frame_index]
        
        # フレームパス特定
        if hasattr(self, 'images_directory'):
            frame_path = os.path.join(self.images_directory, frame_file)
        elif hasattr(self, 'project_config') and self.project_config.get('output_directory'):
            frame_path = os.path.join(self.project_config['output_directory'], frame_file)
        else:
            frame_path = os.path.join("data/frames", frame_file)
            
        # キャンバスにフレーム読み込み
        if hasattr(self, 'bb_canvas'):
            self.bb_canvas.load_frame(frame_path)
            
        # ステータス更新
        self.current_frame = frame_index
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(f"Frame: {frame_index + 1}/{self.total_frames} - {frame_file}")
        
    def closeEvent(self, event):
        """ウィンドウ閉じる処理"""
        # 設定保存
        self.config.save_window_state(self)
        event.accept()


if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # メインウィンドウ作成・表示
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())