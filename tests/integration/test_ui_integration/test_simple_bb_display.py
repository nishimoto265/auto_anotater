#!/usr/bin/env python3
"""
簡単なBB表示テスト - プロジェクト読み込み無しでテスト
"""

import sys
import os
sys.path.append('/media/thithilab/volume/auto_anotatation/src')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

def test_simple_bb_display():
    """シンプルなBB表示テスト"""
    app = QApplication(sys.argv)
    
    print("=== Simple BB Display Test ===")
    
    # メインウィンドウ作成（プロジェクト情報なし）
    from presentation.main_window.main_window import MainWindow
    
    main_window = MainWindow()
    
    # アノテーションディレクトリを手動設定
    main_window.annotation_output_dir = "/media/thithilab/volume/auto_anotatation/test_annotations"
    print(f"Set annotation_output_dir: {main_window.annotation_output_dir}")
    
    # フレーム0を手動設定
    main_window.current_frame = 0
    
    # フレーム画像を手動読み込み
    frame_path = "/media/thithilab/volume/auto_anotatation/data/frames/000000.jpg"
    if os.path.exists(frame_path):
        success = main_window.bb_canvas.load_frame(frame_path)
        print(f"Frame loaded: {success}")
        
        # アノテーションを手動読み込み
        main_window.load_current_annotations()
        print(f"Loaded {len(main_window.current_annotations)} annotations")
        
        # BBを表示
        if main_window.current_annotations:
            print("Updating bounding boxes...")
            for i, bb in enumerate(main_window.current_annotations[:3]):
                print(f"BB {i}: {bb}")
            main_window.bb_canvas.update_bounding_boxes(main_window.current_annotations)
            print("BB update complete")
            
            # BBリストパネルも更新
            if hasattr(main_window, 'bb_list_panel'):
                main_window.bb_list_panel.update_bb_list(main_window.current_annotations)
                print("BB list panel updated")
        else:
            print("No annotations to display")
    else:
        print(f"Frame file not found: {frame_path}")
    
    main_window.show()
    
    # 3秒後に状態確認
    def check_status():
        print("\n=== Status Check ===")
        canvas = main_window.bb_canvas
        print(f"Canvas current_bbs: {len(canvas.current_bbs)}")
        print(f"Scene items: {len(canvas.scene.items())}")
        
        if hasattr(canvas, 'bb_renderer'):
            renderer = canvas.bb_renderer
            print(f"Renderer items: {len(renderer.rendered_items)}")
            
        # シーンアイテムの詳細
        for i, item in enumerate(canvas.scene.items()):
            print(f"Scene item {i}: {type(item).__name__}")
            if hasattr(item, 'bb_entity'):
                print(f"  BB entity: {item.bb_entity.id}")
    
    QTimer.singleShot(3000, check_status)
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    test_simple_bb_display()