#!/usr/bin/env python3
"""
実際のキー押下テスト
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

def test_actual_keys():
    """実際のキー押下テスト"""
    app = QApplication(sys.argv)
    
    # テスト用データ
    project_info = (
        "images",
        "/media/thithilab/volume/auto_anotatation/data/frames",
        {
            "name": "Key Test",
            "output_directory": "",
        }
    )
    
    print("Creating MainWindow...")
    window = MainWindow(project_info=project_info)
    window.show()
    
    # ウィンドウをアクティブにして初期化完了まで待機
    window.activateWindow()
    window.raise_()
    QTest.qWait(1000)
    
    print("\n=== 実際のキー押下テスト ===")
    
    # フォーカスをメインウィンドウに確実に設定
    window.setFocus()
    QTest.qWait(100)
    
    # 現在のフレーム情報表示
    print(f"Initial frame: {getattr(window, 'current_frame', 'Unknown')}")
    
    # Dキーを押してみる
    print("Pressing D key (next frame)...")
    QTest.keyPress(window, Qt.Key.Key_D)
    QTest.qWait(200)
    print(f"Frame after D: {getattr(window, 'current_frame', 'Unknown')}")
    
    # Aキーを押してみる
    print("Pressing A key (previous frame)...")
    QTest.keyPress(window, Qt.Key.Key_A)
    QTest.qWait(200)
    print(f"Frame after A: {getattr(window, 'current_frame', 'Unknown')}")
    
    # Wキーを押してみる
    print("Pressing W key (BB creation mode)...")
    QTest.keyPress(window, Qt.Key.Key_W)
    QTest.qWait(200)
    
    # ショートカット統計確認
    if hasattr(window, 'keyboard_handler'):
        print(f"\nShortcuts executed: {window.keyboard_handler.total_shortcuts_executed}")
        
        # 各アクションの実行回数確認
        for key, action in window.keyboard_handler.actions.items():
            print(f"  {key}: {action.call_count} times")
    
    # 終了前にもう一度キーテスト
    print("\nSecond round of key tests...")
    QTest.keyPress(window, Qt.Key.Key_D)
    QTest.keyPress(window, Qt.Key.Key_D)
    QTest.qWait(500)
    
    if hasattr(window, 'keyboard_handler'):
        print(f"Final shortcuts executed: {window.keyboard_handler.total_shortcuts_executed}")
    
    print("Test completed!")
    
    # 2秒後に終了
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(2000)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_actual_keys())