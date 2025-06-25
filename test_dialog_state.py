#!/usr/bin/env python3
"""
ダイアログの状態をチェック（非インタラクティブ）
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

def test_dialog_states():
    app = QApplication(sys.argv)
    
    dialog = ProjectStartupDialog()
    
    print("=== Initial State (Video Selected) ===")
    print(f"video_radio.isChecked(): {dialog.video_radio.isChecked()}")
    print(f"existing_images_label.isVisible(): {dialog.existing_images_label.isVisible()}")
    print(f"existing_images_edit.isVisible(): {dialog.existing_images_edit.isVisible()}")
    
    print("\n=== After Switching to Existing ===")
    dialog.existing_radio.setChecked(True)
    print(f"existing_radio.isChecked(): {dialog.existing_radio.isChecked()}")
    print(f"existing_images_label.isVisible(): {dialog.existing_images_label.isVisible()}")
    print(f"existing_images_edit.isVisible(): {dialog.existing_images_edit.isVisible()}")
    print(f"existing_images_browse_btn.isVisible(): {dialog.existing_images_browse_btn.isVisible()}")
    
    print("\n=== After Switching Back to Video ===")
    dialog.video_radio.setChecked(True)
    print(f"video_radio.isChecked(): {dialog.video_radio.isChecked()}")
    print(f"existing_images_label.isVisible(): {dialog.existing_images_label.isVisible()}")
    print(f"existing_images_edit.isVisible(): {dialog.existing_images_edit.isVisible()}")
    
    print("\n=== Final Switch to Existing ===")
    dialog.existing_radio.setChecked(True)
    print(f"existing_radio.isChecked(): {dialog.existing_radio.isChecked()}")
    print(f"existing_images_label.isVisible(): {dialog.existing_images_label.isVisible()}")
    print(f"existing_images_edit.isVisible(): {dialog.existing_images_edit.isVisible()}")
    
    # Show dialog briefly
    dialog.show()
    
    # Close after 2 seconds
    QTimer.singleShot(2000, lambda: (
        print("\n=== Final visibility check in dialog ==="),
        print(f"Label visible: {dialog.existing_images_label.isVisible()}"),
        print(f"Edit visible: {dialog.existing_images_edit.isVisible()}"),
        print(f"Button visible: {dialog.existing_images_browse_btn.isVisible()}"),
        app.quit()
    ))
    
    app.exec()

if __name__ == "__main__":
    test_dialog_states()