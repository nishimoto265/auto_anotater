#!/usr/bin/env python3
"""
フレーム表示テスト - 画像が正しく表示されるかテスト
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap

# パス追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from presentation.bb_canvas.canvas_widget import BBCanvas

def test_frame_display():
    """フレーム表示テスト"""
    app = QApplication(sys.argv)
    
    # テストウィンドウ作成
    window = QMainWindow()
    window.setWindowTitle("Frame Display Test")
    window.resize(800, 600)
    
    # BBCanvas作成
    canvas = BBCanvas()
    
    # 中央ウィジェット設定
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    layout.addWidget(canvas)
    window.setCentralWidget(central_widget)
    
    # テスト用画像パス
    test_frame_path = "/media/thithilab/volume/auto_anotatation/data/frames/000000.jpg"
    
    print(f"Testing frame load: {test_frame_path}")
    print(f"File exists: {os.path.exists(test_frame_path)}")
    
    # フレーム読み込みテスト
    if os.path.exists(test_frame_path):
        success = canvas.load_frame(test_frame_path)
        print(f"Load result: {success}")
        
        if success:
            print("SUCCESS: Frame loaded and displayed")
        else:
            print("FAILED: Frame load failed")
    else:
        print("ERROR: Test frame file not found")
    
    # ウィンドウ表示
    window.show()
    
    # 5秒後に自動終了
    from PyQt6.QtCore import QTimer
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(5000)  # 5秒
    
    print("Window will auto-close in 5 seconds...")
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_frame_display())