#!/usr/bin/env python3
"""
UIの変更をテストするスクリプト
BBコピーと追跡機能の分離、ボタンの有効/無効状態を確認
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from presentation.control_panels.bb_copy_panel import BBCopyPanel
from presentation.control_panels.bb_tracking_panel import BBTrackingPanel
from presentation.control_panels.continuous_mode_panel import ContinuousModePanel


class TestWindow(QMainWindow):
    """テスト用メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """UI構築"""
        self.setWindowTitle("UI変更テスト")
        self.setGeometry(100, 100, 400, 600)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 各パネルを追加
        self.continuous_panel = ContinuousModePanel()
        self.bb_copy_panel = BBCopyPanel()
        self.bb_tracking_panel = BBTrackingPanel()
        
        layout.addWidget(self.continuous_panel)
        layout.addWidget(self.bb_copy_panel)
        layout.addWidget(self.bb_tracking_panel)
        
        # テスト用ボタン
        test_btn = QPushButton("BBを選択（テスト）")
        test_btn.clicked.connect(self.simulate_bb_selection)
        layout.addWidget(test_btn)
        
        clear_btn = QPushButton("選択をクリア（テスト）")
        clear_btn.clicked.connect(self.simulate_bb_clear)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        
        # 初期状態の確認
        print("初期状態:")
        print(f"- BBコピーボタン有効: {self.bb_copy_panel.copy_range_btn.isEnabled()}")
        print(f"- 追跡ボタン有効: {self.bb_tracking_panel.track_forward_btn.isEnabled()}")
        
        # シグナル接続
        self.continuous_panel.continuous_mode_changed.connect(
            lambda enabled: print(f"連続モード: {enabled}")
        )
        self.bb_copy_panel.copy_bb_to_range.connect(
            lambda start, end: print(f"範囲コピー: {start} -> {end}")
        )
        self.bb_tracking_panel.track_forward.connect(
            lambda max_frames: print(f"追跡開始: 最大{max_frames}フレーム")
        )
        
    def simulate_bb_selection(self):
        """BB選択をシミュレート"""
        print("\nBB選択をシミュレート")
        self.bb_copy_panel.set_selection_state(True)
        self.bb_tracking_panel.set_selection_state(True)
        print(f"- BBコピーボタン有効: {self.bb_copy_panel.copy_range_btn.isEnabled()}")
        print(f"- 追跡ボタン有効: {self.bb_tracking_panel.track_forward_btn.isEnabled()}")
        
    def simulate_bb_clear(self):
        """BB選択解除をシミュレート"""
        print("\nBB選択解除をシミュレート")
        self.bb_copy_panel.set_selection_state(False)
        self.bb_tracking_panel.set_selection_state(False)
        print(f"- BBコピーボタン有効: {self.bb_copy_panel.copy_range_btn.isEnabled()}")
        print(f"- 追跡ボタン有効: {self.bb_tracking_panel.track_forward_btn.isEnabled()}")


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("\n=== UIテスト開始 ===")
    print("1. 初期状態でボタンが無効になっていることを確認")
    print("2. 'BBを選択'ボタンをクリックしてボタンが有効になることを確認")
    print("3. '選択をクリア'ボタンをクリックしてボタンが無効になることを確認")
    print("4. 各パネルが独立して表示されていることを確認")
    print("\n※ 連続モード、BBコピー、追跡が別々のグループになっていることを確認してください")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()