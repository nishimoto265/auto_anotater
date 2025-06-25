#!/usr/bin/env python3
"""
修正されたフレーム表示機能のテスト
"""

import sys
import os
import time
from PyQt6.QtWidgets import QApplication

# パス追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from presentation.main_window.main_window import MainWindow

def test_fixed_frame_display():
    """修正されたフレーム表示テスト"""
    app = QApplication(sys.argv)
    
    # テスト用プロジェクト設定（フォールバック使用）
    project_info = (
        "video",  # プロジェクトタイプ
        "/dummy/video.mp4",  # ダミーパス
        {
            "name": "Frame Display Test",
            "output_directory": "",  # 空にしてフォールバック使用
            "target_fps": 5.0
        }
    )
    
    print("Creating MainWindow with fallback frame loading...")
    
    try:
        # メインウィンドウ作成
        start_time = time.time()
        window = MainWindow(project_info=project_info)
        setup_time = time.time() - start_time
        
        print(f"Window setup time: {setup_time:.2f}s")
        print(f"Total frames loaded: {getattr(window, 'total_frames', 0)}")
        
        # ウィンドウ表示
        window.show()
        
        # フレーム表示テスト
        if hasattr(window, 'bb_canvas') and hasattr(window, 'total_frames'):
            if window.total_frames > 0:
                print("SUCCESS: Frames loaded, testing display...")
                
                # フレーム選択テスト
                if hasattr(window, 'file_list_panel'):
                    window.file_list_panel.go_to_first_frame()
                    print("Navigated to first frame")
                    
                    time.sleep(1)  # 表示待機
                    
                    if window.total_frames > 1:
                        window.file_list_panel.go_to_next_frame()
                        print("Navigated to next frame")
                
                print("Frame display test completed successfully!")
            else:
                print("WARNING: No frames loaded")
        
        # 3秒後に自動終了
        from PyQt6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(3000)  # 3秒
        
        print("Window will auto-close in 3 seconds...")
        return app.exec()
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_fixed_frame_display())