#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

app = QApplication(sys.argv)

# メインウィンドウ
window = QWidget()
layout = QVBoxLayout()

# ダイアログを開くボタン
btn = QPushButton("Open Dialog")

def open_dialog():
    dialog = ProjectStartupDialog()
    # 既存を選択
    dialog.existing_radio.setChecked(True)
    # 手動でトリガー
    dialog.on_project_type_changed()
    
    # デバッグ情報
    print("=== Dialog Debug Info ===")
    print(f"existing_radio checked: {dialog.existing_radio.isChecked()}")
    print(f"existing_images_container exists: {hasattr(dialog, 'existing_images_container')}")
    print(f"existing_images_container visible: {dialog.existing_images_container.isVisible()}")
    print(f"existing_images_label visible: {dialog.existing_images_label.isVisible()}")
    print(f"Parent layout: {dialog.existing_images_container.parent()}")
    
    dialog.exec()

btn.clicked.connect(open_dialog)
layout.addWidget(btn)
window.setLayout(layout)
window.show()

sys.exit(app.exec())