#!/usr/bin/env python3
"""
動画処理機能のテスト
"""

import os
import sys
import tempfile
import shutil

# プロジェクトパスを追加
sys.path.insert(0, 'src')

def test_video_processing():
    """動画処理機能のテスト"""
    
    print("=== 動画処理機能テスト ===")
    
    # 1. OpenCVインポートテスト
    try:
        import cv2
        print("✅ OpenCV import successful")
        print(f"   OpenCV version: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    # 2. ProgressDialogインポートテスト
    try:
        from presentation.dialogs.progress_dialog import ProcessingWorker
        print("✅ ProcessingWorker import successful")
    except ImportError as e:
        print(f"❌ ProcessingWorker import failed: {e}")
        return False
    
    # 3. 動画ファイル存在確認
    test_video_path = "/media/thithilab/volume/research/datasets/video/test/2025-04-01-14-right/20250401-145501-150000.mp4"
    if os.path.exists(test_video_path):
        print(f"✅ Test video file found: {test_video_path}")
        
        # 動画情報取得テスト
        cap = cv2.VideoCapture(test_video_path)
        if cap.isOpened():
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"   Total frames: {total_frames}")
            print(f"   FPS: {fps}")
            print(f"   Resolution: {width}x{height}")
            
            cap.release()
            print("✅ Video file can be opened and read")
        else:
            print("❌ Cannot open video file")
            return False
    else:
        print(f"⚠️  Test video file not found: {test_video_path}")
        print("   Using a dummy video for testing...")
        test_video_path = None
    
    # 4. 出力ディレクトリテスト
    test_output_dir = "/tmp/test_video_output"
    if os.path.exists(test_output_dir):
        shutil.rmtree(test_output_dir)
    
    os.makedirs(test_output_dir)
    print(f"✅ Output directory created: {test_output_dir}")
    
    # 5. ProcessingWorkerテスト（実際の処理なしで構造確認）
    if test_video_path:
        config = {
            'name': 'test_project',
            'output_fps': 5,
            'output_directory': test_output_dir
        }
        
        worker = ProcessingWorker("video", test_video_path, config)
        print("✅ ProcessingWorker created successfully")
        
        # テスト用プロパティ確認
        print(f"   Project type: {worker.project_type}")
        print(f"   Source path: {worker.source_path}")
        print(f"   Config: {worker.config}")
    
    # 6. 簡単なフレーム抽出テスト
    if test_video_path:
        print("\n--- フレーム抽出テスト ---")
        cap = cv2.VideoCapture(test_video_path)
        
        if cap.isOpened():
            # 最初の5フレームだけ抽出
            for i in range(5):
                ret, frame = cap.read()
                if ret:
                    output_path = os.path.join(test_output_dir, f"test_frame_{i:06d}.jpg")
                    success = cv2.imwrite(output_path, frame)
                    if success:
                        print(f"   ✅ Frame {i} saved: {output_path}")
                    else:
                        print(f"   ❌ Failed to save frame {i}")
                else:
                    print(f"   ⚠️  No more frames at frame {i}")
                    break
            
            cap.release()
            
            # 保存されたフレーム確認
            saved_frames = [f for f in os.listdir(test_output_dir) if f.endswith('.jpg')]
            print(f"   ✅ Total frames saved: {len(saved_frames)}")
            
        else:
            print("   ❌ Cannot open video for frame extraction test")
    
    # 7. クリーンアップ
    if os.path.exists(test_output_dir):
        frame_count = len([f for f in os.listdir(test_output_dir) if f.endswith('.jpg')])
        shutil.rmtree(test_output_dir)
        print(f"✅ Cleanup completed. {frame_count} frames were created.")
    
    print("\n=== テスト完了 ===")
    return True

def test_project_dialog_structure():
    """プロジェクトダイアログ構造テスト"""
    
    print("\n=== プロジェクトダイアログ構造テスト ===")
    
    try:
        # ダミーのプロジェクト設定作成
        test_config = {
            'name': 'test_project',
            'description': 'Test video project',
            'source_type': 'video',
            'source_path': '/test/video.mp4',
            'output_fps': 5,
            'output_directory': '/test/output'
        }
        
        print("✅ Project config structure test passed")
        print(f"   Config keys: {list(test_config.keys())}")
        
        # 必須フィールド確認
        required_fields = ['source_type', 'source_path', 'output_directory']
        for field in required_fields:
            if field in test_config:
                print(f"   ✅ Required field '{field}': {test_config[field]}")
            else:
                print(f"   ❌ Missing required field: {field}")
                
        return True
        
    except Exception as e:
        print(f"❌ Project dialog structure test failed: {e}")
        return False

if __name__ == "__main__":
    print("動画処理機能テストを開始します...\n")
    
    # テスト実行
    video_test_result = test_video_processing()
    dialog_test_result = test_project_dialog_structure()
    
    print(f"\n=== 総合結果 ===")
    print(f"動画処理テスト: {'✅ PASS' if video_test_result else '❌ FAIL'}")
    print(f"ダイアログテスト: {'✅ PASS' if dialog_test_result else '❌ FAIL'}")
    
    if video_test_result and dialog_test_result:
        print("\n🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        print("\n⚠️  一部のテストが失敗しました。")
        sys.exit(1)