#!/usr/bin/env python3
"""
ダイアログレイアウトのテスト
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
    
    # ダイアログを表示
    dialog.show()
    
    # 既存プロジェクトを選択
    def select_existing():
        print("=== Selecting existing project ===")
        dialog.existing_radio.setChecked(True)
        
        # 状態確認
        print(f"Existing radio checked: {dialog.existing_radio.isChecked()}")
        print(f"Image directory label visible: {dialog.existing_images_label.isVisible()}")
        print(f"Image directory edit visible: {dialog.existing_images_edit.isVisible()}")
        print(f"Image directory button visible: {dialog.existing_images_browse_btn.isVisible()}")
        print("\n画像ディレクトリ選択がアノテーションディレクトリの下に表示されているか確認してください")
    
    # 1秒後に既存プロジェクトを選択
    QTimer.singleShot(1000, select_existing)
    
    # 10秒後に終了
    QTimer.singleShot(10000, app.quit)
    
    app.exec()

if __name__ == "__main__":
    main()