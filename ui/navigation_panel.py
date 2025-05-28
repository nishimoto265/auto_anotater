import sys
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                           QLabel, QSpinBox, QProgressBar, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal

class NavigationPanel(QWidget):
    frameChanged = pyqtSignal(int)
    modeChanged = pyqtSignal(str)
    
    def __init__(self, frame_manager, progress_tracker):
        super().__init__()
        self.frame_manager = frame_manager
        self.progress_tracker = progress_tracker
        
        self.initUI()
        self.connectSignals()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # フレーム操作部分
        frame_controls = QHBoxLayout()
        
        self.prev_button = QPushButton("前へ")
        self.next_button = QPushButton("次へ")
        
        self.frame_counter = QSpinBox()
        self.frame_counter.setRange(0, 999999)
        self.frame_counter.setFixedWidth(100)
        
        self.total_frames = QLabel("/ 0")
        
        frame_controls.addWidget(self.prev_button)
        frame_controls.addWidget(self.frame_counter)
        frame_controls.addWidget(self.total_frames)
        frame_controls.addWidget(self.next_button)
        
        # 進捗バー
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("0%")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        # 操作モード
        mode_layout = QHBoxLayout()
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["通常モード", "バッチモード", "自動アノテーション"])
        mode_layout.addWidget(QLabel("モード:"))
        mode_layout.addWidget(self.mode_selector)
        
        # 変化フレームジャンプ
        jump_layout = QHBoxLayout()
        self.prev_change_button = QPushButton("前の変化")
        self.next_change_button = QPushButton("次の変化")
        jump_layout.addWidget(self.prev_change_button)
        jump_layout.addWidget(self.next_change_button)
        
        layout.addLayout(frame_controls)
        layout.addLayout(progress_layout)
        layout.addLayout(mode_layout)
        layout.addLayout(jump_layout)
        
        self.setLayout(layout)
        
    def connectSignals(self):
        self.prev_button.clicked.connect(self.onPrevFrame)
        self.next_button.clicked.connect(self.onNextFrame)
        self.frame_counter.valueChanged.connect(self.onFrameCounterChanged)
        self.mode_selector.currentTextChanged.connect(self.modeChanged.emit)
        self.prev_change_button.clicked.connect(self.onPrevChange)
        self.next_change_button.clicked.connect(self.onNextChange)
        
    def onPrevFrame(self):
        current = self.frame_counter.value()
        if current > 0:
            self.frame_counter.setValue(current - 1)
            
    def onNextFrame(self):
        current = self.frame_counter.value()
        max_frames = int(self.total_frames.text().strip('/'))
        if current < max_frames:
            self.frame_counter.setValue(current + 1)
            
    def onFrameCounterChanged(self, value):
        self.frameChanged.emit(value)
        
    def onPrevChange(self):
        change_frame = self.frame_manager.get_prev_change_frame()
        if change_frame is not None:
            self.frame_counter.setValue(change_frame)
            
    def onNextChange(self):
        change_frame = self.frame_manager.get_next_change_frame()
        if change_frame is not None:
            self.frame_counter.setValue(change_frame)
            
    def updateProgress(self, progress):
        self.progress_bar.setValue(int(progress * 100))
        self.progress_label.setText(f"{int(progress * 100)}%")
        
    def setTotalFrames(self, total):
        self.total_frames.setText(f"/ {total}")
        self.frame_counter.setRange(0, total)

    def getCurrentFrame(self):
        return self.frame_counter.value()
        
    def setCurrentFrame(self, frame):
        self.frame_counter.setValue(frame)