"""
ID/行動修正パネル
選択したBBのIDまたは行動のみを変更する機能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon


class ModifyPanel(QWidget):
    """
    ID/行動修正パネル
    
    機能:
    - チェックボックスで変更する属性を選択
    - IDのみ、行動のみ、または両方を変更可能
    """
    
    # シグナル定義
    apply_changes = pyqtSignal(bool, bool)  # (change_id, change_action)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # グループボックス
        group = QGroupBox("BB修正")
        group_layout = QVBoxLayout(group)
        
        # チェックボックス
        self.id_checkbox = QCheckBox("IDを変更")
        self.id_checkbox.setToolTip(
            "チェックすると選択BBのIDを変更します\n"
            "ショートカット: Alt + 0-9, A-F"
        )
        self.id_checkbox.setChecked(True)
        
        self.action_checkbox = QCheckBox("行動を変更")
        self.action_checkbox.setToolTip(
            "チェックすると選択BBの行動を変更します\n"
            "ショートカット: Shift + 1-5"
        )
        self.action_checkbox.setChecked(True)
        
        # 現在の値表示
        self.current_values_label = QLabel("現在の値:")
        self.current_values_label.setStyleSheet("font-weight: bold;")
        
        self.id_label = QLabel("ID: -")
        self.action_label = QLabel("行動: -")
        
        # 適用ボタン
        self.apply_btn = QPushButton("選択BBに適用")
        self.apply_btn.setToolTip(
            "チェックされた属性を選択BBに適用します"
        )
        
        # 説明ラベル
        info_label = QLabel(
            "チェックした属性のみ変更されます"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        
        # レイアウトに追加
        group_layout.addWidget(self.id_checkbox)
        group_layout.addWidget(self.action_checkbox)
        group_layout.addWidget(self.current_values_label)
        group_layout.addWidget(self.id_label)
        group_layout.addWidget(self.action_label)
        group_layout.addWidget(self.apply_btn)
        group_layout.addWidget(info_label)
        
        layout.addWidget(group)
        
        # 初期状態は無効（BBが選択されていないため）
        self.set_enabled(False)
        
        # シグナル接続
        self.apply_btn.clicked.connect(self.on_apply_clicked)
        
    def set_enabled(self, enabled: bool):
        """パネルの有効/無効設定"""
        self.apply_btn.setEnabled(enabled)
        self.id_checkbox.setEnabled(enabled)
        self.action_checkbox.setEnabled(enabled)
        
    def update_state(self, has_selection: bool, current_id: int = None, current_action: int = None):
        """状態更新"""
        self.set_enabled(has_selection)
        
        # 現在の値を表示
        if current_id is not None:
            self.id_label.setText(f"ID: {current_id}")
        else:
            self.id_label.setText("ID: -")
            
        if current_action is not None:
            action_names = {0: "Sit", 1: "Stand", 2: "Milk", 3: "Water", 4: "Food"}
            action_name = action_names.get(current_action, "Unknown")
            self.action_label.setText(f"行動: {action_name} ({current_action})")
        else:
            self.action_label.setText("行動: -")
            
    def on_apply_clicked(self):
        """適用ボタンクリック処理"""
        change_id = self.id_checkbox.isChecked()
        change_action = self.action_checkbox.isChecked()
        
        if change_id or change_action:
            self.apply_changes.emit(change_id, change_action)