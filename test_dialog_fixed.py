#!/usr/bin/env python3
"""
ダイアログの既存選択時の画像ディレクトリ表示をテスト
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt6.QtWidgets import QApplication
from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

def test_existing_selection():
    app = QApplication(sys.argv)
    
    dialog = ProjectStartupDialog()
    
    # 既存を選択
    dialog.existing_radio.setChecked(True)
    
    # 確認
    print("=== Dialog State After Existing Selection ===")
    print(f"existing_radio.isChecked(): {dialog.existing_radio.isChecked()}")
    print(f"existing_images_label exists: {hasattr(dialog, 'existing_images_label')}")
    print(f"existing_images_label.isVisible(): {dialog.existing_images_label.isVisible()}")
    print(f"existing_images_edit.isVisible(): {dialog.existing_images_edit.isVisible()}")
    print(f"existing_images_browse_btn.isVisible(): {dialog.existing_images_browse_btn.isVisible()}")
    
    # ダイアログを表示
    result = dialog.exec()
    
    if result:
        project_type, path, config = dialog.get_project_info()
        print(f"\nSelected: {project_type}")
        print(f"Config: {config}")
    
    sys.exit(0)

if __name__ == "__main__":
    test_existing_selection()