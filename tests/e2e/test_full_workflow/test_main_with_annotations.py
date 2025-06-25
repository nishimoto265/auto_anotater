#!/usr/bin/env python3
"""
メインアプリケーションのBB表示テスト - アノテーション付き
"""

import sys
import os
sys.path.append('/media/thithilab/volume/auto_anotatation/src')

from PyQt6.QtWidgets import QApplication

def test_main_with_annotations():
    """メインアプリケーションでBB表示テスト"""
    app = QApplication(sys.argv)
    
    print("=== Main Application with Annotations Test ===")
    
    # プロジェクト情報を手動設定（画像プロジェクト）
    project_info = (
        "images",
        "/media/thithilab/volume/auto_anotatation/data/frames",
        {
            'name': 'Test Project with Annotations',
            'output_directory': '/media/thithilab/volume/auto_anotatation/data/frames',
            'annotation_directory': '/media/thithilab/volume/auto_anotatation/data/annotations'
        }
    )
    
    print(f"Project info: {project_info}")
    
    # メインウィンドウ作成
    from presentation.main_window.main_window import MainWindow
    
    window = MainWindow(project_info=project_info)
    
    # ウィンドウを表示
    window.show()
    
    print("Main window should be displayed with BBs visible from startup.")
    print("Check if BBs are displayed on the canvas.")
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    test_main_with_annotations()