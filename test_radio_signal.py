#!/usr/bin/env python3
"""
ラジオボタンのシグナルテスト
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt6.QtWidgets import QApplication
from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

def test_radio_signals():
    app = QApplication(sys.argv)
    
    dialog = ProjectStartupDialog()
    
    # シグナルが発火しているか確認するためのカウンター
    call_count = [0]
    
    def count_calls():
        call_count[0] += 1
        print(f"on_project_type_changed called! Count: {call_count[0]}")
        print(f"  video: {dialog.video_radio.isChecked()}")
        print(f"  image: {dialog.image_radio.isChecked()}")
        print(f"  existing: {dialog.existing_radio.isChecked()}")
        
        # 元の処理も実行
        is_existing = dialog.existing_radio.isChecked()
        dialog.toggle_existing_images_visibility(is_existing)
        dialog.toggle_multi_video_visibility(dialog.video_radio.isChecked())
        dialog.validate_input()
    
    # 元のメソッドを置き換え
    dialog.on_project_type_changed = count_calls
    
    print("=== Testing radio button changes ===")
    
    print("\n1. Setting existing_radio to checked...")
    dialog.existing_radio.setChecked(True)
    
    print(f"\nAfter setting existing, visibility:")
    print(f"  Label: {dialog.existing_images_label.isVisible()}")
    print(f"  Edit: {dialog.existing_images_edit.isVisible()}")
    
    print("\n2. Setting video_radio to checked...")
    dialog.video_radio.setChecked(True)
    
    print(f"\nAfter setting video, visibility:")
    print(f"  Label: {dialog.existing_images_label.isVisible()}")
    print(f"  Edit: {dialog.existing_images_edit.isVisible()}")
    
    print(f"\nTotal calls to on_project_type_changed: {call_count[0]}")
    
    sys.exit(0)

if __name__ == "__main__":
    test_radio_signals()