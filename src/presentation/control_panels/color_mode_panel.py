"""
色表示モード切り替えパネル
IDベースまたは行動ベースの色分けを切り替える
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QButtonGroup, QLabel, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class ColorModePanel(QWidget):
    """
    色表示モード切り替えパネル
    
    機能:
    - ID別色分け / 行動別色分け の切り替え
    - 色分けモードの表示
    """
    
    # シグナル定義
    color_mode_changed = pyqtSignal(str)  # 'id' or 'action'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = 'id'  # デフォルトはID別
        self.setup_ui()
        
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # グループボックス
        group = QGroupBox("色分けモード")
        group_layout = QVBoxLayout(group)
        
        # モード選択ボタン
        self.id_mode_btn = QPushButton("ID別色分け")
        self.id_mode_btn.setCheckable(True)
        self.id_mode_btn.setChecked(True)
        self.id_mode_btn.setToolTip("個体ID（0-15）で色分け表示")
        
        self.action_mode_btn = QPushButton("行動別色分け")
        self.action_mode_btn.setCheckable(True)
        self.action_mode_btn.setToolTip("行動種別（Sit/Stand/Milk/Water/Food）で色分け表示")
        
        # ボタングループ（排他的選択）
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.id_mode_btn)
        self.button_group.addButton(self.action_mode_btn)
        
        # レイアウトに追加
        group_layout.addWidget(self.id_mode_btn)
        group_layout.addWidget(self.action_mode_btn)
        
        # 現在のモード表示
        self.mode_label = QLabel("現在: ID別色分け")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.mode_label.setFont(font)
        group_layout.addWidget(self.mode_label)
        
        layout.addWidget(group)
        
        # シグナル接続
        self.id_mode_btn.clicked.connect(lambda: self.set_color_mode('id'))
        self.action_mode_btn.clicked.connect(lambda: self.set_color_mode('action'))
        
    def set_color_mode(self, mode: str):
        """色分けモード設定"""
        if mode not in ['id', 'action']:
            return
            
        self.current_mode = mode
        
        # ボタン状態更新
        if mode == 'id':
            self.id_mode_btn.setChecked(True)
            self.mode_label.setText("現在: ID別色分け")
        else:
            self.action_mode_btn.setChecked(True)
            self.mode_label.setText("現在: 行動別色分け")
            
        # シグナル発信
        self.color_mode_changed.emit(mode)
        
    def get_color_mode(self) -> str:
        """現在の色分けモード取得"""
        return self.current_mode
        
    def toggle_mode(self):
        """モード切り替え（ショートカット用）"""
        new_mode = 'action' if self.current_mode == 'id' else 'id'
        self.set_color_mode(new_mode)