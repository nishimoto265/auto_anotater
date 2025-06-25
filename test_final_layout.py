#!/usr/bin/env python3
"""
最終的なレイアウトテスト
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

def main():
    app = QApplication(sys.argv)
    
    dialog = ProjectStartupDialog()
    dialog.show()
    
    # 既存プロジェクトを選択
    def test_layout():
        print("=== Testing layout ===")
        
        # 既存を選択
        dialog.existing_radio.setChecked(True)
        
        print(f"Existing radio checked: {dialog.existing_radio.isChecked()}")
        print(f"Images container visible: {dialog.existing_images_container.isVisible()}")
        print(f"Images edit visible: {dialog.existing_images_edit.isVisible()}")
        
        print("\n確認ポイント:")
        print("1. アノテーションディレクトリ選択欄の下に画像ディレクトリ選択欄が表示")
        print("2. ラベルなしで、同じインデントレベル")
        print("3. プレースホルダーに「対応する画像ディレクトリを選択...」と表示")
    
    # 0.5秒後にテスト実行
    QTimer.singleShot(500, test_layout)
    
    # 10秒後に終了
    QTimer.singleShot(10000, app.quit)
    
    app.exec()

if __name__ == "__main__":
    main()