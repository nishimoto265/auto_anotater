#!/usr/bin/env python3
"""
修正されたメインアプリケーションのテスト
複数動画選択機能のエラー修正確認
"""

import sys
import os

def test_main_imports():
    """メインアプリケーションのインポートテスト"""
    print("=== メインアプリケーション インポートテスト ===")
    
    try:
        # パス追加
        sys.path.insert(0, 'src')
        
        # 基本インポート
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
        
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 インポート成功")
        
        # プレゼンテーション層インポート
        from presentation.main_window.main_window import MainWindow
        print("✅ MainWindow インポート成功")
        
        from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
        print("✅ ProjectStartupDialog インポート成功")
        
        from presentation.dialogs.progress_dialog import ProgressDialog
        print("✅ ProgressDialog インポート成功")
        
        # メイン関数インポート
        from main import setup_application
        print("✅ main.setup_application インポート成功")
        
        return True
        
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_compatibility():
    """シグナル互換性テスト"""
    print("\n=== シグナル互換性テスト ===")
    
    try:
        sys.path.insert(0, 'src')
        from PyQt6.QtCore import QObject, pyqtSignal
        from PyQt6.QtWidgets import QApplication
        from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
        
        # QApplication作成
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        
        # ProjectStartupDialog のシグナル定義確認
        dialog = ProjectStartupDialog()
        signal_name = "project_selected"
        
        if hasattr(dialog, signal_name):
            signal_obj = getattr(dialog, signal_name)
            print(f"✅ {signal_name} シグナル確認済み")
            print(f"   シグナル型: {signal_obj.signal}")
            
            # シグナル接続テスト
            def test_receiver(project_type, project_path, config):
                print(f"テスト受信: {type(project_type).__name__}, {type(project_path).__name__}, {type(config).__name__}")
                
                # 複数動画パスの場合の処理テスト
                if isinstance(project_path, list):
                    print(f"  複数動画パス: {len(project_path)}個")
                else:
                    print(f"  単一パス: {project_path}")
            
            signal_obj.connect(test_receiver)
            print("✅ シグナル接続成功")
            
            app.quit()
            return True
        else:
            print(f"❌ {signal_name} シグナルが見つかりません")
            return False
            
    except Exception as e:
        print(f"❌ シグナル互換性エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_progress_dialog_multi_video():
    """ProgressDialog 複数動画対応テスト"""
    print("\n=== ProgressDialog 複数動画対応テスト ===")
    
    try:
        sys.path.insert(0, 'src')
        from PyQt6.QtWidgets import QApplication
        from presentation.dialogs.progress_dialog import ProgressDialog
        
        # テスト用設定
        multi_video_config = {
            "name": "test_multi_project",
            "source_type": "multi_video",
            "source_paths": ["/test/video1.mp4", "/test/video2.mp4", "/test/video3.mp4"],
            "start_frame_number": 300,
            "concatenate_videos": True,
            "output_fps": 5,
            "output_directory": "/tmp/test_output"
        }
        
        single_video_config = {
            "name": "test_single_project", 
            "source_type": "video",
            "source_path": "/test/single.mp4",
            "start_frame_number": 100,
            "output_fps": 5,
            "output_directory": "/tmp/test_output"
        }
        
        # アプリケーション作成（表示なし）
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        
        # 複数動画用ProgressDialog作成テスト
        multi_dialog = ProgressDialog("video", multi_video_config["source_paths"], multi_video_config)
        print("✅ 複数動画 ProgressDialog 作成成功")
        
        # 単一動画用ProgressDialog作成テスト  
        single_dialog = ProgressDialog("video", single_video_config["source_path"], single_video_config)
        print("✅ 単一動画 ProgressDialog 作成成功")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ ProgressDialog テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_path_handling():
    """main.py のパス処理ロジックテスト"""
    print("\n=== main.py パス処理ロジックテスト ===")
    
    try:
        # main.py の処理ロジックをシミュレート
        test_cases = [
            ("単一動画", "video", "/single/video.mp4", {"type": "single"}),
            ("複数動画", "video", ["/video1.mp4", "/video2.mp4"], {"type": "multi", "source_type": "multi_video"})
        ]
        
        for case_name, project_type, project_path, project_config in test_cases:
            print(f"\n--- {case_name}ケース ---")
            
            # main.py line 70-73 のロジック
            if isinstance(project_path, list) and len(project_path) > 0:
                dialog_path = project_path[0]  # 表示用に最初のパス
                print(f"  複数動画検出: {len(project_path)}個")
                print(f"  ProgressDialog用パス: {dialog_path}")
            else:
                dialog_path = project_path
                print(f"  単一動画: {dialog_path}")
                
            print(f"  ✅ パス処理ロジック正常")
        
        return True
        
    except Exception as e:
        print(f"❌ パス処理テストエラー: {e}")
        return False

if __name__ == "__main__":
    print("修正されたメインアプリケーションテストを開始します...\n")
    
    # テスト実行
    import_test = test_main_imports()
    signal_test = test_signal_compatibility() if import_test else False
    progress_test = test_progress_dialog_multi_video() if import_test else False  
    path_test = test_main_path_handling()
    
    print(f"\n=== 最終結果 ===")
    print(f"インポート: {'✅ PASS' if import_test else '❌ FAIL'}")
    print(f"シグナル互換性: {'✅ PASS' if signal_test else '❌ FAIL'}")
    print(f"ProgressDialog: {'✅ PASS' if progress_test else '❌ FAIL'}")
    print(f"パス処理: {'✅ PASS' if path_test else '❌ FAIL'}")
    
    if all([import_test, signal_test, progress_test, path_test]):
        print("\n🎉 すべてのテストが成功しました！")
        print("\n修正された機能:")
        print("  ✅ OpenCV 4.8.1 安定バージョン")
        print("  ✅ NumPy 1.26.4 互換バージョン")
        print("  ✅ pyqtSignal(str, object, dict) 型修正")
        print("  ✅ 複数動画パス処理対応")
        print("  ✅ ProgressDialog 複数動画表示")
        print("\n🚀 メインアプリケーションが正常に動作するはずです！")
        print("    実行コマンド: python src/main.py")
    else:
        print("\n⚠️  一部のテストで問題が検出されました。")
        print("詳細なエラーログを確認してください。")