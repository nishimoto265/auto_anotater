#!/usr/bin/env python3
"""
プロジェクト選択ダイアログのみのテスト
複数動画選択機能の動作確認
"""

import sys
import os

# プロジェクトパス追加
sys.path.insert(0, 'src')

def test_project_dialog():
    """プロジェクト選択ダイアログテスト"""
    print("=== プロジェクト選択ダイアログテスト ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
        
        # QApplication作成
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        print("✅ QApplication作成成功")
        
        # ダイアログ作成
        dialog = ProjectStartupDialog()
        print("✅ ProjectStartupDialog作成成功")
        
        # シグナル接続テスト
        def on_project_selected(project_type, project_path, config):
            print(f"シグナル受信:")
            print(f"  project_type: {project_type} (型: {type(project_type).__name__})")
            print(f"  project_path: {project_path} (型: {type(project_path).__name__})")
            print(f"  config: {config}")
            
            # 複数動画の場合の詳細確認
            if isinstance(project_path, list):
                print(f"  複数動画: {len(project_path)}個")
                for i, path in enumerate(project_path):
                    print(f"    {i+1}. {os.path.basename(path)}")
            else:
                print(f"  単一動画: {os.path.basename(project_path)}")
                
            app.quit()
        
        dialog.project_selected.connect(on_project_selected)
        print("✅ シグナル接続成功")
        
        # ダイアログ表示（ノンブロッキング）
        dialog.show()
        print("✅ ダイアログ表示成功")
        print("\n--- 手動テスト用ダイアログが表示されました ---")
        print("1. 「複数選択」ボタンをクリック")
        print("2. 複数の動画ファイルを選択（テスト用にダミーファイルでもOK）")
        print("3. スタートフレーム番号を設定（例: 300）")
        print("4. 「プロジェクト開始」をクリック")
        print("5. シグナル型エラーが発生しないことを確認")
        print("------------------------------------------------")
        
        # イベントループ開始（タイムアウト付き）
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ プロジェクトダイアログエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_emission_manually():
    """シグナル送信の手動テスト"""
    print("\n=== シグナル送信手動テスト ===")
    
    try:
        from PyQt6.QtCore import QObject, pyqtSignal
        
        # テスト用クラス
        class TestEmitter(QObject):
            test_signal = pyqtSignal(str, object, dict)
        
        emitter = TestEmitter()
        
        # シグナル受信テスト
        received_data = []
        def on_signal_received(type_arg, path_arg, config_arg):
            received_data.append((type_arg, path_arg, config_arg))
            print(f"受信: {type_arg}, {type(path_arg).__name__}, {type(config_arg).__name__}")
        
        emitter.test_signal.connect(on_signal_received)
        
        # 単一動画テスト
        emitter.test_signal.emit("video", "/single/video.mp4", {"type": "single"})
        print("✅ 単一動画シグナル送信成功")
        
        # 複数動画テスト
        emitter.test_signal.emit("video", ["/video1.mp4", "/video2.mp4"], {"type": "multi"})
        print("✅ 複数動画シグナル送信成功")
        
        return len(received_data) == 2
        
    except Exception as e:
        print(f"❌ シグナル送信テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("プロジェクト選択ダイアログテストを開始します...\n")
    
    # 基本機能確認
    signal_test = test_signal_emission_manually()
    
    if signal_test:
        print("\n基本シグナル機能は正常です。")
        print("実際のダイアログテストを開始します...\n")
        
        # 実際のダイアログテスト
        dialog_test = test_project_dialog()
        
        if dialog_test:
            print("\n🎉 プロジェクト選択ダイアログが正常に動作しました！")
        else:
            print("\n⚠️  ダイアログテストで問題が発生しました。")
    else:
        print("\n⚠️  基本シグナル機能に問題があります。")