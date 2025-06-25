#!/usr/bin/env python3
"""
手動でtoggleメソッドを呼んでテスト
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

def test_manual_toggle():
    app = QApplication(sys.argv)
    
    dialog = ProjectStartupDialog()
    
    print("=== Initial state ===")
    print(f"Label visible: {dialog.existing_images_label.isVisible()}")
    print(f"Edit visible: {dialog.existing_images_edit.isVisible()}")
    print(f"Button visible: {dialog.existing_images_browse_btn.isVisible()}")
    
    print("\n=== Calling toggle_existing_images_visibility(True) ===")
    dialog.toggle_existing_images_visibility(True)
    
    print(f"Label visible: {dialog.existing_images_label.isVisible()}")
    print(f"Edit visible: {dialog.existing_images_edit.isVisible()}")
    print(f"Button visible: {dialog.existing_images_browse_btn.isVisible()}")
    
    print("\n=== Calling toggle_existing_images_visibility(False) ===")
    dialog.toggle_existing_images_visibility(False)
    
    print(f"Label visible: {dialog.existing_images_label.isVisible()}")
    print(f"Edit visible: {dialog.existing_images_edit.isVisible()}")
    print(f"Button visible: {dialog.existing_images_browse_btn.isVisible()}")
    
    # ダイアログを表示
    dialog.show()
    
    # タイマーで順番に切り替え
    def step1():
        print("\n=== In dialog: Setting existing radio checked ===")
        dialog.existing_radio.setChecked(True)
        QTimer.singleShot(1000, step2)
    
    def step2():
        print(f"Label visible: {dialog.existing_images_label.isVisible()}")
        print(f"Edit visible: {dialog.existing_images_edit.isVisible()}")
        print("\n=== Manually calling on_project_type_changed ===")
        dialog.on_project_type_changed()
        QTimer.singleShot(1000, step3)
    
    def step3():
        print(f"Label visible: {dialog.existing_images_label.isVisible()}")
        print(f"Edit visible: {dialog.existing_images_edit.isVisible()}")
        QTimer.singleShot(1000, app.quit)
    
    QTimer.singleShot(500, step1)
    
    app.exec()

if __name__ == "__main__":
    test_manual_toggle()