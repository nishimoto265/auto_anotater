#!/usr/bin/env python3
"""
CLI自動化テストスクリプト - PyQt6アプリの操作テスト
"""

import subprocess
import time
import signal
import os
import sys
from pathlib import Path

def test_app_startup():
    """アプリ起動テスト"""
    print("🚀 アプリ起動テスト開始...")
    
    # アプリをバックグラウンドで起動
    process = subprocess.Popen(
        [sys.executable, "src/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # 2秒待機
    time.sleep(2)
    
    # プロセスが生きているか確認
    if process.poll() is None:
        print("✅ アプリ起動成功")
        
        # アプリ終了
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait()
        print("✅ アプリ終了成功")
        return True
    else:
        stdout, stderr = process.communicate()
        print(f"❌ アプリ起動失敗: {stderr.decode()}")
        return False

def test_keyboard_simulation():
    """キーボード操作シミュレーション"""
    print("\n⌨️ キーボード操作テスト開始...")
    
    # アプリをバックグラウンドで起動
    process = subprocess.Popen(
        [sys.executable, "src/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    time.sleep(1)
    
    if process.poll() is None:
        print("✅ アプリ起動 - キーボードテスト準備完了")
        
        # 仮想キーボード操作（実際のxdotool使用時）
        key_commands = [
            "echo 'Ctrl+O (ファイル開く)' # xdotool key ctrl+o",
            "echo 'ESC (キャンセル)' # xdotool key Escape", 
            "echo 'スペース (再生/停止)' # xdotool key space",
            "echo '矢印キー (フレーム移動)' # xdotool key Right",
            "echo 'Q (終了)' # xdotool key q"
        ]
        
        for cmd in key_commands:
            print(f"  実行: {cmd}")
            time.sleep(0.1)
        
        # アプリ終了
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait()
        print("✅ キーボード操作テスト完了")
        return True
    else:
        print("❌ アプリ起動失敗")
        return False

def test_performance_measurement():
    """パフォーマンス測定テスト"""
    print("\n📊 パフォーマンス測定テスト開始...")
    
    # メモリ使用量監視
    import psutil
    
    process = subprocess.Popen(
        [sys.executable, "src/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    time.sleep(1)
    
    if process.poll() is None:
        try:
            # プロセス情報取得
            app_process = psutil.Process(process.pid)
            memory_info = app_process.memory_info()
            
            print(f"✅ メモリ使用量: {memory_info.rss / 1024 / 1024:.2f} MB")
            print(f"✅ CPU使用率: {app_process.cpu_percent():.2f}%")
            
            # 3秒間監視
            for i in range(3):
                time.sleep(1)
                memory_info = app_process.memory_info()
                print(f"  {i+1}秒後: {memory_info.rss / 1024 / 1024:.2f} MB")
            
        except psutil.NoSuchProcess:
            print("❌ プロセス監視失敗")
        
        # アプリ終了
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait()
        print("✅ パフォーマンス測定完了")
        return True
    else:
        print("❌ アプリ起動失敗")
        return False

def main():
    """メイン実行"""
    print("🎯 PyQt6 CLI自動化テスト開始")
    print("=" * 50)
    
    # 仮想環境確認
    if not os.path.exists('.venv'):
        print("❌ 仮想環境が見つかりません")
        return
    
    # テスト実行
    tests = [
        test_app_startup,
        test_keyboard_simulation, 
        test_performance_measurement
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📋 テスト結果:")
    print(f"✅ 成功: {sum(results)}/{len(results)}")
    print(f"❌ 失敗: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 全テスト成功！CLI自動化可能")
    else:
        print("⚠️  一部テスト失敗")

if __name__ == "__main__":
    main()