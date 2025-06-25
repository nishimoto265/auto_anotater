#!/usr/bin/env python3
"""
BB表示デバッグテスト - 既存BBが表示されない問題の調査
"""

import sys
import os
sys.path.append('/media/thithilab/volume/auto_anotatation/src')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

def test_bb_display():
    """BB表示テスト"""
    app = QApplication(sys.argv)
    
    # プロジェクト情報設定（テスト用）
    project_info = (
        "existing",  # project_type
        "/media/thithilab/volume/auto_anotatation/demo_project/project.json",  # project_path
        {
            'name': 'Test Project',
            'images_directory': '/media/thithilab/volume/auto_anotatation/data/frames',
            'annotation_directory': '/media/thithilab/volume/auto_anotatation/test_annotations'
        }
    )
    
    print("=== BB Display Debug Test ===")
    print(f"Project type: {project_info[0]}")
    print(f"Project path: {project_info[1]}")
    print(f"Project config: {project_info[2]}")
    
    # メインウィンドウ作成
    from presentation.main_window.main_window import MainWindow
    
    main_window = MainWindow(project_info=project_info)
    main_window.show()
    
    # 5秒後に詳細情報を表示
    def show_debug_info():
        print("\n=== Debug Info After 5 seconds ===")
        print(f"annotation_output_dir: {getattr(main_window, 'annotation_output_dir', 'NOT SET')}")
        print(f"current_annotations count: {len(getattr(main_window, 'current_annotations', []))}")
        print(f"current_frame: {getattr(main_window, 'current_frame', 'NOT SET')}")
        
        if hasattr(main_window, 'current_annotations'):
            for i, bb in enumerate(main_window.current_annotations[:3]):
                print(f"BB {i}: {bb}")
                
        if hasattr(main_window, 'bb_canvas'):
            canvas = main_window.bb_canvas
            print(f"Canvas current_bbs count: {len(getattr(canvas, 'current_bbs', []))}")
            print(f"Canvas scene items count: {len(canvas.scene.items()) if canvas.scene else 'NO SCENE'}")
            
            if hasattr(canvas, 'bb_renderer'):
                renderer = canvas.bb_renderer
                print(f"Renderer rendered_items count: {len(getattr(renderer, 'rendered_items', []))}")
                
        # アノテーションファイルの直接確認
        annotation_file = "/media/thithilab/volume/auto_anotatation/test_annotations/000000.txt"
        if os.path.exists(annotation_file):
            print(f"Annotation file exists: {annotation_file}")
            with open(annotation_file, 'r') as f:
                lines = f.readlines()
                print(f"Annotation file lines: {len(lines)}")
                for i, line in enumerate(lines[:3]):
                    print(f"Line {i}: {line.strip()}")
        else:
            print(f"Annotation file NOT found: {annotation_file}")
    
    QTimer.singleShot(5000, show_debug_info)
    
    # 10秒後に強制BB作成テスト
    def test_bb_creation():
        print("\n=== Testing BB Creation ===")
        if hasattr(main_window, 'bb_canvas'):
            # 手動でBBを作成してみる
            test_bb = {
                'id': 'test_bb_manual',
                'x': 0.5,
                'y': 0.5,
                'w': 0.1,
                'h': 0.1,
                'individual_id': 1,
                'action_id': 0,
                'confidence': 1.0
            }
            
            main_window.current_annotations.append(test_bb)
            main_window.bb_canvas.update_bounding_boxes(main_window.current_annotations)
            print(f"Manually added test BB. Total BBs: {len(main_window.current_annotations)}")
    
    QTimer.singleShot(10000, test_bb_creation)
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    test_bb_display()