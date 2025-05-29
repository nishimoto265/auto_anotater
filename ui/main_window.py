import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QMenuBar, QToolBar, QStatusBar, QSplitter)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

from src.ui.frame_viewer import FrameViewer
from src.ui.id_panel import IDPanel
from src.ui.navigation_panel import NavigationPanel
from src.core.annotation_manager import AnnotationManager
from utils.performance_monitor import PerformanceMonitor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("オートアノテーションアプリ")
        self.setMinimumSize(1200, 800)
        
        self.annotation_manager = AnnotationManager()
        self.performance_monitor = PerformanceMonitor()
        self.performance_monitor.start_monitoring()
        self.init_ui()
        self.setup_shortcuts()
        self.setup_performance_menu()

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
        
        # パフォーマンスメニュー
        self.performance_menu = menubar.addMenu("パフォーマンス")
        self.show_metrics_action = self.performance_menu.addAction("メトリクス表示")
        self.export_report_action = self.performance_menu.addAction("レポートエクスポート")
        self.performance_menu.addSeparator()
        self.clear_history_action = self.performance_menu.addAction("履歴クリア")

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
        current_frame = self.nav_panel.frame_counter.value()
        self.performance_monitor.start_frame_switch(current_frame)
        self.nav_panel.onPrevFrame()
        new_frame = self.nav_panel.frame_counter.value()
        self.performance_monitor.end_frame_switch(new_frame)
        self.update_performance_status()

    def next_frame(self):
        current_frame = self.nav_panel.frame_counter.value()
        self.performance_monitor.start_frame_switch(current_frame)
        self.nav_panel.onNextFrame()
        new_frame = self.nav_panel.frame_counter.value()
        self.performance_monitor.end_frame_switch(new_frame)
        self.update_performance_status()

    def delete_selected_bb(self):
        self.frame_viewer.delete_selected_bb()

    def setup_performance_menu(self):
        # パフォーマンスメニューのアクション設定
        self.show_metrics_action.triggered.connect(self.show_performance_metrics)
        self.export_report_action.triggered.connect(self.export_performance_report)
        self.clear_history_action.triggered.connect(self.clear_performance_history)
    
    def show_performance_metrics(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit
        summary = self.performance_monitor.get_metrics_summary(300)  # 過去5分間
        
        dialog = QDialog(self)
        dialog.setWindowTitle("パフォーマンスメトリクス")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # メトリクスをフォーマット
        text = "=== パフォーマンスメトリクス (過去5分間) ===\n\n"
        
        if summary:
            # フレーム切り替え時間
            if summary['frame_switch_times']['avg_ms'] is not None:
                text += f"フレーム切り替え時間:\n"
                text += f"  平均: {summary['frame_switch_times']['avg_ms']:.2f}ms\n"
                text += f"  最大: {summary['frame_switch_times']['max_ms']:.2f}ms\n"
                text += f"  最小: {summary['frame_switch_times']['min_ms']:.2f}ms\n\n"
            
            # メモリ使用量
            if summary['memory_usage']['current_mb'] is not None:
                text += f"メモリ使用量:\n"
                text += f"  現在: {summary['memory_usage']['current_mb']:.2f}MB\n"
                text += f"  平均: {summary['memory_usage']['avg_mb']:.2f}MB\n"
                text += f"  最大: {summary['memory_usage']['max_mb']:.2f}MB\n\n"
            
            # CPU使用率
            if summary['cpu_usage']['current_percent'] is not None:
                text += f"CPU使用率:\n"
                text += f"  現在: {summary['cpu_usage']['current_percent']:.1f}%\n"
                text += f"  平均: {summary['cpu_usage']['avg_percent']:.1f}%\n"
                text += f"  最大: {summary['cpu_usage']['max_percent']:.1f}%\n\n"
            
            # GPU使用率
            if summary['gpu_usage']['current_percent'] is not None:
                text += f"GPU使用率:\n"
                text += f"  現在: {summary['gpu_usage']['current_percent']:.1f}%\n"
                text += f"  平均: {summary['gpu_usage']['avg_percent']:.1f}%\n"
                text += f"  最大: {summary['gpu_usage']['max_percent']:.1f}%\n"
        else:
            text += "データがありません\n"
        
        # 最近のアラート
        alerts = self.performance_monitor.get_alerts()
        if alerts:
            text += "\n=== 最近のアラート ===\n"
            for alert in alerts[-10:]:  # 最新10件
                from datetime import datetime
                timestamp = datetime.fromtimestamp(alert.timestamp).strftime('%H:%M:%S')
                text += f"[{timestamp}] {alert.severity.upper()}: {alert.message}\n"
        
        text_edit.setText(text)
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        dialog.exec()
    
    def export_performance_report(self):
        from PyQt6.QtWidgets import QFileDialog
        from datetime import datetime
        
        default_filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filename, _ = QFileDialog.getSaveFileName(
            self, "パフォーマンスレポートを保存", default_filename,
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        
        if filename:
            format = 'csv' if filename.endswith('.csv') else 'json'
            success = self.performance_monitor.export_performance_report(filename, format)
            if success:
                self.statusBar.showMessage(f"レポートを保存しました: {filename}", 3000)
            else:
                self.statusBar.showMessage("レポートの保存に失敗しました", 3000)
    
    def clear_performance_history(self):
        self.performance_monitor.clear_history()
        self.statusBar.showMessage("パフォーマンス履歴をクリアしました", 3000)
    
    def update_performance_status(self):
        # ステータスバーに最新のメトリクスを表示
        metrics = self.performance_monitor.get_current_metrics()
        if metrics:
            status_text = []
            if metrics.frame_switch_time is not None:
                status_text.append(f"切替: {metrics.frame_switch_time*1000:.1f}ms")
            if metrics.process_memory_mb is not None:
                status_text.append(f"メモリ: {metrics.process_memory_mb:.1f}MB")
            if metrics.cpu_percent is not None:
                status_text.append(f"CPU: {metrics.cpu_percent:.1f}%")
            
            if status_text:
                self.statusBar.showMessage(" | ".join(status_text), 5000)
    
    def closeEvent(self, event):
        # アプリケーション終了時にモニタリングを停止
        self.performance_monitor.stop_monitoring()
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