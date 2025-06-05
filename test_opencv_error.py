#!/usr/bin/env python3
"""
OpenCV setBufferAreaMaxSize エラーの診断テスト
"""

import sys
sys.path.insert(0, 'src')

def test_opencv_import():
    """OpenCVインポートテスト"""
    print("=== OpenCV インポートテスト ===")
    
    try:
        import cv2
        print(f"✅ OpenCV インポート成功: {cv2.__version__}")
        
        # setBufferAreaMaxSize が存在するかチェック
        if hasattr(cv2, 'setBufferAreaMaxSize'):
            print("✅ setBufferAreaMaxSize 利用可能")
        else:
            print("❌ setBufferAreaMaxSize 利用不可（新しいOpenCVバージョン）")
            
        return True
        
    except Exception as e:
        print(f"❌ OpenCV インポートエラー: {e}")
        return False

def test_presentation_imports():
    """Presentationモジュールインポートテスト"""
    print("\n=== Presentation モジュールテスト ===")
    
    modules_to_test = [
        'presentation.main_window.main_window',
        'presentation.dialogs.project_startup_dialog', 
        'presentation.dialogs.progress_dialog'
    ]
    
    success_count = 0
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name} インポート成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name} インポートエラー: {e}")
            import traceback
            traceback.print_exc()
            
    return success_count == len(modules_to_test)

def test_main_function():
    """メイン関数テスト（GUI作成なし）"""
    print("\n=== メイン関数テスト ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        import sys
        
        # QApplicationを作成（画面表示なし）
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        print("✅ QApplication 作成成功")
        
        # メイン関数の設定部分のみテスト
        from main import setup_application
        test_app = setup_application()
        print("✅ setup_application 成功")
        
        return True
        
    except Exception as e:
        print(f"❌ メイン関数テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_opencv_functionality():
    """OpenCV基本機能テスト"""
    print("\n=== OpenCV 基本機能テスト ===")
    
    try:
        import cv2
        import numpy as np
        
        # ダミー画像作成
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        print("✅ NumPy 配列作成成功")
        
        # OpenCV 基本操作テスト
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        print("✅ cv2.cvtColor 成功")
        
        # VideoCapture テスト（ダミーパス）
        cap = cv2.VideoCapture()
        print("✅ cv2.VideoCapture 作成成功")
        cap.release()
        
        return True
        
    except Exception as e:
        print(f"❌ OpenCV 基本機能エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def search_setbuffer_usage():
    """setBufferAreaMaxSize使用箇所検索"""
    print("\n=== setBufferAreaMaxSize 使用箇所検索 ===")
    
    import os
    import glob
    
    found_files = []
    
    # Python ファイルを検索
    for pattern in ['src/**/*.py', '**/*.py']:
        for filepath in glob.glob(pattern, recursive=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'setBufferAreaMaxSize' in content:
                        found_files.append(filepath)
                        print(f"📁 {filepath} で発見")
            except Exception:
                continue
    
    if not found_files:
        print("✅ setBufferAreaMaxSize の直接使用なし")
    
    return len(found_files) == 0

if __name__ == "__main__":
    print("OpenCV setBufferAreaMaxSize エラー診断を開始します...\n")
    
    # テスト実行
    opencv_test = test_opencv_import()
    presentation_test = test_presentation_imports()
    main_test = test_main_function()
    opencv_func_test = test_opencv_functionality()
    search_test = search_setbuffer_usage()
    
    print(f"\n=== 診断結果 ===")
    print(f"OpenCV インポート: {'✅ PASS' if opencv_test else '❌ FAIL'}")
    print(f"Presentation モジュール: {'✅ PASS' if presentation_test else '❌ FAIL'}")
    print(f"メイン関数: {'✅ PASS' if main_test else '❌ FAIL'}")
    print(f"OpenCV 基本機能: {'✅ PASS' if opencv_func_test else '❌ FAIL'}")
    print(f"setBuffer 検索: {'✅ PASS' if search_test else '❌ FAIL'}")
    
    if all([opencv_test, presentation_test, main_test, opencv_func_test, search_test]):
        print("\n🎉 すべてのテストが成功しました！")
        print("setBufferAreaMaxSize エラーの原因は外部要因の可能性があります。")
        print("\n推奨解決方法:")
        print("1. 仮想環境の再作成")
        print("2. OpenCV の再インストール")
        print("3. PyQt6 の互換性確認")
    else:
        print("\n⚠️  一部のテストで問題が検出されました。")
        print("詳細なエラーメッセージを確認してください。")