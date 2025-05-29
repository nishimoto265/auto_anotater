import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QMenuBar, QToolBar, QStatusBar, QSplitter, QLabel)
from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtGui import QAction, QIcon

from ui.frame_viewer import FrameViewer
from ui.id_panel import IDPanel
from ui.navigation_panel import NavigationPanel
from core.annotation_manager import AnnotationManager, SaveStatus

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("オートアノテーションアプリ")
        self.setMinimumSize(1200, 800)
        
        self.annotation_manager = AnnotationManager("config/app_config.json")
        self.save_status_label = None
        self.init_ui()
        self.setup_shortcuts()
        self.setup_auto_save()

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
        
        # 保存ステータスラベル
        self.save_status_label = QLabel("保存状態: 待機中")
        self.statusBar.addPermanentWidget(self.save_status_label)
        
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
    
    def setup_auto_save(self):
        """自動保存機能のセットアップ"""
        self.annotation_manager.set_save_status_callback(self.on_save_status_changed)
        self.annotation_manager.set_save_error_callback(self.on_save_error)
    
    @pyqtSlot(SaveStatus)
    def on_save_status_changed(self, status: SaveStatus):
        """保存ステータスが変更されたときの処理"""
        status_text = {
            SaveStatus.IDLE: "保存状態: 待機中",
            SaveStatus.SAVING: "保存状態: 保存中...",
            SaveStatus.SUCCESS: "保存状態: 保存完了",
            SaveStatus.ERROR: "保存状態: エラー"
        }
        
        self.save_status_label.setText(status_text.get(status, "保存状態: 不明"))
        
        # ステータスに応じて色を変更
        if status == SaveStatus.SAVING:
            self.save_status_label.setStyleSheet("color: blue;")
        elif status == SaveStatus.SUCCESS:
            self.save_status_label.setStyleSheet("color: green;")
        elif status == SaveStatus.ERROR:
            self.save_status_label.setStyleSheet("color: red;")
        else:
            self.save_status_label.setStyleSheet("")
    
    @pyqtSlot(str)
    def on_save_error(self, error_message: str):
        """保存エラーが発生したときの処理"""
        self.statusBar.showMessage(f"保存エラー: {error_message}", 5000)
    
    def closeEvent(self, event):
        """ウィンドウが閉じられるときの処理"""
        # 自動保存を停止し、最後の保存を実行
        self.annotation_manager.stop_auto_save()
        self.annotation_manager.force_save()
        event.accept()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())