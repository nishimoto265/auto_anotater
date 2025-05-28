import sys
from PyQt6.QtWidgets import (QDialog, QFileDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QProgressBar, 
                            QListWidget, QMessageBox, QSpinBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer

class StartupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("起動オプション選択")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.video_button = QPushButton("動画から開始")
        self.frames_button = QPushButton("フレームから開始")
        self.resume_button = QPushButton("前回の続きから")
        
        layout.addWidget(self.video_button)
        layout.addWidget(self.frames_button)
        layout.addWidget(self.resume_button)
        
        self.setLayout(layout)
        
        self.video_button.clicked.connect(lambda: self.done(1))
        self.frames_button.clicked.connect(lambda: self.done(2))
        self.resume_button.clicked.connect(lambda: self.done(3))

class VideoSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("動画選択と設定")
        
        layout = QVBoxLayout()
        
        # 動画リスト
        self.video_list = QListWidget()
        self.video_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        layout.addWidget(self.video_list)
        
        # 動画追加ボタン
        add_button = QPushButton("動画追加")
        add_button.clicked.connect(self.add_videos)
        layout.addWidget(add_button)
        
        # 開始番号設定
        number_layout = QHBoxLayout()
        number_layout.addWidget(QLabel("開始番号:"))
        self.start_number = QSpinBox()
        self.start_number.setRange(0, 999999)
        self.start_number.setFixedWidth(100)
        number_layout.addWidget(self.start_number)
        layout.addLayout(number_layout)
        
        # 確定ボタン
        ok_button = QPushButton("確定")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        self.setLayout(layout)
    
    def add_videos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "動画ファイルを選択", "", "動画ファイル (*.mp4 *.avi)"
        )
        self.video_list.addItems(files)

class OutputFolderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("フレーム出力先選択")
        
        layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        browse_button = QPushButton("参照...")
        browse_button.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)
        
        ok_button = QPushButton("確定")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        self.setLayout(layout)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "出力フォルダを選択")
        if folder:
            self.path_edit.setText(folder)

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("処理中...")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("処理中...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
    
    def update_progress(self, value, status=""):
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)

def show_error(parent, message, title="エラー"):
    QMessageBox.critical(parent, title, message)

def show_warning(parent, message, title="警告"):
    QMessageBox.warning(parent, title, message)

def show_info(parent, message, title="情報"):
    QMessageBox.information(parent, title, message)

def confirm_dialog(parent, message, title="確認"):
    reply = QMessageBox.question(parent, title, message,
                               QMessageBox.StandardButton.Yes | 
                               QMessageBox.StandardButton.No)
    return reply == QMessageBox.StandardButton.Yes