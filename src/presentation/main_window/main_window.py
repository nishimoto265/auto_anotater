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
from typing import Optional, Dict, Any
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
from ..shortcuts.keyboard_handler import KeyboardHandler


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
        self.bb_list_panel = BBListPanel()
        self.file_list_panel = FileListPanel()
        
        # レイアウト
        layout = QVBoxLayout(frame)
        layout.addWidget(self.id_panel)
        layout.addWidget(self.action_panel)
        layout.addWidget(self.bb_list_panel)
        layout.addWidget(self.file_list_panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
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
        }
        
        for key, handler in shortcuts.items():
            self.keyboard_handler.register_shortcut(key, handler.__name__, handler)
            
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
        
    # ==================== ショートカットハンドラー ====================
    
    def previous_frame(self):
        """前フレーム（Aキー・50ms以下必達）"""
        start_time = time.perf_counter()
        
        current_frame = self.get_current_frame_id()
        if current_frame > 0:
            new_frame = f"{current_frame - 1:06d}"
            self.frame_change_requested.emit(new_frame)
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 50:
            print(f"WARNING: Previous frame took {elapsed:.2f}ms (>50ms)")
            
    def next_frame(self):
        """次フレーム（Dキー・50ms以下必達）"""
        start_time = time.perf_counter()
        
        current_frame = self.get_current_frame_id()
        max_frame = self.get_max_frame_id()
        if current_frame < max_frame:
            new_frame = f"{current_frame + 1:06d}"
            self.frame_change_requested.emit(new_frame)
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 50:
            print(f"WARNING: Next frame took {elapsed:.2f}ms (>50ms)")
            
    def toggle_bb_creation_mode(self):
        """BB作成モード切り替え（Wキー・1ms以下）"""
        start_time = time.perf_counter()
        
        self.bb_canvas.toggle_creation_mode()
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: BB creation mode toggle took {elapsed:.2f}ms (>1ms)")
            
    def delete_selected_bb(self):
        """選択BB削除（Sキー・1ms以下）"""
        start_time = time.perf_counter()
        
        selected_bb = self.bb_canvas.get_selected_bb()
        if selected_bb:
            self.bb_deletion_requested.emit(selected_bb.id)
            
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
        
    # ==================== イベントハンドラー ====================
    
    def on_bb_created(self, x: float, y: float, w: float, h: float):
        """BB作成時の処理"""
        current_id = self.id_panel.get_selected_id()
        current_action = self.action_panel.get_selected_action()
        self.bb_creation_requested.emit(x, y, w, h, current_id, current_action)
        
    def on_bb_selected(self, bb_id: str):
        """BB選択時の処理"""
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
                # 現在フレーム更新
                if hasattr(self, 'file_list_panel'):
                    current_index = self.file_list_panel.get_current_frame_index()
                    self.current_frame = current_index
                    
                # ステータス更新
                self.update_status(f"Frame: {self.current_frame + 1}/{self.total_frames}")
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
        
    def update_status(self, message: str):
        """ステータス更新"""
        self.status_bar.showMessage(message)
        
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
        project_file = self.project_path
        images_dir = self.project_config.get('images_directory', '')
        output_dir = self.project_config.get('output_directory', '')
        print(f"Existing project: {project_file}")
        print(f"Images directory: {images_dir}")
        print(f"Output directory: {output_dir}")
        
        # Agent7 Persistenceでプロジェクト読み込み
        try:
            from persistence.file_io.json_handler import JSONHandler
            
            self.json_handler = JSONHandler()
            
            # プロジェクト設定読み込み
            project_data = self.json_handler.load_project(project_file)
            
            # 画像ディレクトリからフレーム読み込み
            if images_dir:
                self.load_image_folder(images_dir)
            else:
                print("Warning: No images directory specified")
                self.total_frames = 0
                
            # アノテーションデータ復元
            if 'annotations' in project_data:
                self.load_annotations(project_data['annotations'])
                
        except ImportError as e:
            print(f"Agent7 Persistence not available: {e}")
            # フォールバック: 直接JSON読み込み
            self.load_fallback_project(project_file, images_dir)
            
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