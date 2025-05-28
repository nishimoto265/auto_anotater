import sys
from PyQt6.QtWidgets import (QWidget, QGridLayout, QVBoxLayout, 
                           QPushButton, QLabel, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

class IdPanel(QWidget):
    id_selected = pyqtSignal(int)
    action_selected = pyqtSignal(str)
    
    def __init__(self, config_manager, color_manager):
        super().__init__()
        self.config = config_manager
        self.colors = color_manager
        
        self.selected_id = None
        self.selected_action = None
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 現在の選択表示
        self.info_label = QLabel("選択中: なし")
        layout.addWidget(self.info_label)
        
        # ID選択グリッド (4x4)
        id_grid = QGridLayout()
        for i in range(16):
            btn = QPushButton(str(i))
            btn.setFixedSize(50, 50)
            btn.clicked.connect(lambda x, id=i: self.on_id_selected(id))
            color = self.colors.get_id_color(i)
            self.set_button_color(btn, color)
            id_grid.addWidget(btn, i//4, i%4)
        layout.addLayout(id_grid)
        
        # 行動選択スクロールエリア
        scroll = QScrollArea()
        action_widget = QWidget()
        self.action_layout = QVBoxLayout(action_widget)
        
        for action in self.config.get_actions():
            self.add_action_button(action)
            
        scroll.setWidget(action_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
        
    def add_action_button(self, action):
        btn = QPushButton(action)
        btn.clicked.connect(lambda: self.on_action_selected(action))
        self.action_layout.addWidget(btn)
        
    def on_id_selected(self, id):
        self.selected_id = id
        self.update_info_label()
        self.id_selected.emit(id)
        
    def on_action_selected(self, action):
        self.selected_action = action
        self.update_info_label()
        self.action_selected.emit(action)
        
    def update_info_label(self):
        text = "選択中: "
        if self.selected_id is not None:
            text += f"ID {self.selected_id} "
        if self.selected_action:
            text += f"/ {self.selected_action}"
        self.info_label.setText(text)
        
    def set_button_color(self, button, color):
        palette = button.palette()
        palette.setColor(QPalette.ColorRole.Button, QColor(color))
        button.setPalette(palette)
        button.setAutoFillBackground(True)
        
    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key_0 <= key <= Qt.Key_9:
            id = key - Qt.Key_0
            self.on_id_selected(id)
        elif Qt.Key_A <= key <= Qt.Key_F:
            id = key - Qt.Key_A + 10
            self.on_id_selected(id)
        super().keyPressEvent(event)

    def update_from_bb_selection(self, bb_data):
        if bb_data:
            self.selected_id = bb_data.id
            self.selected_action = bb_data.action
            self.update_info_label()