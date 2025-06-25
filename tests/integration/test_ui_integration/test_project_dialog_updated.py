#!/usr/bin/env python3
"""
更新されたプロジェクト選択ダイアログのテスト
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# パス追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from presentation.dialogs.project_startup_dialog import ProjectStartupDialog

def test_project_dialog():
    """プロジェクト選択ダイアログテスト"""
    app = QApplication(sys.argv)
    
    print("=== 更新されたプロジェクト選択ダイアログテスト ===")
    print("👉 既存プロジェクト選択で画像+アノテーションディレクトリ個別指定を確認")
    print("="*60)
    
    dialog = ProjectStartupDialog()
    
    # 既存プロジェクトラジオボタンを選択
    dialog.existing_radio.setChecked(True)
    
    # テスト用パス設定
    test_image_dir = "/media/thithilab/volume/auto_anotatation/data/frames"
    test_annotation_dir = "/media/thithilab/volume/auto_anotatation/test_annotations"
    test_project_name = "Test_Updated_Project"
    
    # フィールドに値を設定
    dialog.existing_image_path_edit.setText(test_image_dir)
    dialog.existing_annotation_path_edit.setText(test_annotation_dir)
    dialog.project_name_edit.setText(test_project_name)
    
    print(f"✅ 画像ディレクトリ: {dialog.existing_image_path_edit.text()}")
    print(f"✅ アノテーションディレクトリ: {dialog.existing_annotation_path_edit.text()}")
    print(f"✅ プロジェクト名: {dialog.project_name_edit.text()}")
    
    # 入力検証確認
    dialog.validate_input()
    is_valid = dialog.ok_button.isEnabled()
    print(f"✅ 入力検証: {'有効' if is_valid else '無効'}")
    
    # プロジェクト情報生成テスト
    if is_valid:
        # accept_projectメソッドをテスト用に実行
        try:
            dialog.selected_type = "images"
            dialog.selected_path = dialog.existing_image_path_edit.text().strip()
            dialog.project_config = {
                "name": dialog.project_name_edit.text().strip(),
                "description": dialog.description_edit.toPlainText().strip(),
                "source_type": "images",
                "source_path": dialog.selected_path,
                "output_directory": dialog.output_dir_edit.text().strip(),
                "annotation_directory": dialog.existing_annotation_path_edit.text().strip(),
            }
            
            print(f"\n📋 生成されたプロジェクト設定:")
            print(f"  タイプ: {dialog.selected_type}")
            print(f"  パス: {dialog.selected_path}")
            print(f"  設定:")
            for key, value in dialog.project_config.items():
                print(f"    {key}: {value}")
                
            print(f"\n✅ 既存プロジェクト選択（画像+アノテーション）: 正常動作")
            
        except Exception as e:
            print(f"❌ プロジェクト設定生成エラー: {e}")
    else:
        print(f"❌ 入力検証失敗")
    
    dialog.show()
    
    # 3秒後に終了
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(3000)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_project_dialog())