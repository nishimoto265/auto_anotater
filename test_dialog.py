#!/usr/bin/env python3
"""
プロジェクト選択ダイアログのテスト
"""

import sys
import os
sys.path.insert(0, 'src')

from PyQt6.QtWidgets import QApplication
from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

def test_dialog():
    app = QApplication(sys.argv)
    
    dialog = ProjectStartupDialog()
    dialog.show()
    
    print("=== プロジェクト選択ダイアログ表示中 ===")
    print("動画ファイル、画像フォルダ、または既存プロジェクトを選択できます")
    
    result = dialog.exec()
    
    if result == ProjectStartupDialog.DialogCode.Accepted:
        project_type, path, config = dialog.get_project_info()
        print(f"\n=== 選択結果 ===")
        print(f"プロジェクトタイプ: {project_type}")
        print(f"パス: {path}")
        print(f"設定: {config}")
        return True
    else:
        print("キャンセルされました")
        return False

if __name__ == "__main__":
    test_dialog()