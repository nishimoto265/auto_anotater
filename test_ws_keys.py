#!/usr/bin/env python3
"""
W/Sキー機能テスト（BB作成・削除）
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

def test_ws_keys():
    """W/Sキー機能テスト"""
    app = QApplication(sys.argv)
    
    # テスト用データ
    project_info = (
        "images",
        "/media/thithilab/volume/auto_anotatation/data/frames",
        {
            "name": "WS Key Test",
            "output_directory": "",
            "annotation_directory": "/media/thithilab/volume/auto_anotatation/test_annotations"
        }
    )
    
    print("Creating MainWindow...")
    window = MainWindow(project_info=project_info)
    window.show()
    
    # ウィンドウをアクティブにして初期化完了まで待機
    window.activateWindow()
    window.raise_()
    QTest.qWait(1000)
    
    print("\n=== W/Sキー機能テスト ===")
    
    # フォーカスをメインウィンドウに確実に設定
    window.setFocus()
    QTest.qWait(100)
    
    # 現在のアノテーション数表示
    print(f"Initial annotations: {len(window.current_annotations)}")
    print(f"Annotation output dir: {window.annotation_output_dir}")
    
    # Wキーテスト（BB作成モード切り替え）
    print("\n1. Testing W key (BB creation mode)...")
    for i in range(3):
        print(f"  - Press W #{i+1}")
        QTest.keyPress(window, Qt.Key.Key_W)
        QTest.qWait(300)
    
    # 手動でBB作成をシミュレート
    print("\n2. Simulating BB creation...")
    try:
        # on_bb_created メソッドを直接呼び出し
        window.on_bb_created(0.5, 0.3, 0.1, 0.15)  # 中央付近に小さなBB
        window.on_bb_created(0.2, 0.7, 0.08, 0.12)  # 左下に別のBB
        print(f"  Created 2 BBs. Current count: {len(window.current_annotations)}")
    except Exception as e:
        print(f"  Error creating BB: {e}")
    
    QTest.qWait(500)
    
    # Sキーテスト（BB削除）
    print("\n3. Testing S key (BB deletion)...")
    initial_count = len(window.current_annotations)
    for i in range(3):
        print(f"  - Press S #{i+1}")
        QTest.keyPress(window, Qt.Key.Key_S)
        QTest.qWait(300)
        current_count = len(window.current_annotations)
        print(f"    BB count: {initial_count} -> {current_count}")
        initial_count = current_count
    
    # アノテーションファイル確認
    print("\n4. Checking annotation files...")
    if window.annotation_output_dir:
        frame_file = os.path.join(window.annotation_output_dir, "000000.txt")
        if os.path.exists(frame_file):
            print(f"  Annotation file exists: {frame_file}")
            with open(frame_file, 'r') as f:
                content = f.read().strip()
                if content:
                    print(f"  File content:\n{content}")
                else:
                    print("  File is empty (no BBs)")
        else:
            print(f"  No annotation file found: {frame_file}")
    
    # 最終状態表示
    print(f"\nFinal state:")
    print(f"  Annotations in memory: {len(window.current_annotations)}")
    print(f"  Output directory: {window.annotation_output_dir}")
    
    # ショートカット統計確認
    if hasattr(window, 'keyboard_handler'):
        print(f"\nShortcut statistics:")
        for key, action in window.keyboard_handler.actions.items():
            print(f"  {key}: {action.call_count} times executed")
    
    print("\nTest completed!")
    
    # 3秒後に終了
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(3000)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_ws_keys())