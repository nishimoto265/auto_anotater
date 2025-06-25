#!/usr/bin/env python3
"""
最終的なダイアログテスト
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
    
    def check_state():
        print("\n=== Current Dialog State ===")
        print(f"Video radio: {dialog.video_radio.isChecked()}")
        print(f"Image radio: {dialog.image_radio.isChecked()}")
        print(f"Existing radio: {dialog.existing_radio.isChecked()}")
        print(f"Label visible: {dialog.existing_images_label.isVisible()}")
        print(f"Edit visible: {dialog.existing_images_edit.isVisible()}")
        print(f"Button visible: {dialog.existing_images_browse_btn.isVisible()}")
    
    def test_sequence():
        print("=== Testing sequence ===")
        
        # Step 1: Check initial state
        print("\n1. Initial state (Video selected):")
        check_state()
        
        # Step 2: Switch to existing
        QTimer.singleShot(1000, lambda: (
            print("\n2. Switching to Existing..."),
            dialog.existing_radio.setChecked(True),
            QTimer.singleShot(500, lambda: (
                check_state(),
                QTimer.singleShot(1000, lambda: (
                    print("\n3. Switching back to Video..."),
                    dialog.video_radio.setChecked(True),
                    QTimer.singleShot(500, lambda: (
                        check_state(),
                        QTimer.singleShot(1000, lambda: (
                            print("\n4. Final switch to Existing..."),
                            dialog.existing_radio.setChecked(True),
                            QTimer.singleShot(500, lambda: (
                                check_state(),
                                print("\n=== Test Complete ==="),
                                print("画像ディレクトリ選択欄が表示されているか確認してください"),
                                QTimer.singleShot(3000, app.quit)
                            ))
                        ))
                    ))
                ))
            ))
        ))
    
    # ダイアログを表示してからテスト開始
    dialog.show()
    QTimer.singleShot(500, test_sequence)
    
    app.exec()

if __name__ == "__main__":
    main()