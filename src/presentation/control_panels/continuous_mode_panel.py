"""
連続BB生成モードパネル
同じ位置に連続してBBを生成する機能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QCheckBox
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
    """
    
    # シグナル定義
    continuous_mode_changed = pyqtSignal(bool)  # 連続モード変更
    
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
        
        # 説明ラベル
        desc_label = QLabel(
            "有効時: BBを作成すると、次のフレームでも\n"
            "同じ位置に同じBBが自動生成されます"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px;")
        
        # レイアウトに追加
        group_layout.addWidget(self.continuous_check)
        group_layout.addWidget(self.status_label)
        group_layout.addWidget(desc_label)
        
        layout.addWidget(group)
        
        # シグナル接続
        self.continuous_check.stateChanged.connect(self.on_continuous_mode_changed)
        
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
        
        
    def toggle_continuous_mode(self):
        """連続モード切り替え（ショートカット用）"""
        self.continuous_check.setChecked(not self.continuous_check.isChecked())