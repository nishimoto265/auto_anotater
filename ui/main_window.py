import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QMenuBar, QToolBar, QStatusBar, QSplitter)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

from src.ui.frame_viewer import FrameViewer
from src.ui.id_panel import IDPanel
from src.ui.navigation_panel import NavigationPanel
from src.core.annotation_manager import AnnotationManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("オートアノテーションアプリ")
        self.setMinimumSize(1200, 800)
        
        self.annotation_manager = AnnotationManager()
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
        toolbar.addAction(QIcon(), "前フレーム")
        toolbar.addAction(QIcon(), "次フレーム")
        toolbar.addSeparator()
        toolbar.addAction(QIcon(), "BB作成")
        toolbar.addAction(QIcon(), "BB削除")
        toolbar.addSeparator()
        toolbar.addAction(QIcon(), "自動追跡")

    def setup_shortcuts(self):
        # キーボードショートカット
        self.shortcuts = {
            "Ctrl+Z": self.undo,
            "Ctrl+Y": self.redo,
            "Left": self.prev_frame,
            "Right": self.next_frame,
            "Delete": self.delete_selected_bb
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

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())