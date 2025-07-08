"""
BB追跡パネル
選択したBBを後続フレームで追跡してIDを付ける機能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, 
    QLabel, QGroupBox, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, Qt


class BBTrackingPanel(QWidget):
    """
    BB追跡パネル
    
    機能:
    - 選択BBを後続フレームで追跡
    - 追跡が途切れるまで同じIDを付ける
    - 追跡設定のカスタマイズ
    """
    
    # シグナル定義
    track_forward = pyqtSignal(int)  # 追跡フレーム数
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # グループボックス
        group = QGroupBox("BB追跡でID付け")
        group_layout = QVBoxLayout(group)
        
        # 説明ラベル
        desc_label = QLabel(
            "選択したBBを後続フレームで追跡し、\n"
            "追跡が途切れるまで同じIDを付けます"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px;")
        group_layout.addWidget(desc_label)
        
        # 追跡フレーム数設定
        frame_layout = QVBoxLayout()
        frame_layout.addWidget(QLabel("最大追跡フレーム数:"))
        self.max_frames_spin = QSpinBox()
        self.max_frames_spin.setMinimum(1)
        self.max_frames_spin.setMaximum(100)
        self.max_frames_spin.setValue(30)
        self.max_frames_spin.setToolTip(
            "追跡を続ける最大フレーム数\n"
            "（途中で追跡が失敗した場合は停止）"
        )
        frame_layout.addWidget(self.max_frames_spin)
        
        group_layout.addLayout(frame_layout)
        
        # 追跡実行ボタン
        self.track_forward_btn = QPushButton("追跡でID付け")
        self.track_forward_btn.setToolTip(
            "選択したBBを後続フレームで追跡し、\n"
            "追跡が途切れるまで同じIDを付けます\n"
            "※IOU閾値: 0.3以上で追跡継続"
        )
        self.track_forward_btn.setEnabled(False)
        group_layout.addWidget(self.track_forward_btn)
        
        # 追跡状態表示
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        group_layout.addWidget(self.status_label)
        
        layout.addWidget(group)
        
        # シグナル接続
        self.track_forward_btn.clicked.connect(self.on_track_forward_clicked)
        
    def on_track_forward_clicked(self):
        """追跡ボタンクリック"""
        max_frames = self.max_frames_spin.value()
        self.track_forward.emit(max_frames)
        
    def set_selection_state(self, has_selection: bool):
        """選択状態に応じてボタンを有効/無効化"""
        self.track_forward_btn.setEnabled(has_selection)
        
    def set_tracking_status(self, status: str):
        """追跡状態を表示"""
        self.status_label.setText(status)