#!/usr/bin/env python3
"""
エラー防止テスト実行スクリプト

実際に発生したエラーを基に作成された包括的なエラー防止テストスイートを実行。
GUI版とヘッドレス版の両方をサポート。

実行方法:
python run_error_prevention_tests.py                    # 全テスト実行
python run_error_prevention_tests.py --headless         # ヘッドレステストのみ
python run_error_prevention_tests.py --gui              # GUIテストのみ
python run_error_prevention_tests.py --specific         # 具体的エラーケースのみ
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# テストファイルパス
TESTS_DIR = PROJECT_ROOT / 'tests' / 'integration'
RUNTIME_TEST = TESTS_DIR / 'test_runtime_error_prevention.py'
SPECIFIC_TEST = TESTS_DIR / 'test_specific_error_cases.py'
ORIGINAL_TEST = TESTS_DIR / 'test_error_prevention.py'


def run_test_file(test_file, description):
    """個別テストファイル実行"""
    print(f"\n{'='*80}")
    print(f"🚀 {description}")
    print(f"📁 {test_file}")
    print(f"{'='*80}")
    
    if not test_file.exists():
        print(f"❌ テストファイルが見つかりません: {test_file}")
        return False
        
    try:
        # Pythonサブプロセスでテスト実行
        result = subprocess.run([
            sys.executable, str(test_file)
        ], capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        # 出力表示
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        # 結果判定
        success = result.returncode == 0
        if success:
            print(f"✅ {description}: 成功")
        else:
            print(f"❌ {description}: 失敗 (return code: {result.returncode})")
            
        return success
        
    except Exception as e:
        print(f"💥 テスト実行エラー: {e}")
        return False


def run_pytest_tests():
    """pytestベースのテスト実行"""
    try:
        print(f"\n{'='*80}")
        print("🧪 Pytest エラー防止テスト")
        print(f"📁 {ORIGINAL_TEST}")
        print(f"{'='*80}")
        
        result = subprocess.run([
            sys.executable, '-m', 'pytest', str(ORIGINAL_TEST), '-v'
        ], capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        success = result.returncode == 0
        if success:
            print("✅ Pytest エラー防止テスト: 成功")
        else:
            print(f"❌ Pytest エラー防止テスト: 失敗 (return code: {result.returncode})")
            
        return success
        
    except Exception as e:
        print(f"💥 Pytest実行エラー: {e}")
        return False


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='エラー防止テスト実行')
    parser.add_argument('--headless', action='store_true', 
                       help='ヘッドレステストのみ実行（GUI不要）')
    parser.add_argument('--gui', action='store_true', 
                       help='GUIテストのみ実行')
    parser.add_argument('--specific', action='store_true', 
                       help='具体的エラーケーステストのみ実行')
    parser.add_argument('--original', action='store_true', 
                       help='元のエラー防止テストのみ実行')
    
    args = parser.parse_args()
    
    print("🛡️  Fast Auto-Annotation System エラー防止テストスイート")
    print(f"📅 {Path(__file__).name}")
    print(f"🗂️  プロジェクトルート: {PROJECT_ROOT}")
    
    # 実行対象決定
    tests_to_run = []
    
    if args.headless or args.specific:
        tests_to_run.append((SPECIFIC_TEST, "具体的エラーケース防止テスト（ヘッドレス）"))
        
    if args.gui:
        tests_to_run.append((RUNTIME_TEST, "ランタイムエラー防止テスト（GUI）"))
        
    if args.original:
        # pytest 版は別処理
        pass
        
    if not any([args.headless, args.gui, args.specific, args.original]):
        # 全テスト実行
        tests_to_run = [
            (SPECIFIC_TEST, "具体的エラーケース防止テスト（ヘッドレス）"),
            (RUNTIME_TEST, "ランタイムエラー防止テスト（GUI）")
        ]
    
    # テスト実行
    results = []
    
    # Unittest ベーステスト
    for test_file, description in tests_to_run:
        success = run_test_file(test_file, description)
        results.append((description, success))
        
    # Pytest ベーステスト
    if args.original or not any([args.headless, args.gui, args.specific]):
        success = run_pytest_tests()
        results.append(("Pytest エラー防止テスト", success))
    
    # 総合結果
    print(f"\n{'='*80}")
    print("📊 エラー防止テスト総合結果")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"総テスト数: {total_tests}")
    print(f"成功: {passed_tests}")
    print(f"失敗: {failed_tests}")
    
    print(f"\n📋 詳細結果:")
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {description}")
    
    # 総合判定
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print(f"\n🎉 全エラー防止テスト成功！")
        print("   システムは実際のエラーケースに対して堅牢です。")
        print("   🛡️  Fast Auto-Annotation System は本番環境準備完了です。")
        exit_code = 0
    else:
        print(f"\n⚠️  一部エラー防止テストが失敗しました。")
        print("   実際のエラーケースに対する対策を見直してください。")
        print("   🔧 修正が必要です。")
        exit_code = 1
    
    # 推奨次ステップ
    if failed_tests > 0:
        print(f"\n🔧 推奨次ステップ:")
        print("   1. 失敗したテストの詳細ログを確認")
        print("   2. 対応するソースコードのエラーハンドリングを強化")
        print("   3. テスト修正後、再度全テストを実行")
        print("   4. 継続的インテグレーション（CI）への組み込み検討")
    else:
        print(f"\n🚀 推奨次ステップ:")
        print("   1. 継続的インテグレーション（CI）への組み込み")
        print("   2. 新機能開発時のエラーテスト追加")
        print("   3. 定期的なエラー防止テスト実行")
        print("   4. ユーザーフィードバックに基づくテスト拡張")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())