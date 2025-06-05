"""
Agent1 Presentation - FileListPanel
ファイル一覧パネル（フレーム一覧・ナビゲーション・高速表示）

性能要件:
- フレーム一覧更新: 20ms以下
- フレーム選択: 5ms以下
- サムネイル表示: 50ms以下
- スクロール応答: 10ms以下
"""

import time
import os
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QFrame, QPushButton, QProgressBar, QScrollArea,
    QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon, QBrush


class FrameListItem(QListWidgetItem):
    """フレームリストアイテム（高速表示・サムネイル対応）"""
    
    def __init__(self, frame_path: str, frame_index: int, parent=None):
        super().__init__(parent)
        self.frame_path = frame_path
        self.frame_index = frame_index
        self.frame_id = f"frame_{frame_index:06d}"
        self.has_annotations = False
        self.annotation_count = 0
        
        # 表示設定
        self.setText(f"Frame {frame_index:06d}")
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizeHint(QSize(120, 80))
        
        # 初期スタイル設定
        self.update_appearance()
        
    def update_appearance(self):
        """外観更新（アノテーション状態反映）"""
        start_time = time.perf_counter()
        
        try:
            if self.has_annotations:
                # アノテーション有り: 緑背景
                brush = QBrush(QColor(200, 255, 200))
                self.setBackground(brush)
                self.setText(f"Frame {self.frame_index:06d}\n({self.annotation_count} BBs)")
            else:
                # アノテーション無し: 通常背景
                brush = QBrush(QColor(255, 255, 255))
                self.setBackground(brush)
                self.setText(f"Frame {self.frame_index:06d}\n(No BBs)")
                
        except Exception as e:
            print(f"Frame item appearance update error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Frame item appearance update took {elapsed:.2f}ms (>5ms)")
            
    def set_annotation_status(self, has_annotations: bool, count: int = 0):
        """アノテーション状態設定"""
        self.has_annotations = has_annotations
        self.annotation_count = count
        self.update_appearance()
        
    def set_thumbnail(self, pixmap: QPixmap):
        """サムネイル設定"""
        if not pixmap.isNull():
            # アイコンサイズに調整
            scaled_pixmap = pixmap.scaled(60, 40, Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
            self.setIcon(QIcon(scaled_pixmap))


class FileListPanel(QWidget):
    """
    ファイル一覧パネル（フレーム一覧・ナビゲーション・高速表示）
    
    性能要件:
    - フレーム一覧更新: 20ms以下
    - フレーム選択: 5ms以下
    - サムネイル表示: 50ms以下
    - スクロール応答: 10ms以下
    """
    
    # シグナル定義
    frame_selected = pyqtSignal(str)  # 選択されたフレームID
    frame_double_clicked = pyqtSignal(str)  # ダブルクリックされたフレームID
    frames_loaded = pyqtSignal(int)  # ロードされたフレーム数
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 状態管理
        self.frame_items: Dict[str, FrameListItem] = {}
        self.selected_frame_id: Optional[str] = None
        self.total_frames = 0
        self.loaded_frames = 0
        
        # 性能統計
        self.update_count = 0
        self.total_update_time = 0
        self.last_update_time = 0
        self.selection_times = []
        
        # UI構築
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # タイトル
        title_label = QLabel("フレーム一覧")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 情報表示
        self.info_label = QLabel("フレーム数: 0 / ロード済み: 0")
        self.info_label.setFont(QFont("Arial", 9))
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # フレームリスト
        list_frame = QFrame()
        list_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(2, 2, 2, 2)
        
        self.frame_list = QListWidget()
        self.frame_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.frame_list.setViewMode(QListWidget.ViewMode.ListMode)
        self.frame_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.frame_list.setFont(QFont("Arial", 8))
        self.frame_list.setAlternatingRowColors(True)
        
        list_layout.addWidget(self.frame_list)
        layout.addWidget(list_frame)
        
        # ナビゲーションボタン
        nav_frame = QFrame()
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(2, 2, 2, 2)
        
        self.first_btn = QPushButton("⏮ 最初")
        self.prev_btn = QPushButton("⏪ 前")
        self.next_btn = QPushButton("⏩ 次")
        self.last_btn = QPushButton("⏭ 最後")
        
        for btn in [self.first_btn, self.prev_btn, self.next_btn, self.last_btn]:
            btn.setFixedHeight(30)
            btn.setFont(QFont("Arial", 8))
            nav_layout.addWidget(btn)
            
        layout.addWidget(nav_frame)
        
        # 選択情報
        self.selection_label = QLabel("選択: なし")
        self.selection_label.setFont(QFont("Arial", 9))
        self.selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.selection_label)
        
        # 統計情報
        self.stats_label = QLabel("性能: 更新0回")
        self.stats_label.setFont(QFont("Arial", 8))
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)
        
    def setup_connections(self):
        """シグナル接続"""
        self.frame_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.frame_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # ナビゲーションボタン
        self.first_btn.clicked.connect(self.go_to_first_frame)
        self.prev_btn.clicked.connect(self.go_to_previous_frame)
        self.next_btn.clicked.connect(self.go_to_next_frame)
        self.last_btn.clicked.connect(self.go_to_last_frame)
        
    def load_frame_list(self, frame_paths: List[str]) -> float:
        """
        フレーム一覧ロード（20ms以下必達）
        
        Args:
            frame_paths: フレームパスリスト
            
        Returns:
            float: ロード時間（ms）
        """
        start_time = time.perf_counter()
        
        try:
            # プログレスバー表示
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(frame_paths))
            self.progress_bar.setValue(0)
            
            # 既存リストクリア
            self.frame_list.clear()
            self.frame_items.clear()
            
            # フレーム情報更新
            self.total_frames = len(frame_paths)
            self.loaded_frames = 0
            
            # バッチ処理で高速ロード
            batch_size = 50  # 50個ずつ処理
            for i in range(0, len(frame_paths), batch_size):
                batch = frame_paths[i:i + batch_size]
                self._load_frame_batch(batch, i)
                self.loaded_frames += len(batch)
                self.progress_bar.setValue(self.loaded_frames)
                
                # UI更新（応答性維持）
                if i % 100 == 0:
                    self.update_info_display()
                    
            # プログレスバー非表示
            self.progress_bar.setVisible(False)
            
            # 最終情報更新
            self.update_info_display()
            
        except Exception as e:
            print(f"Frame list load error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        
        # 統計更新
        self.update_count += 1
        self.total_update_time += elapsed
        self.last_update_time = elapsed
        
        # 性能監視
        if elapsed > 20:
            print(f"WARNING: Frame list load took {elapsed:.2f}ms (>20ms)")
            
        # シグナル発出
        self.frames_loaded.emit(self.loaded_frames)
        
        return elapsed
        
    def _load_frame_batch(self, frame_paths: List[str], start_index: int):
        """フレームバッチロード"""
        for i, frame_path in enumerate(frame_paths):
            frame_index = start_index + i
            frame_item = FrameListItem(frame_path, frame_index)
            
            self.frame_list.addItem(frame_item)
            self.frame_items[frame_item.frame_id] = frame_item
            
    def select_frame(self, frame_id: str) -> float:
        """
        フレーム選択（5ms以下必達）
        
        Args:
            frame_id: 選択するフレームID
            
        Returns:
            float: 選択時間（ms）
        """
        start_time = time.perf_counter()
        
        try:
            if frame_id in self.frame_items:
                item = self.frame_items[frame_id]
                # UI更新を最小限に
                self.frame_list.blockSignals(True)
                self.frame_list.setCurrentItem(item)
                self.frame_list.blockSignals(False)
                
                self.selected_frame_id = frame_id
                self.frame_selected.emit(frame_id)
                
                # スクロールは必要時のみ（パフォーマンス優先）
                current_row = self.frame_list.currentRow()
                visible_range = self.frame_list.viewport().height() // 80  # アイテム高さ80px想定
                first_visible = self.frame_list.verticalScrollBar().value() // 80
                
                if current_row < first_visible or current_row > first_visible + visible_range:
                    self.frame_list.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)
                
        except Exception as e:
            print(f"Frame selection error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        self.selection_times.append(elapsed)
        
        if elapsed > 5:
            print(f"WARNING: Frame selection took {elapsed:.2f}ms (>5ms)")
            
        return elapsed
        
    def update_frame_annotation_status(self, frame_id: str, has_annotations: bool, count: int = 0):
        """フレームアノテーション状態更新"""
        if frame_id in self.frame_items:
            self.frame_items[frame_id].set_annotation_status(has_annotations, count)
            
    def on_selection_changed(self):
        """選択変更処理"""
        current_item = self.frame_list.currentItem()
        if isinstance(current_item, FrameListItem):
            self.selected_frame_id = current_item.frame_id
            self.frame_selected.emit(current_item.frame_id)
            
            # 選択情報更新
            self.selection_label.setText(f"選択: {current_item.frame_id} (Index: {current_item.frame_index})")
            
    def on_item_double_clicked(self, item: QListWidgetItem):
        """アイテムダブルクリック処理"""
        if isinstance(item, FrameListItem):
            self.frame_double_clicked.emit(item.frame_id)
            
    def go_to_first_frame(self):
        """最初のフレームに移動"""
        if self.frame_list.count() > 0:
            first_item = self.frame_list.item(0)
            if isinstance(first_item, FrameListItem):
                self.select_frame(first_item.frame_id)
                
    def go_to_previous_frame(self):
        """前のフレームに移動"""
        current_row = self.frame_list.currentRow()
        if current_row > 0:
            prev_item = self.frame_list.item(current_row - 1)
            if isinstance(prev_item, FrameListItem):
                self.select_frame(prev_item.frame_id)
                
    def go_to_next_frame(self):
        """次のフレームに移動"""
        current_row = self.frame_list.currentRow()
        if current_row < self.frame_list.count() - 1:
            next_item = self.frame_list.item(current_row + 1)
            if isinstance(next_item, FrameListItem):
                self.select_frame(next_item.frame_id)
                
    def go_to_last_frame(self):
        """最後のフレームに移動"""
        last_index = self.frame_list.count() - 1
        if last_index >= 0:
            last_item = self.frame_list.item(last_index)
            if isinstance(last_item, FrameListItem):
                self.select_frame(last_item.frame_id)
                
    def update_info_display(self):
        """情報表示更新"""
        self.info_label.setText(f"フレーム数: {self.total_frames} / ロード済み: {self.loaded_frames}")
        
        # 統計更新
        avg_update_time = (self.total_update_time / self.update_count 
                          if self.update_count > 0 else 0)
        avg_selection_time = (sum(self.selection_times) / len(self.selection_times)
                             if self.selection_times else 0)
        
        self.stats_label.setText(
            f"性能: 更新{self.update_count}回 (平均{avg_update_time:.1f}ms), 選択平均{avg_selection_time:.1f}ms"
        )
        
    def get_selected_frame_id(self) -> Optional[str]:
        """選択フレームID取得"""
        return self.selected_frame_id
        
    def get_frame_count(self) -> int:
        """フレーム数取得"""
        return self.total_frames
        
    def get_current_frame_index(self) -> int:
        """現在フレームインデックス取得"""
        current_item = self.frame_list.currentItem()
        if isinstance(current_item, FrameListItem):
            return current_item.frame_index
        return -1
        
    def clear_frames(self):
        """フレームリストクリア"""
        self.frame_list.clear()
        self.frame_items.clear()
        self.selected_frame_id = None
        self.total_frames = 0
        self.loaded_frames = 0
        self.update_info_display()
        
    def set_frame_thumbnail(self, frame_id: str, pixmap: QPixmap):
        """フレームサムネイル設定"""
        if frame_id in self.frame_items:
            self.frame_items[frame_id].set_thumbnail(pixmap)
            
    def get_performance_info(self) -> Dict[str, Any]:
        """性能情報取得"""
        avg_update_time = (self.total_update_time / self.update_count 
                          if self.update_count > 0 else 0)
        avg_selection_time = (sum(self.selection_times) / len(self.selection_times)
                             if self.selection_times else 0)
        
        return {
            'total_frames': self.total_frames,
            'loaded_frames': self.loaded_frames,
            'selected_frame_id': self.selected_frame_id,
            'update_count': self.update_count,
            'avg_update_time': avg_update_time,
            'avg_selection_time': avg_selection_time,
            'last_update_time': self.last_update_time,
            'target_performance': {
                'frame_list_update': '20ms以下',
                'frame_selection': '5ms以下',
                'thumbnail_display': '50ms以下',
                'scroll_response': '10ms以下',
            }
        }


if __name__ == "__main__":
    # FileListPanelテスト
    from PyQt6.QtWidgets import QApplication, QMainWindow
    import sys
    
    app = QApplication(sys.argv)
    
    # メインウィンドウ作成
    main_window = QMainWindow()
    
    # FileListPanel作成
    file_list_panel = FileListPanel()
    main_window.setCentralWidget(file_list_panel)
    main_window.resize(300, 600)
    main_window.show()
    
    # テスト用フレームパス生成
    def create_test_frame_paths(count: int) -> List[str]:
        return [f"/path/to/frame_{i:06d}.jpg" for i in range(count)]
    
    # 性能テスト
    print("FileListPanel Performance Test")
    print("=" * 35)
    
    # ロード性能テスト
    test_counts = [100, 500, 1000, 2000]
    
    for count in test_counts:
        print(f"\nTesting {count} frames:")
        test_frame_paths = create_test_frame_paths(count)
        
        # ロード時間測定
        load_time = file_list_panel.load_frame_list(test_frame_paths)
        
        print(f"  Load time: {load_time:.2f}ms")
        print(f"  Target: <20ms, Status: {'PASS' if load_time < 20 else 'FAIL'}")
        
        # 選択性能テスト（最初の10フレーム）
        selection_times = []
        for i in range(min(10, count)):
            frame_id = f"frame_{i:06d}"
            select_time = file_list_panel.select_frame(frame_id)
            selection_times.append(select_time)
            
        if selection_times:
            avg_select_time = sum(selection_times) / len(selection_times)
            print(f"  Selection average time: {avg_select_time:.3f}ms")
            print(f"  Selection target: <5ms, Status: {'PASS' if avg_select_time < 5 else 'FAIL'}")
        
        # アノテーション状態テスト
        for i in range(0, min(count, 50), 5):  # 5個おきに50個まで
            frame_id = f"frame_{i:06d}"
            file_list_panel.update_frame_annotation_status(frame_id, True, i % 5 + 1)
            
    # 性能情報表示
    perf_info = file_list_panel.get_performance_info()
    print("\nPerformance Info:")
    for key, value in perf_info.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")
            
    print("FileListPanel test completed")
    
    # アプリケーション実行（テスト用）
    # sys.exit(app.exec())