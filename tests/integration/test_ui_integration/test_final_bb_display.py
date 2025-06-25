#!/usr/bin/env python3
"""
最終BB表示テスト - 問題が解決されたかを確認
"""

import sys
import os
sys.path.append('/media/thithilab/volume/auto_anotatation/src')

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def test_final_bb_display():
    """最終BB表示テスト"""
    app = QApplication(sys.argv)
    
    print("=== Final BB Display Test ===")
    print("This test will verify that BBs are displayed correctly from startup.")
    
    # プロジェクト情報設定
    project_info = (
        "existing",
        "/media/thithilab/volume/auto_anotatation/demo_project/project.json",
        {
            'name': 'Test Project',
            'images_directory': '/media/thithilab/volume/auto_anotatation/data/frames',
            'annotation_directory': '/media/thithilab/volume/auto_anotatation/test_annotations'
        }
    )
    
    # メインウィンドウ作成（実際のプロジェクト読み込みは避ける）
    from presentation.main_window.main_window import MainWindow
    
    main_window = MainWindow()
    
    # 手動設定
    main_window.annotation_output_dir = "/media/thithilab/volume/auto_anotatation/test_annotations"
    main_window.current_frame = 0
    
    # フレーム読み込み
    frame_path = "/media/thithilab/volume/auto_anotatation/data/frames/000000.jpg"
    if os.path.exists(frame_path):
        main_window.bb_canvas.load_frame(frame_path)
        main_window.load_current_annotations()
        
        if main_window.current_annotations:
            print(f"Loaded {len(main_window.current_annotations)} annotations")
            main_window.bb_canvas.update_bounding_boxes(main_window.current_annotations)
            
            if hasattr(main_window, 'bb_list_panel'):
                main_window.bb_list_panel.update_bb_list(main_window.current_annotations)
        else:
            print("No annotations loaded")
    else:
        print(f"Frame file not found: {frame_path}")
    
    # ウィンドウ表示
    main_window.show()
    
    def final_check():
        print("\n=== Final Status Check ===")
        canvas = main_window.bb_canvas
        
        total_items = len(canvas.scene.items())
        bb_items = [item for item in canvas.scene.items() if hasattr(item, 'bb_entity')]
        
        print(f"Scene items: {total_items}")
        print(f"BB items: {len(bb_items)}")
        print(f"Current annotations: {len(main_window.current_annotations)}")
        
        if bb_items:
            print(f"First BB: rect={bb_items[0].rect()}, visible={bb_items[0].isVisible()}")
            print(f"BB pen: {bb_items[0].pen().width()}px {bb_items[0].pen().color().name()}")
        
        print(f"Scene rect: {canvas.scene.sceneRect()}")
        print(f"View transform: scale({canvas.transform().m11():.2f}, {canvas.transform().m22():.2f})")
        
        # 結論
        if len(bb_items) == len(main_window.current_annotations) and len(bb_items) > 0:
            print("✅ SUCCESS: BBs are properly loaded and should be visible!")
        else:
            print("❌ ISSUE: BBs are not properly loaded")
    
    # 3秒後に最終チェック
    QTimer.singleShot(3000, final_check)
    
    # 5秒後に自動終了
    QTimer.singleShot(5000, app.quit)
    
    print("Window should be displayed. Check if BBs are visible...")
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    test_final_bb_display()