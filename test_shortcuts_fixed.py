#!/usr/bin/env python3
"""
修正されたショートカット機能のテスト
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

def test_fixed_shortcuts():
    """修正されたショートカット機能のテスト"""
    app = QApplication(sys.argv)
    
    # テスト用プロジェクト設定（小さな画像セット）
    project_info = (
        "images",  # プロジェクトタイプ
        "/media/thithilab/volume/auto_anotatation/data/frames",  # 小さなサンプル
        {
            "name": "Shortcut Test",
            "output_directory": "",
            "target_fps": 5.0
        }
    )
    
    print("Creating MainWindow for shortcut testing...")
    
    try:
        # メインウィンドウ作成
        start_time = time.time()
        window = MainWindow(project_info=project_info)
        setup_time = time.time() - start_time
        
        print(f"Window setup time: {setup_time:.2f}s")
        print(f"Total frames loaded: {getattr(window, 'total_frames', 0)}")
        
        # ウィンドウ表示
        window.show()
        
        # 少し待機（初期化完了まで）
        QTest.qWait(500)
        
        # ショートカットテスト
        print("\n=== ショートカットテスト開始 ===")
        
        # 1. フレーム移動テスト（A, D）
        print("1. Testing frame navigation (A/D keys)...")
        for i in range(3):
            print(f"  - Pressing D (next frame)...")
            QTest.keyPress(window, Qt.Key.Key_D)
            QTest.qWait(100)
            
        for i in range(2):
            print(f"  - Pressing A (previous frame)...")
            QTest.keyPress(window, Qt.Key.Key_A)
            QTest.qWait(100)
            
        # 2. BB作成モードテスト（W）
        print("2. Testing BB creation mode (W key)...")
        QTest.keyPress(window, Qt.Key.Key_W)
        QTest.qWait(100)
        print("  - BB creation mode toggled")
        
        # 3. BB削除テスト（S）
        print("3. Testing BB deletion (S key)...")
        QTest.keyPress(window, Qt.Key.Key_S)
        QTest.qWait(100)
        print("  - BB deletion triggered")
        
        # 4. Undo機能テスト（Ctrl+Z）
        print("4. Testing undo (Ctrl+Z)...")
        QTest.keyPress(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        QTest.qWait(100)
        print("  - Undo triggered")
        
        # 5. キャンセル機能テスト（Escape）
        print("5. Testing cancel (Escape)...")
        QTest.keyPress(window, Qt.Key.Key_Escape)
        QTest.qWait(100)
        print("  - Cancel triggered")
        
        print("\n=== 全ショートカットテスト完了 ===")
        print("SUCCESS: All shortcuts processed without errors!")
        
        # キーボードハンドラーの統計情報表示
        if hasattr(window, 'keyboard_handler') and hasattr(window.keyboard_handler, 'get_performance_info'):
            stats = window.keyboard_handler.get_performance_info()
            print(f"\nPerformance Stats:")
            print(f"  Total shortcuts executed: {stats.get('total_executed', 0)}")
            print(f"  Average execution time: {stats.get('avg_execution_time', 0):.2f}ms")
            print(f"  Max execution time: {stats.get('max_execution_time', 0):.2f}ms")
        
        # 2秒後に自動終了
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(2000)
        
        print("Window will auto-close in 2 seconds...")
        return app.exec()
        
    except Exception as e:
        print(f"Error during shortcut test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_fixed_shortcuts())