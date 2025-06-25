"""
色設定ダイアログ - 個体IDまたは行動IDベースの色設定

機能:
- 個体ID基準 vs 行動ID基準の選択
- カラーパレット表示・変更
- プリセット色設定
- リアルタイムプレビュー
"""

from typing import Dict, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QRadioButton, QButtonGroup,
    QFrame, QColorDialog, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap, QPainter


class ColorButton(QPushButton):
    """色選択ボタン"""
    
    color_changed = pyqtSignal(QColor)
    
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self.current_color = color
        self.setFixedSize(40, 30)
        self.update_color_display()
        
    def update_color_display(self):
        """色表示を更新"""
        # ボタンの背景色を設定
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({self.current_color.red()}, {self.current_color.green()}, {self.current_color.blue()});
                border: 2px solid black;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                border: 3px solid black;
            }}
        """)
        
    def mousePressEvent(self, event):
        """マウスクリックで色選択ダイアログを開く"""
        color = QColorDialog.getColor(self.current_color, self, "色を選択")
        if color.isValid():
            self.current_color = color
            self.update_color_display()
            self.color_changed.emit(color)
        super().mousePressEvent(event)


class ColorSettingsDialog(QDialog):
    """色設定ダイアログ"""
    
    # シグナル定義
    color_mode_changed = pyqtSignal(str)  # "individual" or "action"
    colors_changed = pyqtSignal(dict)     # {id: QColor}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BB色設定")
        self.setFixedSize(500, 400)
        
        # 現在の設定
        self.color_mode = "individual"  # "individual" or "action"
        self.individual_colors = self.get_default_individual_colors()
        self.action_colors = self.get_default_action_colors()
        
        # UI構築
        self.setup_ui()
        
    def setup_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # タイトル
        title_label = QLabel("バウンディングボックスの色設定")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 色基準選択
        mode_group = self.create_mode_selection_group()
        layout.addWidget(mode_group)
        
        # 色設定エリア
        self.color_settings_area = QFrame()
        layout.addWidget(self.color_settings_area)
        
        # 初期表示
        self.update_color_settings_display()
        
        # ボタン
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("デフォルトに戻す")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        apply_btn = QPushButton("適用")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def create_mode_selection_group(self) -> QGroupBox:
        """色基準選択グループ作成"""
        group = QGroupBox("色の基準")
        layout = QVBoxLayout(group)
        
        self.mode_group = QButtonGroup()
        
        # 個体ID基準
        self.individual_radio = QRadioButton("個体ID基準（0-15）")
        self.individual_radio.setToolTip("各個体に固有の色を割り当て")
        self.individual_radio.setChecked(True)
        self.mode_group.addButton(self.individual_radio, 0)
        layout.addWidget(self.individual_radio)
        
        # 行動ID基準
        self.action_radio = QRadioButton("行動ID基準（Sit, Stand, Milk, Water, Food）")
        self.action_radio.setToolTip("各行動に固有の色を割り当て")
        self.mode_group.addButton(self.action_radio, 1)
        layout.addWidget(self.action_radio)
        
        # シグナル接続
        self.mode_group.buttonClicked.connect(self.on_mode_changed)
        
        return group
        
    def on_mode_changed(self, button):
        """色基準変更時の処理"""
        if button == self.individual_radio:
            self.color_mode = "individual"
        else:
            self.color_mode = "action"
            
        self.update_color_settings_display()
        
    def update_color_settings_display(self):
        """色設定表示を更新"""
        # 既存のレイアウトをクリア
        if self.color_settings_area.layout():
            for i in reversed(range(self.color_settings_area.layout().count())):
                self.color_settings_area.layout().itemAt(i).widget().deleteLater()
        
        if self.color_mode == "individual":
            self.create_individual_color_settings()
        else:
            self.create_action_color_settings()
            
    def create_individual_color_settings(self):
        """個体ID色設定作成"""
        layout = QGridLayout(self.color_settings_area)
        layout.setSpacing(5)
        
        title = QLabel("個体ID色設定（0-15）")
        title.setStyleSheet("font-weight: bold; margin: 5px;")
        layout.addWidget(title, 0, 0, 1, 4)
        
        # 16個体の色ボタンを4x4で配置
        self.individual_color_buttons = {}
        
        for i in range(16):
            row = i // 4 + 1
            col = i % 4
            
            # ラベル
            label = QLabel(f"ID {i}:")
            layout.addWidget(label, row, col * 2)
            
            # 色ボタン
            color_btn = ColorButton(self.individual_colors[i])
            color_btn.color_changed.connect(lambda color, id_num=i: self.on_individual_color_changed(id_num, color))
            self.individual_color_buttons[i] = color_btn
            layout.addWidget(color_btn, row, col * 2 + 1)
            
    def create_action_color_settings(self):
        """行動ID色設定作成"""
        layout = QVBoxLayout(self.color_settings_area)
        layout.setSpacing(10)
        
        title = QLabel("行動ID色設定")
        title.setStyleSheet("font-weight: bold; margin: 5px;")
        layout.addWidget(title)
        
        # 5行動の色設定
        action_names = ["Sit", "Stand", "Milk", "Water", "Food"]
        action_descriptions = ["座る", "立つ", "授乳", "水飲み", "食事"]
        
        self.action_color_buttons = {}
        
        for i, (name, desc) in enumerate(zip(action_names, action_descriptions)):
            row_layout = QHBoxLayout()
            
            # ラベル
            label = QLabel(f"{name} ({desc}):")
            label.setMinimumWidth(120)
            row_layout.addWidget(label)
            
            # 色ボタン
            color_btn = ColorButton(self.action_colors[i])
            color_btn.color_changed.connect(lambda color, action_id=i: self.on_action_color_changed(action_id, color))
            self.action_color_buttons[i] = color_btn
            row_layout.addWidget(color_btn)
            
            row_layout.addStretch()
            layout.addLayout(row_layout)
            
        layout.addStretch()
        
    def on_individual_color_changed(self, individual_id: int, color: QColor):
        """個体ID色変更"""
        self.individual_colors[individual_id] = color
        
    def on_action_color_changed(self, action_id: int, color: QColor):
        """行動ID色変更"""
        self.action_colors[action_id] = color
        
    def reset_to_defaults(self):
        """デフォルト色に戻す"""
        self.individual_colors = self.get_default_individual_colors()
        self.action_colors = self.get_default_action_colors()
        self.update_color_settings_display()
        
    def apply_settings(self):
        """設定を適用"""
        # 色モード変更シグナル
        self.color_mode_changed.emit(self.color_mode)
        
        # 色変更シグナル
        if self.color_mode == "individual":
            self.colors_changed.emit(self.individual_colors)
        else:
            self.colors_changed.emit(self.action_colors)
            
    def get_default_individual_colors(self) -> Dict[int, QColor]:
        """デフォルト個体ID色取得"""
        return {
            0: QColor(255, 0, 0),    # Red
            1: QColor(0, 255, 0),    # Green
            2: QColor(0, 0, 255),    # Blue
            3: QColor(255, 255, 0),  # Yellow
            4: QColor(255, 0, 255),  # Magenta
            5: QColor(0, 255, 255),  # Cyan
            6: QColor(255, 128, 0),  # Orange
            7: QColor(128, 0, 255),  # Purple
            8: QColor(255, 192, 203),# Pink
            9: QColor(165, 42, 42),  # Brown
            10: QColor(128, 128, 128),# Gray
            11: QColor(0, 128, 0),    # Dark Green
            12: QColor(0, 0, 128),    # Navy
            13: QColor(128, 128, 0),  # Olive
            14: QColor(128, 0, 128),  # Maroon
            15: QColor(0, 128, 128),  # Teal
        }
        
    def get_default_action_colors(self) -> Dict[int, QColor]:
        """デフォルト行動ID色取得"""
        return {
            0: QColor(0, 150, 0),      # Sit: Green
            1: QColor(100, 100, 255),  # Stand: Blue
            2: QColor(255, 200, 100),  # Milk: Orange
            3: QColor(0, 200, 255),    # Water: Cyan
            4: QColor(255, 100, 100),  # Food: Red
        }
        
    def get_current_colors(self) -> Dict[int, QColor]:
        """現在の色設定取得"""
        if self.color_mode == "individual":
            return self.individual_colors
        else:
            return self.action_colors
            
    def get_color_mode(self) -> str:
        """現在の色モード取得"""
        return self.color_mode


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    dialog = ColorSettingsDialog()
    dialog.show()
    
    sys.exit(app.exec())