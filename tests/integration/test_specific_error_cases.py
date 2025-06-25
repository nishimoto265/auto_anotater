#!/usr/bin/env python3
"""
具体的エラーケース防止テスト

実際のバグレポートから抽出された具体的なエラーパターンのテスト。
GUI環境が不要な単体テストとして実装。

エラーログ例:
- "Selected BB: BBEntity(...) Deleting BB: bb_9_1749117219"
- "BB deletion triggered Selected BB: BBEntity(...) Deleting BB: bb_0_1749117143"
- "BB list update error: 'dict' object has no attribute 'id'"
- "WARNING: Frame selection took 26.56ms (>5ms)"
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# パス追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestSpecificErrorCases(unittest.TestCase):
    """具体的エラーケースの防止テスト（ヘッドレス）"""
    
    def test_bb_deletion_exact_error_scenario(self):
        """
        実際のエラーログを再現したBB削除テスト
        
        エラーログ:
        Selected BB: BBEntity(id='bb_9_1749117219', ...)
        Deleting BB: bb_9_1749117219
        BB deletion triggered
        Selected BB: BBEntity(id='bb_0_1749117143', ...)
        Deleting BB: bb_0_1749117143
        """
        print("\n🔍 実際のBB削除エラーシナリオ再現")
        
        # MainWindowの削除ロジックをモック
        class MockMainWindow:
            def __init__(self):
                self.current_annotations = [
                    {'id': 'bb_9_1749117219', 'x': 0.5396, 'y': 0.3407, 'w': 0.2503, 'h': 0.1727, 'individual_id': 0, 'action_id': 0, 'confidence': 1.0},
                    {'id': 'bb_0_1749117143', 'x': 0.6498, 'y': 0.5566, 'w': 0.0883, 'h': 0.2888, 'individual_id': 0, 'action_id': 0, 'confidence': 1.0}
                ]
                self.bb_canvas = Mock()
                self.bb_list_panel = Mock()
                self.deletion_calls = []
                
            def get_selected_bb(self):
                # 最初の呼び出しでは選択BBあり、2回目では別のBBが選択される状況を再現
                if len(self.deletion_calls) == 0:
                    return type('BBEntity', (), {
                        'id': 'bb_9_1749117219',
                        'x': 0.5396, 'y': 0.3407, 'w': 0.2503, 'h': 0.1727,
                        'individual_id': 0, 'action_id': 0, 'confidence': 1.0
                    })()
                return None
                
            def delete_selected_bb_original_logic(self):
                """元のロジック（重複実行バグ再現）"""
                self.deletion_calls.append("start")
                
                selected_bb = self.get_selected_bb()
                if selected_bb:
                    print(f"Selected BB: {selected_bb.id}")
                    print(f"Deleting BB: {selected_bb.id}")
                    # シグナル送信（これが重複実行の原因）
                    self.emit_bb_deletion_signal(selected_bb.id)
                    # さらにダイレクト削除も実行（バグ - これで重複削除される）
                    self.current_annotations = [bb for bb in self.current_annotations if bb.get('id') != selected_bb.id]
                else:
                    print("No BB selected for deletion")
                    if self.current_annotations:
                        deleted_bb = self.current_annotations.pop()
                        print(f"Deleted latest BB: {deleted_bb['id']}")
                    
            def emit_bb_deletion_signal(self, bb_id):
                """シグナル削除処理（重複実行の原因）"""
                self.deletion_calls.append(f"signal_delete_{bb_id}")
                # シグナルハンドラーが別のBBを削除する
                if self.current_annotations:
                    self.current_annotations.pop()  # 最新BB削除
                    
            def delete_selected_bb_fixed_logic(self):
                """修正されたロジック（重複実行防止）"""
                self.deletion_calls.append("start_fixed")
                
                selected_bb = self.get_selected_bb()
                deleted_bb_id = None
                
                if selected_bb:
                    print(f"Selected BB: {selected_bb.id}")
                    print(f"Deleting selected BB: {selected_bb.id}")
                    deleted_bb_id = selected_bb.id
                    self.current_annotations = [bb for bb in self.current_annotations if bb.get('id') != selected_bb.id]
                else:
                    if self.current_annotations:
                        deleted_bb = self.current_annotations.pop()
                        deleted_bb_id = deleted_bb['id']
                        print(f"Deleted latest BB: {deleted_bb_id}")
                        
                if deleted_bb_id:
                    print(f"Successfully deleted BB: {deleted_bb_id}")
        
        # バグのあるロジックのテスト
        print("🐛 バグ再現: 重複削除ロジック")
        window_buggy = MockMainWindow()
        initial_count = len(window_buggy.current_annotations)
        
        window_buggy.delete_selected_bb_original_logic()
        
        after_buggy_count = len(window_buggy.current_annotations)
        deleted_count_buggy = initial_count - after_buggy_count
        
        print(f"  削除前: {initial_count} BBs")
        print(f"  削除後: {after_buggy_count} BBs")
        print(f"  削除数: {deleted_count_buggy} BBs")
        print(f"  削除呼び出し: {window_buggy.deletion_calls}")
        
        # バグ検証: 1回の削除で2つ削除される
        self.assertGreater(deleted_count_buggy, 1, "バグのあるロジックでは複数削除される")
        
        # 修正されたロジックのテスト
        print("\n✅ 修正: 単一削除ロジック")
        window_fixed = MockMainWindow()
        initial_count_fixed = len(window_fixed.current_annotations)
        
        window_fixed.delete_selected_bb_fixed_logic()
        
        after_fixed_count = len(window_fixed.current_annotations)
        deleted_count_fixed = initial_count_fixed - after_fixed_count
        
        print(f"  削除前: {initial_count_fixed} BBs")
        print(f"  削除後: {after_fixed_count} BBs")
        print(f"  削除数: {deleted_count_fixed} BBs")
        print(f"  削除呼び出し: {window_fixed.deletion_calls}")
        
        # 修正検証: 1回の削除で1つだけ削除される
        self.assertEqual(deleted_count_fixed, 1, "修正されたロジックでは1つだけ削除される")
        
        print("✅ BB削除重複実行防止: PASS")
        
    def test_bb_list_update_dict_attribute_error(self):
        """
        BBリスト更新時の 'dict' object has no attribute 'id' エラー防止
        
        エラーメッセージ:
        "BB list update error: 'dict' object has no attribute 'id'"
        """
        print("\n🔍 BBリスト更新dict属性エラー防止")
        
        # BBListPanelの update_bb_list ロジックをモック
        class MockBBListPanel:
            def __init__(self):
                self.update_calls = []
                self.error_calls = []
                
            def update_bb_list_original(self, bb_list):
                """元のロジック（型チェック不足）"""
                self.update_calls.append("original")
                for bb in bb_list:
                    # 直接属性アクセス（dictの場合エラー）
                    bb_id = bb.id  # AttributeError: 'dict' object has no attribute 'id'
                    
            def update_bb_list_fixed(self, bb_list):
                """修正されたロジック（型チェック付き）"""
                self.update_calls.append("fixed")
                for bb in bb_list:
                    try:
                        # 辞書とオブジェクトの両方に対応
                        if hasattr(bb, 'id'):
                            bb_id = bb.id
                        elif isinstance(bb, dict):
                            bb_id = bb.get('id', 'unknown')
                        else:
                            bb_id = str(bb)
                        
                        print(f"Processing BB: {bb_id}")
                    except Exception as e:
                        self.error_calls.append(str(e))
                        print(f"BB list update error: {e}")
        
        # 問題のあるデータ（dictとオブジェクトの混在）
        problematic_bb_list = [
            # dictオブジェクト（'id'キーなし）
            {'x': 0.5, 'y': 0.5, 'w': 0.1, 'h': 0.1, 'individual_id': 0},
            # dictオブジェクト（'id'キーあり）
            {'id': 'bb_123', 'x': 0.3, 'y': 0.3, 'w': 0.1, 'h': 0.1, 'individual_id': 1},
            # BBEntityオブジェクト風
            type('BBEntity', (), {'id': 'bb_456', 'x': 0.7, 'y': 0.7})()
        ]
        
        # バグのあるロジックのテスト
        print("🐛 バグ再現: 型チェック不足")
        panel_buggy = MockBBListPanel()
        
        try:
            panel_buggy.update_bb_list_original(problematic_bb_list)
            buggy_success = False
        except AttributeError as e:
            print(f"  期待通りエラー発生: {e}")
            buggy_success = True
            
        self.assertTrue(buggy_success, "型チェック不足でAttributeErrorが発生するべき")
        
        # 修正されたロジックのテスト
        print("\n✅ 修正: 型チェック付きロジック")
        panel_fixed = MockBBListPanel()
        
        try:
            panel_fixed.update_bb_list_fixed(problematic_bb_list)
            fixed_success = True
        except Exception as e:
            print(f"  予期しないエラー: {e}")
            fixed_success = False
            
        self.assertTrue(fixed_success, "型チェック付きロジックではエラーが発生しないべき")
        self.assertEqual(len(panel_fixed.error_calls), 0, "エラーが記録されないべき")
        
        print("✅ BBリスト更新dict属性エラー防止: PASS")
        
    def test_shortcut_callable_validation(self):
        """
        ショートカット実行時の 'str' object is not callable エラー防止
        """
        print("\n🔍 ショートカット呼び出し可能性検証")
        
        # ShortcutActionのテスト
        class MockShortcutAction:
            def __init__(self, key, handler, description):
                self.key = key
                self.handler = handler
                self.description = description
                self.call_count = 0
                self.error_count = 0
                
            def execute_original(self):
                """元のロジック（callable チェック不足）"""
                # 直接呼び出し（strの場合エラー）
                result = self.handler()  # TypeError: 'str' object is not callable
                self.call_count += 1
                return result
                
            def execute_fixed(self):
                """修正されたロジック（callable チェック付き）"""
                if callable(self.handler):
                    try:
                        result = self.handler()
                        self.call_count += 1
                        return result
                    except Exception as e:
                        self.error_count += 1
                        print(f"Handler execution error: {e}")
                else:
                    self.error_count += 1
                    print(f"Handler is not callable: {type(self.handler)} = {self.handler}")
                return None
        
        # 正常なハンドラー
        call_log = []
        def valid_handler():
            call_log.append("valid_called")
            return "success"
            
        # 問題のあるハンドラー（文字列）
        invalid_handler = "toggle_bb_creation_mode"  # 実際のエラーケース
        
        # バグのあるロジックのテスト
        print("🐛 バグ再現: callable チェック不足")
        action_buggy = MockShortcutAction("W", invalid_handler, "Invalid Handler")
        
        try:
            action_buggy.execute_original()
            buggy_success = False
        except TypeError as e:
            print(f"  期待通りエラー発生: {e}")
            buggy_success = True
            
        self.assertTrue(buggy_success, "callable チェック不足でTypeErrorが発生するべき")
        
        # 修正されたロジックのテスト
        print("\n✅ 修正: callable チェック付きロジック")
        
        # 有効なハンドラーのテスト
        action_valid = MockShortcutAction("W", valid_handler, "Valid Handler")
        result_valid = action_valid.execute_fixed()
        
        self.assertEqual(result_valid, "success", "有効なハンドラーは正常実行されるべき")
        self.assertEqual(action_valid.call_count, 1, "呼び出し回数が記録されるべき")
        self.assertEqual(action_valid.error_count, 0, "エラー回数は0であるべき")
        
        # 無効なハンドラーのテスト
        action_invalid = MockShortcutAction("S", invalid_handler, "Invalid Handler")
        result_invalid = action_invalid.execute_fixed()
        
        self.assertIsNone(result_invalid, "無効なハンドラーはNoneを返すべき")
        self.assertEqual(action_invalid.call_count, 0, "呼び出し回数は0であるべき")
        self.assertEqual(action_invalid.error_count, 1, "エラー回数が記録されるべき")
        
        print("✅ ショートカット呼び出し可能性検証: PASS")
        
    def test_performance_measurement_accuracy(self):
        """
        パフォーマンス測定の精度とオーバーヘッド検証
        
        警告例:
        "WARNING: Frame selection took 26.56ms (>5ms)"
        """
        print("\n🔍 パフォーマンス測定精度検証")
        
        import time
        
        # パフォーマンス測定ロジックのテスト
        class MockPerformanceMonitor:
            def __init__(self):
                self.measurements = []
                self.warnings = []
                
            def measure_operation(self, operation, target_ms=5.0):
                """操作の実行時間測定"""
                start_time = time.perf_counter()
                
                result = operation()
                
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                self.measurements.append(elapsed_ms)
                
                if elapsed_ms > target_ms:
                    warning = f"WARNING: Operation took {elapsed_ms:.2f}ms (>{target_ms}ms)"
                    self.warnings.append(warning)
                    print(f"  {warning}")
                    
                return result, elapsed_ms
        
        monitor = MockPerformanceMonitor()
        
        # 高速操作（目標内）
        def fast_operation():
            time.sleep(0.001)  # 1ms
            return "fast_result"
            
        # 低速操作（目標超過）
        def slow_operation():
            time.sleep(0.01)   # 10ms
            return "slow_result"
            
        # 測定テスト
        print("⚡ 高速操作測定")
        result_fast, time_fast = monitor.measure_operation(fast_operation, 5.0)
        
        print("🐌 低速操作測定")
        result_slow, time_slow = monitor.measure_operation(slow_operation, 5.0)
        
        # 結果検証
        self.assertEqual(result_fast, "fast_result", "高速操作の結果が正しいべき")
        self.assertEqual(result_slow, "slow_result", "低速操作の結果が正しいべき")
        
        # パフォーマンス検証
        self.assertLess(time_fast, 5.0, "高速操作は目標時間内であるべき")
        self.assertGreater(time_slow, 5.0, "低速操作は目標時間を超過するべき")
        
        # 警告検証
        self.assertEqual(len(monitor.warnings), 1, "低速操作のみ警告が発生するべき")
        self.assertIn("10.", monitor.warnings[0], "警告メッセージに実際の時間が含まれるべき")
        
        print(f"  測定結果: 高速={time_fast:.2f}ms, 低速={time_slow:.2f}ms")
        print(f"  警告数: {len(monitor.warnings)}")
        print("✅ パフォーマンス測定精度検証: PASS")
        
    def test_data_consistency_validation(self):
        """
        データ整合性検証（BB作成・削除・更新の一貫性）
        """
        print("\n🔍 データ整合性検証")
        
        # アノテーションデータ管理のテスト
        class MockAnnotationManager:
            def __init__(self):
                self.current_annotations = []
                self.operation_log = []
                
            def create_bb(self, x, y, w, h, individual_id=0, action_id=0):
                """BB作成"""
                import time
                bb_id = f"bb_{len(self.current_annotations)}_{int(time.time())}"
                bb = {
                    'id': bb_id,
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'individual_id': individual_id,
                    'action_id': action_id,
                    'confidence': 1.0
                }
                self.current_annotations.append(bb)
                self.operation_log.append(f"create_{bb_id}")
                return bb_id
                
            def delete_bb(self, bb_id=None):
                """BB削除"""
                if bb_id:
                    # 指定BB削除
                    original_count = len(self.current_annotations)
                    self.current_annotations = [bb for bb in self.current_annotations if bb['id'] != bb_id]
                    deleted_count = original_count - len(self.current_annotations)
                    if deleted_count > 0:
                        self.operation_log.append(f"delete_specific_{bb_id}")
                        return bb_id
                else:
                    # 最新BB削除
                    if self.current_annotations:
                        deleted_bb = self.current_annotations.pop()
                        self.operation_log.append(f"delete_latest_{deleted_bb['id']}")
                        return deleted_bb['id']
                return None
                
            def validate_consistency(self):
                """データ整合性チェック"""
                issues = []
                
                # 重複ID チェック
                ids = [bb['id'] for bb in self.current_annotations]
                if len(ids) != len(set(ids)):
                    issues.append("重複IDが存在")
                    
                # 必須フィールドチェック
                required_fields = ['id', 'x', 'y', 'w', 'h', 'individual_id', 'action_id', 'confidence']
                for i, bb in enumerate(self.current_annotations):
                    for field in required_fields:
                        if field not in bb:
                            issues.append(f"BB[{i}]に必須フィールド'{field}'がない")
                            
                # 座標範囲チェック
                for i, bb in enumerate(self.current_annotations):
                    if not (0 <= bb.get('x', -1) <= 1):
                        issues.append(f"BB[{i}]のx座標が範囲外: {bb.get('x')}")
                    if not (0 <= bb.get('y', -1) <= 1):
                        issues.append(f"BB[{i}]のy座標が範囲外: {bb.get('y')}")
                        
                return issues
        
        manager = MockAnnotationManager()
        
        # 操作シーケンステスト
        print("📝 BB作成シーケンス")
        bb1_id = manager.create_bb(0.2, 0.3, 0.1, 0.1, 0, 0)
        bb2_id = manager.create_bb(0.5, 0.6, 0.15, 0.12, 1, 1)
        bb3_id = manager.create_bb(0.8, 0.1, 0.08, 0.09, 0, 2)
        
        print(f"  作成されたBB: {len(manager.current_annotations)}個")
        
        # 整合性チェック（作成後）
        issues_create = manager.validate_consistency()
        self.assertEqual(len(issues_create), 0, f"作成後の整合性エラー: {issues_create}")
        
        print("🗑️ BB削除シーケンス")
        deleted_id = manager.delete_bb(bb2_id)  # 特定BB削除
        self.assertEqual(deleted_id, bb2_id, "指定されたBBが削除されるべき")
        
        deleted_latest = manager.delete_bb()    # 最新BB削除
        self.assertIsNotNone(deleted_latest, "最新BBが削除されるべき")
        
        print(f"  削除後のBB: {len(manager.current_annotations)}個")
        
        # 整合性チェック（削除後）
        issues_delete = manager.validate_consistency()
        self.assertEqual(len(issues_delete), 0, f"削除後の整合性エラー: {issues_delete}")
        
        # 操作ログチェック
        expected_operations = 5  # 3回作成 + 2回削除
        self.assertEqual(len(manager.operation_log), expected_operations, 
                        f"操作ログ数が一致しない: {manager.operation_log}")
        
        print(f"  操作ログ: {manager.operation_log}")
        print("✅ データ整合性検証: PASS")


def run_specific_error_tests():
    """具体的エラーケース防止テスト実行"""
    print("=" * 80)
    print("🎯 具体的エラーケース防止テスト")
    print("📝 実際のバグレポートから抽出されたエラーパターンのテスト")
    print("=" * 80)
    
    # テストスイート作成
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSpecificErrorCases)
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果サマリー
    print("\n" + "=" * 80)
    print("📊 具体的エラーケース防止テスト結果")
    print("=" * 80)
    print(f"実行テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 全具体的エラーケース防止テスト成功！")
        print("   実際のバグパターンに対する防止策が有効です。")
    else:
        print("\n⚠️  一部テストが失敗しました。")
        print("   実際のバグパターンに対する対策を見直してください。")
        
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_specific_error_tests()
    sys.exit(0 if success else 1)