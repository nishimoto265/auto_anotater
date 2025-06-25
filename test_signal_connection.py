#!/usr/bin/env python3
"""
シグナル接続の確認
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt6.QtWidgets import QApplication, QRadioButton
from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

def test_signal_connection():
    app = QApplication(sys.argv)
    
    dialog = ProjectStartupDialog()
    
    print("=== Checking signal connections ===")
    
    # toggled シグナルの接続を確認
    print(f"video_radio receivers: {dialog.video_radio.receivers(dialog.video_radio.toggled)}")
    print(f"image_radio receivers: {dialog.image_radio.receivers(dialog.image_radio.toggled)}")
    print(f"existing_radio receivers: {dialog.existing_radio.receivers(dialog.existing_radio.toggled)}")
    
    # 手動でシグナルを発火
    print("\n=== Manually emitting signals ===")
    dialog.existing_radio.toggled.emit(True)
    
    print(f"\nAfter manual emit:")
    print(f"  Label: {dialog.existing_images_label.isVisible()}")
    print(f"  Edit: {dialog.existing_images_edit.isVisible()}")
    
    # 新しいラジオボタンでテスト
    print("\n=== Testing with new radio button ===")
    test_radio = QRadioButton("Test")
    
    def test_handler(checked):
        print(f"Test handler called with checked={checked}")
    
    test_radio.toggled.connect(test_handler)
    print(f"Before setChecked:")
    test_radio.setChecked(True)
    print(f"After setChecked, isChecked={test_radio.isChecked()}")
    
    sys.exit(0)

if __name__ == "__main__":
    test_signal_connection()