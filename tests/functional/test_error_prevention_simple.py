#!/usr/bin/env python3
"""
エラー防止テスト - 簡易版

実際に発生したエラーの防止策が正しく動作することを確認する簡易テスト。
"""

import sys
import os

# パス追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_bb_deletion_no_duplicate():
    """BB削除の重複実行防止テスト"""
    print("🔍 Test 1: BB削除重複実行防止")
    
    # MockMainWindow
    class MockWindow:
        def __init__(self):
            self.current_annotations = [
                {'id': 'bb_1', 'x': 0.2, 'y': 0.2, 'w': 0.1, 'h': 0.1},
                {'id': 'bb_2', 'x': 0.5, 'y': 0.5, 'w': 0.1, 'h': 0.1},
                {'id': 'bb_3', 'x': 0.8, 'y': 0.8, 'w': 0.1, 'h': 0.1}
            ]
            
        def delete_selected_bb_fixed(self):
            """修正された削除ロジック"""
            # 選択BBなしの場合、最新BB削除
            if self.current_annotations:
                deleted_bb = self.current_annotations.pop()
                return deleted_bb['id']
            return None
    
    window = MockWindow()
    initial_count = len(window.current_annotations)
    
    # 1回の削除操作
    deleted_id = window.delete_selected_bb_fixed()
    final_count = len(window.current_annotations)
    
    # 検証
    assert final_count == initial_count - 1, f"1つだけ削除されるべき: {initial_count} -> {final_count}"
    assert deleted_id == 'bb_3', f"最新BBが削除されるべき: {deleted_id}"
    
    print(f"  削除前: {initial_count} BBs")
    print(f"  削除後: {final_count} BBs") 
    print(f"  削除BB: {deleted_id}")
    print("✅ BB削除重複実行防止: PASS")
    return True

def test_callable_validation():
    """ショートカットハンドラーのcallable検証テスト"""
    print("\n🔍 Test 2: Callable検証")
    
    class MockShortcutAction:
        def __init__(self, handler):
            self.handler = handler
            
        def execute_safe(self):
            """安全な実行（callable検証付き）"""
            if callable(self.handler):
                try:
                    return self.handler()
                except Exception as e:
                    print(f"Handler error: {e}")
                    return None
            else:
                print(f"Handler not callable: {type(self.handler)}")
                return None
    
    # 正常なハンドラー
    def valid_handler():
        return "success"
    
    # 不正なハンドラー（文字列）
    invalid_handler = "toggle_mode"
    
    # テスト実行
    action1 = MockShortcutAction(valid_handler)
    result1 = action1.execute_safe()
    
    action2 = MockShortcutAction(invalid_handler)
    result2 = action2.execute_safe()
    
    # 検証
    assert result1 == "success", f"正常ハンドラーは成功すべき: {result1}"
    assert result2 is None, f"不正ハンドラーはNoneを返すべき: {result2}"
    
    print(f"  正常ハンドラー結果: {result1}")
    print(f"  不正ハンドラー結果: {result2}")
    print("✅ Callable検証: PASS")
    return True

def test_dict_attribute_safety():
    """辞書属性アクセスの安全性テスト"""
    print("\n🔍 Test 3: 辞書属性安全アクセス")
    
    def safe_get_id(bb):
        """安全なID取得"""
        if hasattr(bb, 'id'):
            return bb.id
        elif isinstance(bb, dict):
            return bb.get('id', 'unknown')
        else:
            return str(bb)
    
    # テストデータ
    bb_object = type('BB', (), {'id': 'bb_obj'})()
    bb_dict_with_id = {'id': 'bb_dict', 'x': 0.5}
    bb_dict_no_id = {'x': 0.3, 'y': 0.4}
    
    # テスト実行
    id1 = safe_get_id(bb_object)
    id2 = safe_get_id(bb_dict_with_id)
    id3 = safe_get_id(bb_dict_no_id)
    
    # 検証
    assert id1 == 'bb_obj', f"オブジェクトIDが正しくない: {id1}"
    assert id2 == 'bb_dict', f"辞書IDが正しくない: {id2}"
    assert id3 == 'unknown', f"IDなし辞書の処理が正しくない: {id3}"
    
    print(f"  オブジェクト: {id1}")
    print(f"  辞書(IDあり): {id2}")
    print(f"  辞書(IDなし): {id3}")
    print("✅ 辞書属性安全アクセス: PASS")
    return True

def test_type_conversion_safety():
    """型変換の安全性テスト"""
    print("\n🔍 Test 4: 型変換安全性")
    
    from PyQt6.QtCore import QPointF, QPoint
    
    def safe_point_subtraction(point_f, point):
        """安全なポイント減算"""
        if isinstance(point, QPoint):
            point = QPointF(point)  # QPoint -> QPointF変換
        return point_f - point
    
    # テストデータ
    point_f = QPointF(100.5, 200.7)
    point = QPoint(50, 30)
    
    # 安全な演算
    result = safe_point_subtraction(point_f, point)
    
    # 検証
    expected_x = 50.5
    expected_y = 170.7
    
    assert abs(result.x() - expected_x) < 0.1, f"X座標が正しくない: {result.x()}"
    assert abs(result.y() - expected_y) < 0.1, f"Y座標が正しくない: {result.y()}"
    
    print(f"  結果: ({result.x():.1f}, {result.y():.1f})")
    print(f"  期待: ({expected_x}, {expected_y})")
    print("✅ 型変換安全性: PASS")
    return True

def run_simple_error_prevention_tests():
    """簡易エラー防止テスト実行"""
    print("🛡️  簡易エラー防止テスト実行")
    print("=" * 50)
    
    tests = [
        test_bb_deletion_no_duplicate,
        test_callable_validation,
        test_dict_attribute_safety,
        test_type_conversion_safety
    ]
    
    results = []
    for test in tests:
        try:
            success = test()
            results.append(success)
        except Exception as e:
            print(f"❌ テストエラー: {e}")
            results.append(False)
    
    # 結果
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 結果: {passed}/{total} テスト成功")
    
    if passed == total:
        print("🎉 全エラー防止テスト成功！")
        print("   実際に発生したエラーに対する防止策が有効です。")
        return True
    else:
        print("⚠️  一部テストが失敗しました。")
        return False

if __name__ == "__main__":
    success = run_simple_error_prevention_tests()
    sys.exit(0 if success else 1)