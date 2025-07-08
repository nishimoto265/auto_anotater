"""
BB範囲コピーパネル
選択したBBを指定範囲のフレームにコピーする機能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, Qt


class BBCopyPanel(QWidget):
    """
    BB範囲コピーパネル
    
    機能:
    - 選択したBBを指定フレーム範囲にコピー
    - 開始・終了フレーム指定
    - 重複チェック付きコピー
    """
    
    # シグナル定義
    copy_bb_to_range = pyqtSignal(int, int)  # 開始フレーム, 終了フレーム
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # グループボックス
        group = QGroupBox("BBを範囲にコピー")
        group_layout = QVBoxLayout(group)
        
        # 説明ラベル
        desc_label = QLabel(
            "選択したBBを指定範囲の\n"
            "全フレームにコピーします"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px;")
        group_layout.addWidget(desc_label)
        
        # フレーム範囲設定
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("開始:"))
        self.start_frame_spin = QSpinBox()
        self.start_frame_spin.setMinimum(0)
        self.start_frame_spin.setMaximum(99999)
        self.start_frame_spin.setToolTip("コピー開始フレーム")
        range_layout.addWidget(self.start_frame_spin)
        
        range_layout.addWidget(QLabel("終了:"))
        self.end_frame_spin = QSpinBox()
        self.end_frame_spin.setMinimum(0)
        self.end_frame_spin.setMaximum(99999)
        self.end_frame_spin.setToolTip("コピー終了フレーム")
        range_layout.addWidget(self.end_frame_spin)
        
        group_layout.addLayout(range_layout)
        
        # コピー実行ボタン
        self.copy_range_btn = QPushButton("選択BBを範囲にコピー")
        self.copy_range_btn.setToolTip(
            "現在選択中のBBを指定範囲の\n"
            "全フレームにコピーします\n"
            "※重複チェック付き（IOU > 0.8）"
        )
        self.copy_range_btn.setEnabled(False)
        group_layout.addWidget(self.copy_range_btn)
        
        layout.addWidget(group)
        
        # シグナル接続
        self.copy_range_btn.clicked.connect(self.on_copy_range_clicked)
        
    def on_copy_range_clicked(self):
        """範囲コピーボタンクリック"""
        start = self.start_frame_spin.value()
        end = self.end_frame_spin.value()
        
        if start <= end:
            self.copy_bb_to_range.emit(start, end)
        
    def set_frame_range(self, current: int, total: int):
        """フレーム範囲設定"""
        self.start_frame_spin.setMaximum(total - 1)
        self.end_frame_spin.setMaximum(total - 1)
        self.start_frame_spin.setValue(current)
        self.end_frame_spin.setValue(min(current + 10, total - 1))
        
    def set_selection_state(self, has_selection: bool):
        """選択状態に応じてボタンを有効/無効化"""
        self.copy_range_btn.setEnabled(has_selection)