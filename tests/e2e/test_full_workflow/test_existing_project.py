#!/usr/bin/env python3
"""
既存プロジェクト（途中から）テスト
"""

import sys
import os
sys.path.append('/media/thithilab/volume/auto_anotatation/src')

from PyQt6.QtWidgets import QApplication

def test_existing_project_flow():
    """既存プロジェクトのフローをテスト"""
    app = QApplication(sys.argv)
    
    print("=== Existing Project Flow Test ===")
    
    # 「途中から」を選択した場合の設定を模擬
    project_info = (
        "images",  # プロジェクトタイプ（ダイアログから返される）
        "/media/thithilab/volume/auto_anotatation/data/frames",  # 画像ディレクトリ
        {
            'name': 'Existing Project Test',
            'description': '',
            'source_type': 'images',
            'source_path': '/media/thithilab/volume/auto_anotatation/data/frames',
            'output_directory': '/media/thithilab/volume/auto_anotatation/data/frames',
            'annotation_directory': '/media/thithilab/volume/auto_anotatation/data/annotations'  # ここが重要！
        }
    )
    
    print("=== Project Configuration ===")
    print(f"Type: {project_info[0]}")
    print(f"Path: {project_info[1]}")
    print(f"Config: {project_info[2]}")
    print()
    
    # メインウィンドウ作成
    from presentation.main_window.main_window import MainWindow
    
    window = MainWindow(project_info=project_info)
    window.show()
    
    print("Window displayed. Check if BBs are visible from startup!")
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    test_existing_project_flow()