#!/usr/bin/env python3
"""
テスト実行スクリプト
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """すべてのテストを実行"""
    
    # プロジェクトルート
    project_root = Path(__file__).parent.parent
    
    print("=== UI修正の回帰テストを実行 ===\n")
    
    # テストコマンド
    test_commands = [
        # 基本的なテスト実行
        ["python", "-m", "pytest", "tests/test_ui_fixes.py", "-v", "--tb=short"],
        
        # 統合テスト
        ["python", "-m", "pytest", "tests/test_integration_ui.py", "-v", "--tb=short"],
        
        # カバレッジ付きテスト
        ["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=term-missing"],
        
        # 特定のマーカーでテスト
        ["python", "-m", "pytest", "-m", "regression", "-v"],
    ]
    
    # 各テストを実行
    for i, cmd in enumerate(test_commands):
        print(f"\n{'='*60}")
        print(f"テスト {i+1}/{len(test_commands)}: {' '.join(cmd[2:])}")
        print('='*60)
        
        try:
            result = subprocess.run(cmd, cwd=project_root)
            if result.returncode != 0:
                print(f"\n❌ テスト失敗: {' '.join(cmd)}")
                return result.returncode
        except Exception as e:
            print(f"\n❌ テスト実行エラー: {e}")
            return 1
    
    print("\n✅ すべてのテストが成功しました！")
    return 0


def run_specific_test(test_name):
    """特定のテストを実行"""
    
    project_root = Path(__file__).parent.parent
    
    if test_name == "dialog":
        # ダイアログ関連のテストのみ
        cmd = ["python", "-m", "pytest", "tests/test_ui_fixes.py::TestProjectStartupDialog", "-v"]
    elif test_name == "canvas":
        # キャンバス関連のテストのみ
        cmd = ["python", "-m", "pytest", "tests/test_ui_fixes.py::TestBBCanvas", "-v"]
    elif test_name == "deletion":
        # 削除機能のテストのみ
        cmd = ["python", "-m", "pytest", "tests/test_ui_fixes.py::TestMainWindow::test_s_key_deletion", "-v"]
    elif test_name == "integration":
        # 統合テストのみ
        cmd = ["python", "-m", "pytest", "tests/test_integration_ui.py", "-v"]
    else:
        print(f"不明なテスト名: {test_name}")
        print("使用可能: dialog, canvas, deletion, integration")
        return 1
    
    print(f"実行: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 特定のテストを実行
        exit_code = run_specific_test(sys.argv[1])
    else:
        # すべてのテストを実行
        exit_code = run_tests()
    
    sys.exit(exit_code)