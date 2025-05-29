import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QMenuBar, QToolBar, QStatusBar, QSplitter)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

from src.ui.frame_viewer import FrameViewer
from src.ui.id_panel import IDPanel
from src.ui.navigation_panel import NavigationPanel
from src.ui.dialogs import show_warning, show_error
from src.core.annotation_manager import AnnotationManager
from src.core.tracking_system import TrackingSystem
from src.core.bbox_manager import BBoxManager
from src.core.image_cache import ImageCache
from src.utils.algorithm_utils import AlgorithmUtils

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("オートアノテーションアプリ")
        self.setMinimumSize(1200, 800)
        
        self.annotation_manager = AnnotationManager()
        self.bbox_manager = BBoxManager()
        self.image_cache = ImageCache()
        self.algorithm_utils = AlgorithmUtils()
        self.tracking_system = TrackingSystem(
            self.bbox_manager, self.image_cache, self.algorithm_utils
        )
        self.tracking_enabled = False
        self.current_frame_id = 0
        
        self.init_ui()
        self.setup_shortcuts()

    def init_ui(self):
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # メニューバーとツールバー
        self.create_menu_bar()
        self.create_tool_bar()
        
        # 中央部分のスプリッター
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # フレームビューア
        self.frame_viewer = FrameViewer()
        splitter.addWidget(self.frame_viewer)
        
        # 右サイドパネル
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # ID選択パネル
        self.id_panel = IDPanel()
        right_layout.addWidget(self.id_panel)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)  # フレームビューアを広く
        splitter.setStretchFactor(1, 1)  # サイドパネルを狭く
        
        main_layout.addWidget(splitter)
        
        # ナビゲーションパネル
        self.nav_panel = NavigationPanel()
        self.nav_panel.frameChanged.connect(self.on_frame_changed)
        main_layout.addWidget(self.nav_panel)
        
        # ステータスバー
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # スタイル設定
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QMenuBar {
                background-color: #F0F0F0;
            }
            QToolBar {
                background-color: #F0F0F0;
                border: none;
            }
            QStatusBar {
                background-color: #F0F0F0;
            }
        """)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        file_menu.addAction("開く")
        file_menu.addAction("保存")
        file_menu.addSeparator()
        file_menu.addAction("終了")
        
        # 編集メニュー
        edit_menu = menubar.addMenu("編集")
        edit_menu.addAction("元に戻す")
        edit_menu.addAction("やり直し")
        
        # 表示メニュー
        view_menu = menubar.addMenu("表示")
        view_menu.addAction("ズームイン")
        view_menu.addAction("ズームアウト")

    def create_tool_bar(self):
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # ツールバーアクション
        self.prev_frame_action = toolbar.addAction(QIcon(), "前フレーム")
        self.next_frame_action = toolbar.addAction(QIcon(), "次フレーム")
        toolbar.addSeparator()
        self.create_bb_action = toolbar.addAction(QIcon(), "BB作成")
        self.delete_bb_action = toolbar.addAction(QIcon(), "BB削除")
        toolbar.addSeparator()
        
        # 追跡関連のアクション
        self.start_tracking_action = QAction(QIcon(), "追跡開始", self)
        self.start_tracking_action.triggered.connect(self.start_tracking)
        toolbar.addAction(self.start_tracking_action)
        
        self.stop_tracking_action = QAction(QIcon(), "追跡停止", self)
        self.stop_tracking_action.triggered.connect(self.stop_tracking)
        self.stop_tracking_action.setEnabled(False)
        toolbar.addAction(self.stop_tracking_action)
        
        toolbar.addSeparator()
        self.tracking_params_action = QAction(QIcon(), "追跡設定", self)
        self.tracking_params_action.triggered.connect(self.show_tracking_params)
        toolbar.addAction(self.tracking_params_action)
        
        # アクションの接続
        self.prev_frame_action.triggered.connect(self.prev_frame)
        self.next_frame_action.triggered.connect(self.next_frame)
        self.delete_bb_action.triggered.connect(self.delete_selected_bb)

    def setup_shortcuts(self):
        # キーボードショートカット
        self.shortcuts = {
            "Ctrl+Z": self.undo,
            "Ctrl+Y": self.redo,
            "Left": self.prev_frame,
            "Right": self.next_frame,
            "Delete": self.delete_selected_bb,
            "T": self.toggle_tracking,
            "Ctrl+T": self.show_tracking_params,
            "Shift+T": self.start_tracking_selected
        }
        
        for key, func in self.shortcuts.items():
            action = QAction(self)
            action.setShortcut(key)
            action.triggered.connect(func)
            self.addAction(action)

    def undo(self):
        self.annotation_manager.undo()
        self.frame_viewer.update()

    def redo(self):
        self.annotation_manager.redo()
        self.frame_viewer.update()

    def prev_frame(self):
        self.nav_panel.go_prev_frame()

    def next_frame(self):
        self.nav_panel.go_next_frame()

    def delete_selected_bb(self):
        self.frame_viewer.delete_selected_bb()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.frame_viewer.update_view()
    
    def start_tracking(self):
        """選択されたBBの追跡を開始"""
        selected_bbox = self.frame_viewer.get_selected_bbox()
        if not selected_bbox:
            show_warning(self, "追跡を開始するにはBounding Boxを選択してください")
            return
            
        individual_id = selected_bbox.individual_id
        success = self.tracking_system.start_tracking(
            self.current_frame_id, individual_id
        )
        
        if success:
            self.tracking_enabled = True
            self.start_tracking_action.setEnabled(False)
            self.stop_tracking_action.setEnabled(True)
            self.frame_viewer.set_tracking_state(individual_id, True)
            self.statusBar.showMessage(
                f"個体 {individual_id} の追跡を開始しました", 3000
            )
        else:
            show_error(self, "追跡の開始に失敗しました")
    
    def stop_tracking(self):
        """追跡を停止"""
        for individual_id in list(self.tracking_system.tracking_states.keys()):
            self.tracking_system.stop_tracking(individual_id)
            self.frame_viewer.set_tracking_state(individual_id, False)
            
        self.tracking_enabled = False
        self.start_tracking_action.setEnabled(True)
        self.stop_tracking_action.setEnabled(False)
        self.statusBar.showMessage("追跡を停止しました", 3000)
    
    def toggle_tracking(self):
        """追跡のオン/オフを切り替え"""
        if self.tracking_enabled:
            self.stop_tracking()
        else:
            self.start_tracking()
    
    def start_tracking_selected(self):
        """選択された個体の追跡を開始（ショートカット用）"""
        self.start_tracking()
    
    def show_tracking_params(self):
        """追跡パラメータダイアログを表示"""
        from src.ui.dialogs import TrackingParametersDialog
        dialog = TrackingParametersDialog(
            self.tracking_system, parent=self
        )
        if dialog.exec():
            self.statusBar.showMessage("追跡パラメータを更新しました", 3000)
    
    def on_frame_changed(self, frame_id: int):
        """フレームが変更されたときの処理"""
        prev_frame_id = self.current_frame_id
        self.current_frame_id = frame_id
        
        if self.tracking_enabled:
            self.tracking_system.update(prev_frame_id, frame_id)
            
            # 追跡失敗をチェック
            for individual_id, state in self.tracking_system.tracking_states.items():
                if state.lost_count >= self.tracking_system.max_lost_frames:
                    self.handle_tracking_failure(individual_id)
    
    def handle_tracking_failure(self, individual_id: int):
        """追跡失敗時の処理"""
        from PyQt6.QtWidgets import QMessageBox
        
        msg = QMessageBox(self)
        msg.setWindowTitle("追跡エラー")
        msg.setText(f"個体 {individual_id} の追跡が失われました。")
        msg.setInformativeText("手動で位置を修正しますか？")
        
        correct_btn = msg.addButton("修正", QMessageBox.ButtonRole.AcceptRole)
        skip_btn = msg.addButton("スキップ", QMessageBox.ButtonRole.RejectRole)
        stop_btn = msg.addButton("追跡停止", QMessageBox.ButtonRole.DestructiveRole)
        
        msg.exec()
        
        if msg.clickedButton() == correct_btn:
            self.frame_viewer.enable_manual_correction_mode(individual_id)
        elif msg.clickedButton() == stop_btn:
            self.tracking_system.stop_tracking(individual_id)
            self.frame_viewer.set_tracking_state(individual_id, False)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())