#!/usr/bin/env python3
"""
最小限のアプリケーションテスト
PyQt6とOpenCVの互換性確認
"""

def test_minimal_imports():
    """最小限のインポートテスト"""
    print("=== 最小限インポートテスト ===")
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except Exception as e:
        print(f"❌ OpenCV エラー: {e}")
        return False
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 インポート成功")
    except Exception as e:
        print(f"❌ PyQt6 エラー: {e}")
        return False
        
    return True

def test_basic_video_processing():
    """基本的な動画処理テスト"""
    print("\n=== 基本動画処理テスト ===")
    
    try:
        import cv2
        import numpy as np
        
        # ダミー動画データ作成
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # VideoCapture テスト
        cap = cv2.VideoCapture()
        
        # 基本プロパティ取得テスト
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        
        cap.release()
        
        print("✅ 基本動画処理成功")
        return True
        
    except Exception as e:
        print(f"❌ 動画処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_minimal_qt_app():
    """最小限のQtアプリケーション"""
    print("\n=== 最小限Qtアプリケーション ===")
    
    try:
        import sys
        from PyQt6.QtWidgets import QApplication, QLabel
        
        # QApplication作成（表示なし）
        app = QApplication(sys.argv if 'sys' in globals() else [])
        app.setQuitOnLastWindowClosed(False)
        
        print("✅ QApplication作成成功")
        
        # 簡単なウィジェット作成
        label = QLabel("Test")
        print("✅ QLabel作成成功")
        
        # アプリケーション終了
        app.quit()
        print("✅ Qtアプリケーション終了成功")
        
        return True
        
    except Exception as e:
        print(f"❌ Qtアプリケーションエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("最小限アプリケーションテストを開始します...\n")
    
    import_test = test_minimal_imports()
    if not import_test:
        print("インポートエラーのため、テストを中断します。")
        exit(1)
    
    video_test = test_basic_video_processing()
    qt_test = test_minimal_qt_app()
    
    print(f"\n=== 結果 ===")
    print(f"インポート: {'✅ PASS' if import_test else '❌ FAIL'}")
    print(f"動画処理: {'✅ PASS' if video_test else '❌ FAIL'}")
    print(f"Qt: {'✅ PASS' if qt_test else '❌ FAIL'}")
    
    if all([import_test, video_test, qt_test]):
        print("\n🎉 基本機能は正常に動作しています！")
        print("メインアプリケーションの問題は他の要因の可能性があります。")
    else:
        print("\n⚠️  基本機能に問題があります。")