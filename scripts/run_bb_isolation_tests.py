#!/usr/bin/env python3
"""
BB フレーム分離テスト実行スクリプト

このスクリプトは以下の問題が再発しないことを確認します:
1. フレーム切り替え時に前のフレームのBBが残る
2. 全フレームのBBが1つのフレームに表示される
3. BBが他のフレームに漏れて表示される

使用方法:
python run_bb_isolation_tests.py [--verbose] [--performance]
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path

# プロジェクトルートを設定
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT / "src"))

def run_command(cmd: list, timeout: int = 60) -> tuple:
    """コマンド実行"""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            cwd=PROJECT_ROOT
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timeout after {timeout}s"
    except Exception as e:
        return -1, "", str(e)

def run_unit_tests(verbose: bool = False) -> bool:
    """BBフレーム分離単体テストを実行"""
    print("🧪 BBフレーム分離 単体テストを実行中...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/test_presentation/test_bb_frame_isolation.py",
        "--tb=short"
    ]
    
    if verbose:
        cmd.append("-v")
    
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print("✅ 単体テスト成功")
        if verbose:
            print(stdout)
        return True
    else:
        print("❌ 単体テスト失敗")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return False

def run_integration_tests(verbose: bool = False) -> bool:
    """BBフレーム分離統合テストを実行"""
    print("🔄 BBフレーム分離 統合テストを実行中...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/test_frame_specific_bb_rendering.py",
        "--tb=short"
    ]
    
    if verbose:
        cmd.append("-v")
    
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print("✅ 統合テスト成功")
        if verbose:
            print(stdout)
        return True
    else:
        print("❌ 統合テスト失敗")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return False

def run_performance_tests() -> bool:
    """性能テストを実行"""
    print("⚡ BBフレーム分離 性能テストを実行中...")
    
    # 性能テスト専用の実行
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/test_frame_specific_bb_rendering.py::TestFrameSpecificBBRendering::test_performance_bb_clearing",
        "tests/unit/test_presentation/test_bb_frame_isolation.py::TestBBFrameIsolation::test_render_performance_with_many_bbs",
        "-v", "--tb=short"
    ]
    
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print("✅ 性能テスト成功")
        
        # 性能結果の解析
        if "PASS" in stdout:
            print("📊 性能要件を満たしています")
        
        return True
    else:
        print("❌ 性能テスト失敗")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return False

def check_imports() -> bool:
    """必要なモジュールが正しくインポートできることを確認"""
    print("📦 モジュールインポートを確認中...")
    
    try:
        from presentation.bb_canvas.canvas_widget import BBCanvas
        from presentation.bb_canvas.bb_renderer import BBRenderer
        print("✅ 必要なモジュールのインポート成功")
        return True
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        return False

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="BB フレーム分離テスト実行")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    parser.add_argument("--performance", "-p", action="store_true", help="性能テストも実行")
    parser.add_argument("--unit-only", action="store_true", help="単体テストのみ実行")
    parser.add_argument("--integration-only", action="store_true", help="統合テストのみ実行")
    
    args = parser.parse_args()
    
    print("🚀 BB フレーム分離テスト開始")
    print("=" * 50)
    
    start_time = time.time()
    success_count = 0
    total_tests = 0
    
    # モジュールインポートチェック
    total_tests += 1
    if check_imports():
        success_count += 1
    
    # 単体テスト
    if not args.integration_only:
        total_tests += 1
        if run_unit_tests(args.verbose):
            success_count += 1
    
    # 統合テスト
    if not args.unit_only:
        total_tests += 1
        if run_integration_tests(args.verbose):
            success_count += 1
    
    # 性能テスト
    if args.performance:
        total_tests += 1
        if run_performance_tests():
            success_count += 1
    
    # 結果サマリー
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 50)
    print("📋 テスト結果サマリー")
    print(f"実行時間: {elapsed_time:.2f}秒")
    print(f"成功: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 全テスト成功！ BBフレーム分離が正常に動作しています。")
        
        # 追加メッセージ
        print("\n✨ 確認された機能:")
        print("  - フレーム切り替え時の前BBクリア")
        print("  - フレーム別BB表示の分離")
        print("  - BBアイテムの適切なメモリ管理")
        print("  - シーンアイテム数の正確な管理")
        
        if args.performance:
            print("  - 性能要件の満足")
        
        return 0
    else:
        print("💥 一部テストが失敗しました。BBフレーム分離に問題がある可能性があります。")
        
        # 問題のトラブルシューティングヒント
        print("\n🔧 トラブルシューティング:")
        print("  1. BBRenderer._clear_rendered_items()がシーンからアイテムを削除しているか確認")
        print("  2. display_frame()で前フレームのBBが残っていないか確認")
        print("  3. update_bounding_boxes()で適切なBBのみが表示されているか確認")
        print("  4. 差分描画が無効化されているか確認(_should_use_differential_rendering)")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())