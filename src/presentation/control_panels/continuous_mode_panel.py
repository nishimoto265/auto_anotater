"""
連続BB生成モードパネル
同じ位置に連続してBBを生成する機能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QCheckBox, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class ContinuousModePanel(QWidget):
    """
    連続BB生成モードパネル
    
    機能:
    - 連続モードのON/OFF
    - 最後に作成したBBの位置を記憶
    - フレーム切り替え時に同じ位置にBB自動生成
    - 範囲指定でBBをコピー
    """
    
    # シグナル定義
    continuous_mode_changed = pyqtSignal(bool)  # 連続モード変更
    copy_bb_to_range = pyqtSignal(int, int)  # 開始フレーム, 終了フレーム
    track_forward = pyqtSignal()  # 前方追跡
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.continuous_mode = False
        self.setup_ui()
        
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # グループボックス
        group = QGroupBox("連続BB生成")
        group_layout = QVBoxLayout(group)
        
        # 連続モードチェックボックス
        self.continuous_check = QCheckBox("連続生成モード")
        self.continuous_check.setToolTip(
            "有効時: BBを作成すると、次のフレームでも\n"
            "同じ位置に同じBBが自動生成されます\n"
            "ショートカット: Shift + W"
        )
        
        # 状態表示
        self.status_label = QLabel("連続モード: OFF")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.status_label.setFont(font)
        
        # BBコピー範囲設定
        copy_group = QGroupBox("BBを範囲コピー")
        copy_layout = QVBoxLayout(copy_group)
        
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("開始:"))
        self.start_frame_spin = QSpinBox()
        self.start_frame_spin.setMinimum(0)
        self.start_frame_spin.setMaximum(99999)
        range_layout.addWidget(self.start_frame_spin)
        
        range_layout.addWidget(QLabel("終了:"))
        self.end_frame_spin = QSpinBox()
        self.end_frame_spin.setMinimum(0)
        self.end_frame_spin.setMaximum(99999)
        range_layout.addWidget(self.end_frame_spin)
        
        copy_layout.addLayout(range_layout)
        
        self.copy_range_btn = QPushButton("選択BBを範囲にコピー")
        self.copy_range_btn.setToolTip(
            "現在選択中のBBを指定範囲の\n"
            "全フレームにコピーします"
        )
        self.copy_range_btn.setEnabled(False)
        copy_layout.addWidget(self.copy_range_btn)
        
        # 追跡でID付ボタン
        self.track_forward_btn = QPushButton("追跡でID付")
        self.track_forward_btn.setToolTip(
            "選択したBBを後続フレームで追跡し、\n"
            "追跡が途切れるまで同じIDを付けます"
        )
        self.track_forward_btn.setEnabled(False)
        
        # レイアウトに追加
        group_layout.addWidget(self.continuous_check)
        group_layout.addWidget(self.status_label)
        group_layout.addWidget(copy_group)
        group_layout.addWidget(self.track_forward_btn)
        
        layout.addWidget(group)
        
        # シグナル接続
        self.continuous_check.stateChanged.connect(self.on_continuous_mode_changed)
        self.copy_range_btn.clicked.connect(self.on_copy_range_clicked)
        self.track_forward_btn.clicked.connect(self.track_forward.emit)
        
    def on_continuous_mode_changed(self, state):
        """連続モード変更処理"""
        self.continuous_mode = (state == Qt.CheckState.Checked.value)
        self.status_label.setText(f"連続モード: {'ON' if self.continuous_mode else 'OFF'}")
        
        # 状態に応じてスタイル変更
        if self.continuous_mode:
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: black; font-weight: bold;")
            
        self.continuous_mode_changed.emit(self.continuous_mode)
        
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
        self.track_forward_btn.setEnabled(has_selection)
        
    def toggle_continuous_mode(self):
        """連続モード切り替え（ショートカット用）"""
        self.continuous_check.setChecked(not self.continuous_check.isChecked())