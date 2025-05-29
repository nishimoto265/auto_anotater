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

class TrackingParametersDialog(QDialog):
    def __init__(self, tracking_system, parent=None):
        super().__init__(parent)
        self.tracking_system = tracking_system
        self.setWindowTitle("追跡パラメータ設定")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # テンプレートサイズ
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("テンプレートサイズ:"))
        self.template_size_spin = QSpinBox()
        self.template_size_spin.setRange(16, 128)
        self.template_size_spin.setSingleStep(8)
        self.template_size_spin.setValue(self.tracking_system.template_size[0])
        template_layout.addWidget(self.template_size_spin)
        template_layout.addWidget(QLabel("x"))
        self.template_size_spin2 = QSpinBox()
        self.template_size_spin2.setRange(16, 128)
        self.template_size_spin2.setSingleStep(8)
        self.template_size_spin2.setValue(self.tracking_system.template_size[1])
        template_layout.addWidget(self.template_size_spin2)
        layout.addLayout(template_layout)
        
        # 最大ロストフレーム数
        lost_layout = QHBoxLayout()
        lost_layout.addWidget(QLabel("最大ロストフレーム数:"))
        self.max_lost_frames_spin = QSpinBox()
        self.max_lost_frames_spin.setRange(1, 50)
        self.max_lost_frames_spin.setValue(self.tracking_system.max_lost_frames)
        lost_layout.addWidget(self.max_lost_frames_spin)
        layout.addLayout(lost_layout)
        
        # 最小信頼度
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(QLabel("最小信頼度:"))
        self.min_confidence_spin = QSpinBox()
        self.min_confidence_spin.setRange(1, 99)
        self.min_confidence_spin.setValue(int(self.tracking_system.min_confidence * 100))
        confidence_layout.addWidget(self.min_confidence_spin)
        confidence_layout.addWidget(QLabel("%"))
        layout.addLayout(confidence_layout)
        
        # 特徴点パラメータ
        feature_group = QVBoxLayout()
        feature_group.addWidget(QLabel("特徴点検出パラメータ:"))
        
        corners_layout = QHBoxLayout()
        corners_layout.addWidget(QLabel("  最大コーナー数:"))
        self.max_corners_spin = QSpinBox()
        self.max_corners_spin.setRange(10, 100)
        self.max_corners_spin.setValue(self.tracking_system.feature_params['maxCorners'])
        corners_layout.addWidget(self.max_corners_spin)
        feature_group.addLayout(corners_layout)
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("  品質レベル:"))
        self.quality_level_spin = QSpinBox()
        self.quality_level_spin.setRange(1, 99)
        self.quality_level_spin.setValue(int(self.tracking_system.feature_params['qualityLevel'] * 100))
        quality_layout.addWidget(self.quality_level_spin)
        quality_layout.addWidget(QLabel("%"))
        feature_group.addLayout(quality_layout)
        
        layout.addLayout(feature_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def accept(self):
        # パラメータを更新
        self.tracking_system.template_size = (
            self.template_size_spin.value(),
            self.template_size_spin2.value()
        )
        self.tracking_system.max_lost_frames = self.max_lost_frames_spin.value()
        self.tracking_system.min_confidence = self.min_confidence_spin.value() / 100.0
        self.tracking_system.feature_params['maxCorners'] = self.max_corners_spin.value()
        self.tracking_system.feature_params['qualityLevel'] = self.quality_level_spin.value() / 100.0
        
        super().accept()