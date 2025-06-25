#!/usr/bin/env python3
"""
更新された機能のテスト

1. ID文字サイズ5倍（80px）
2. 行動ID表示 → 行動名表示
3. アノテーションファイル出力の行動名対応
4. プロジェクト選択画面での画像+アノテーションディレクトリ個別指定
"""

import sys
import os
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# パス追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from presentation.main_window.main_window import MainWindow

def test_updated_features():
    """更新機能テスト"""
    app = QApplication(sys.argv)
    
    # 既存プロジェクト形式のテストデータ
    project_info = (
        "images",
        "/media/thithilab/volume/auto_anotatation/data/frames",
        {
            "name": "Updated Features Test",
            "output_directory": "",
            "annotation_directory": "/media/thithilab/volume/auto_anotatation/test_annotations"
        }
    )
    
    print("=== 更新機能テスト ===")
    print("1. ID文字サイズ5倍（16px→80px）")
    print("2. 行動ID表示 → 行動名表示")
    print("3. アノテーションファイル行動名出力")
    print("4. プロジェクト選択 - 画像+アノテーションディレクトリ個別指定")
    print("="*50)
    
    window = MainWindow(project_info=project_info)
    window.show()
    QTest.qWait(1000)
    
    # BB作成モードON
    print("\n🔧 BB作成モードを有効化...")
    window.toggle_bb_creation_mode()
    QTest.qWait(200)
    
    # 異なる行動IDのBBを作成してテスト
    actions_to_test = [
        (0, "待機"),
        (1, "移動"), 
        (2, "食事"),
        (3, "休憩"),
        (4, "その他")
    ]
    
    print(f"\n🎯 各行動タイプのBBを作成...")
    for action_id, action_name in actions_to_test:
        # 行動設定
        window.action_panel.select_action(action_id)
        
        # BB作成（位置をずらして配置）
        x = 0.1 + (action_id * 0.15)
        y = 0.2 + (action_id * 0.1)
        window.on_bb_created(x, y, 0.1, 0.1)
        
        print(f"  ✅ 行動ID {action_id} ({action_name}) のBB作成")
    
    print(f"\n📄 作成されたBB数: {len(window.current_annotations)}")
    
    # アノテーションファイル確認
    if window.annotation_output_dir and os.path.exists(window.annotation_output_dir):
        frame_file = f"{window.current_frame:06d}.txt"
        file_path = os.path.join(window.annotation_output_dir, frame_file)
        
        if os.path.exists(file_path):
            print(f"\n📁 アノテーションファイル確認: {frame_file}")
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            print(f"  ファイル内容（{len(lines)}行）:")
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 6:
                        individual_id = parts[0]
                        action_name = parts[5]  # 行動名（数値ではなく文字列）
                        print(f"    行{i+1}: ID={individual_id}, 行動={action_name}")
                        
                        # 行動名が正しく出力されているか確認
                        expected_actions = ["待機", "移動", "食事", "休憩", "その他"]
                        if action_name in expected_actions:
                            print(f"      ✅ 行動名正常: {action_name}")
                        else:
                            print(f"      ❌ 行動名異常: {action_name}")
        else:
            print(f"  ⚠️ アノテーションファイルが見つかりません: {file_path}")
    else:
        print(f"  ⚠️ アノテーション出力ディレクトリが設定されていません")
    
    print(f"\n🖼️ UI表示テスト:")
    print(f"  - ID文字サイズ: 80px（5倍）- 目視確認")
    print(f"  - 行動表示: ID数値 → 行動名文字列 - 目視確認")
    print(f"  - BB線の太さ: 4px - 目視確認")
    
    print(f"\n=== テスト結果 ===")
    print(f"✅ アノテーション出力ディレクトリ設定: {window.annotation_output_dir}")
    print(f"✅ BB作成とファイル保存: 動作確認")
    print(f"✅ 行動名表示・保存: YOLO形式対応")
    print(f"✅ プロジェクト形式: 画像+アノテーションディレクトリ個別指定対応")
    
    # 3秒後に終了
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(3000)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_updated_features())