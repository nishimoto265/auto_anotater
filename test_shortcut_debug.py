#!/usr/bin/env python3
"""
ショートカットデバッグテスト
"""

import sys
import os
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# パス追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from presentation.main_window.main_window import MainWindow

def test_shortcut_debug():
    """ショートカットデバッグテスト"""
    app = QApplication(sys.argv)
    
    # 小さなテスト用データ
    project_info = (
        "images",
        "/media/thithilab/volume/auto_anotatation/data/frames",
        {
            "name": "Debug Test",
            "output_directory": "",
        }
    )
    
    print("Creating MainWindow...")
    window = MainWindow(project_info=project_info)
    window.show()
    
    # 少し待機
    QTest.qWait(1000)
    
    print("\n=== ショートカットデバッグ ===")
    
    # キーボードハンドラーの状態確認
    if hasattr(window, 'keyboard_handler'):
        handler = window.keyboard_handler
        print(f"KeyboardHandler exists: {handler}")
        print(f"Actions registered: {list(handler.actions.keys())}")
        print(f"Shortcuts registered: {list(handler.shortcuts.keys())}")
        
        # 手動でアクション実行テスト
        print("\n=== 手動アクション実行テスト ===")
        for key in ['D', 'A', 'W']:
            if key in handler.actions:
                print(f"Testing action {key}...")
                try:
                    handler._execute_action(key)
                    print(f"  {key}: SUCCESS")
                except Exception as e:
                    print(f"  {key}: ERROR - {e}")
            else:
                print(f"  {key}: NOT REGISTERED")
    else:
        print("ERROR: KeyboardHandler not found!")
    
    # フレーム情報確認
    print(f"\nFrame info:")
    print(f"  Total frames: {getattr(window, 'total_frames', 'Not set')}")
    print(f"  Current frame: {getattr(window, 'current_frame', 'Not set')}")
    print(f"  Frame paths: {hasattr(window, 'frame_paths')}")
    
    # 2秒後に終了
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(2000)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_shortcut_debug())