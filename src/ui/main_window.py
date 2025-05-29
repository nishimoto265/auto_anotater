import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QMenuBar, QToolBar, QStatusBar, QSplitter, QLabel)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QIcon

from src.ui.frame_viewer import FrameViewer
from src.ui.id_panel import IdPanel
from src.ui.navigation_panel import NavigationPanel
from src.core.annotation_manager import AnnotationManager
from src.core.image_cache import ImageCache
from src.utils.color_manager import ColorManager

class MainWindow(QMainWindow):
    def __init__(self, source_type='video', start_frame=0, config_manager=None):
        super().__init__()
        self.source_type = source_type
        self.start_frame = start_frame
        self.config_manager = config_manager
        self.color_manager = ColorManager()
        
        self.setWindowTitle("オートアノテーションアプリ")
        self.setMinimumSize(1200, 800)
        
        # config_managerから設定ファイルパスを取得
        config_path = 'config/app_config.json'  # デフォルトパス
        if self.config_manager:
            config_path = self.config_manager.config_path
            
        # Initialize image cache with configuration
        cache_size_gb = 20.0
        max_memory_gb = 64.0
        if self.config_manager:
            cache_size_gb = self.config_manager.get_setting('performance.cache_size_gb', 20)
            max_memory_gb = self.config_manager.get_setting('performance.max_memory_usage_gb', 64)
            
        self.image_cache = ImageCache(max_cache_size_gb=cache_size_gb, max_memory_gb=max_memory_gb)
        
        self.annotation_manager = AnnotationManager(config_path)
        self.init_ui()
        self.setup_shortcuts()
        self.setup_memory_monitor()

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
        self.frame_viewer = FrameViewer(image_cache=self.image_cache)
        splitter.addWidget(self.frame_viewer)
        
        # 右サイドパネル
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # ID選択パネル
        self.id_panel = IdPanel(self.config_manager, self.color_manager)
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
        
        # メモリ使用状況表示用ラベル
        self.memory_label = QLabel("メモリ: 0.0GB / 0.0GB")
        self.cache_label = QLabel("キャッシュ: 0フレーム")
        self.hit_ratio_label = QLabel("ヒット率: 0.0%")
        
        self.statusBar.addPermanentWidget(self.memory_label)
        self.statusBar.addPermanentWidget(self.cache_label)
        self.statusBar.addPermanentWidget(self.hit_ratio_label)
        
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

    def setup_memory_monitor(self):
        """メモリ監視タイマーをセットアップ"""
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_status)
        self.memory_timer.start(1000)  # 1秒ごとに更新
        
    def update_memory_status(self):
        """メモリ使用状況をステータスバーに更新"""
        stats = self.image_cache.get_memory_stats()
        
        # メモリ使用状況
        memory_text = f"メモリ: {stats['total_used_gb']:.1f}GB / {stats['max_memory_gb']:.1f}GB"
        self.memory_label.setText(memory_text)
        
        # キャッシュ状況
        cache_text = f"キャッシュ: {stats['cache_frames']}フレーム ({stats['cache_size_gb']:.1f}GB / {stats['max_cache_gb']:.1f}GB)"
        self.cache_label.setText(cache_text)
        
        # ヒット率
        hit_ratio = stats['hit_ratio'] * 100
        hit_text = f"ヒット率: {hit_ratio:.1f}%"
        self.hit_ratio_label.setText(hit_text)
        
    def closeEvent(self, event):
        """ウィンドウ終了時の処理"""
        if hasattr(self, 'memory_timer'):
            self.memory_timer.stop()
        if hasattr(self, 'image_cache'):
            self.image_cache.stop()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.frame_viewer.update_view()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())