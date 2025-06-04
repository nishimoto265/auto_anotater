"""
ユーザー操作応答性テスト
キーボード応答1ms以下・マウス応答5ms以下確認
"""
import time
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from unittest.mock import Mock, patch, MagicMock

from src.presentation.shortcuts.keyboard_handler import KeyboardHandler
from src.presentation.bb_canvas.mouse_handler import MouseHandler
from src.presentation.bb_canvas.canvas_widget import BBCanvas


class TestUserInteraction:
    """ユーザー操作応答性テスト"""
    
    @pytest.fixture
    def app(self):
        """PyQt6アプリケーション"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def keyboard_handler(self, app):
        """KeyboardHandler instance"""
        return KeyboardHandler()
    
    @pytest.fixture
    def mouse_handler(self, app):
        """MouseHandler instance"""
        return MouseHandler()
    
    @pytest.fixture
    def bb_canvas(self, app):
        """BBCanvas instance"""
        return BBCanvas()
    
    def test_keyboard_response_1ms(self, keyboard_handler):
        """キーボード応答1ms以下確認"""
        test_keys = ['A', 'D', 'W', 'S']
        
        for key in test_keys:
            start_time = time.perf_counter()
            result = keyboard_handler.handle_key_press(key)
            end_time = time.perf_counter()
            
            response_time = (end_time - start_time) * 1000
            assert response_time <= 1.0, f"キー'{key}'応答時間{response_time:.3f}msが1ms超過"
            assert result is True, f"キー'{key}'処理が失敗"
    
    def test_ctrl_key_combinations(self, keyboard_handler):
        """Ctrlキー組み合わせ応答確認"""
        start_time = time.perf_counter()
        result = keyboard_handler.handle_key_press('Ctrl+Z')
        end_time = time.perf_counter()
        
        response_time = (end_time - start_time) * 1000
        assert response_time <= 1.0, f"Ctrl+Z応答時間{response_time:.3f}msが1ms超過"
        assert result is True, "Ctrl+Z処理が失敗"
    
    def test_mouse_response_5ms(self, mouse_handler):
        """マウス応答5ms以下確認"""
        test_events = [
            ('press', QPoint(100, 100)),
            ('move', QPoint(150, 150)),
            ('release', QPoint(200, 200))
        ]
        
        for event_type, position in test_events:
            start_time = time.perf_counter()
            
            if event_type == 'press':
                mouse_handler.handle_mouse_press(position, Qt.MouseButton.LeftButton)
            elif event_type == 'move':
                mouse_handler.handle_mouse_move(position)
            elif event_type == 'release':
                mouse_handler.handle_mouse_release(position, Qt.MouseButton.LeftButton)
            
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000
            
            assert response_time <= 5.0, f"マウス{event_type}応答時間{response_time:.3f}msが5ms超過"
    
    def test_shortcut_keys_response(self, keyboard_handler):
        """ショートカットキー応答確認（A/D/W/S/Ctrl+Z）"""
        shortcuts = {
            'A': 'previous_frame',
            'D': 'next_frame',
            'W': 'create_bb_mode',
            'S': 'delete_bb',
            'Ctrl+Z': 'undo'
        }
        
        for key, expected_action in shortcuts.items():
            start_time = time.perf_counter()
            
            # アクション実行確認
            action = keyboard_handler.get_action_for_key(key)
            result = keyboard_handler.handle_key_press(key)
            
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000
            
            assert action == expected_action, f"キー'{key}'のアクションが不正: {action} != {expected_action}"
            assert response_time <= 1.0, f"ショートカット'{key}'応答時間{response_time:.3f}msが1ms超過"
            assert result is True, f"ショートカット'{key}'処理が失敗"
    
    def test_rapid_key_presses(self, keyboard_handler):
        """高速キー連打応答確認"""
        key_sequence = ['A', 'D'] * 50  # 100回連続キー操作
        
        start_time = time.perf_counter()
        
        for key in key_sequence:
            result = keyboard_handler.handle_key_press(key)
            assert result is True, f"高速連打中のキー'{key}'処理が失敗"
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000
        average_time = total_time / len(key_sequence)
        
        assert average_time <= 1.0, f"高速連打平均応答時間{average_time:.3f}msが1ms超過"
    
    def test_mouse_drag_performance(self, mouse_handler):
        """マウスドラッグ性能確認"""
        # BB作成ドラッグシミュレーション
        start_point = QPoint(100, 100)
        end_point = QPoint(200, 200)
        
        start_time = time.perf_counter()
        
        # ドラッグ開始
        mouse_handler.handle_mouse_press(start_point, Qt.MouseButton.LeftButton)
        
        # ドラッグ中（10点の中間位置）
        for i in range(1, 11):
            x = start_point.x() + (end_point.x() - start_point.x()) * i / 10
            y = start_point.y() + (end_point.y() - start_point.y()) * i / 10
            mouse_handler.handle_mouse_move(QPoint(int(x), int(y)))
        
        # ドラッグ終了
        mouse_handler.handle_mouse_release(end_point, Qt.MouseButton.LeftButton)
        
        end_time = time.perf_counter()
        drag_time = (end_time - start_time) * 1000
        
        assert drag_time <= 50.0, f"ドラッグ操作時間{drag_time:.2f}msが50ms超過"
    
    def test_zoom_wheel_response(self, bb_canvas):
        """ズームホイール応答確認"""
        from PyQt6.QtGui import QWheelEvent
        
        # ホイールイベント作成
        wheel_event = QWheelEvent(
            QPoint(100, 100),  # position
            QPoint(100, 100),  # global position
            QPoint(0, 120),    # pixel delta
            QPoint(0, 120),    # angle delta
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        
        start_time = time.perf_counter()
        bb_canvas.wheelEvent(wheel_event)
        end_time = time.perf_counter()
        
        wheel_time = (end_time - start_time) * 1000
        assert wheel_time <= 5.0, f"ホイールズーム応答時間{wheel_time:.3f}msが5ms超過"
    
    def test_canvas_click_response(self, bb_canvas):
        """キャンバスクリック応答確認"""
        from PyQt6.QtGui import QMouseEvent
        
        # マウスクリックイベント作成
        click_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(150, 150),
            QPoint(150, 150),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        start_time = time.perf_counter()
        bb_canvas.mousePressEvent(click_event)
        end_time = time.perf_counter()
        
        click_time = (end_time - start_time) * 1000
        assert click_time <= 5.0, f"キャンバスクリック応答時間{click_time:.3f}msが5ms超過"
    
    def test_key_event_processing(self, keyboard_handler):
        """キーイベント処理性能確認"""
        from PyQt6.QtGui import QKeyEvent
        
        # 各種キーイベント作成・処理
        key_events = [
            (Qt.Key.Key_A, 'A'),
            (Qt.Key.Key_D, 'D'),
            (Qt.Key.Key_W, 'W'),
            (Qt.Key.Key_S, 'S')
        ]
        
        for qt_key, key_str in key_events:
            key_event = QKeyEvent(
                QKeyEvent.Type.KeyPress,
                qt_key,
                Qt.KeyboardModifier.NoModifier,
                key_str
            )
            
            start_time = time.perf_counter()
            result = keyboard_handler.process_key_event(key_event)
            end_time = time.perf_counter()
            
            process_time = (end_time - start_time) * 1000
            assert process_time <= 1.0, f"キーイベント処理時間{process_time:.3f}msが1ms超過"
            assert result is True, f"キーイベント処理が失敗: {key_str}"
    
    def test_concurrent_user_operations(self, keyboard_handler, mouse_handler):
        """同時ユーザー操作性能確認"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def keyboard_operations():
            start_time = time.perf_counter()
            for _ in range(20):
                keyboard_handler.handle_key_press('D')
            end_time = time.perf_counter()
            results.put(('keyboard', (end_time - start_time) * 1000))
        
        def mouse_operations():
            start_time = time.perf_counter()
            for i in range(20):
                mouse_handler.handle_mouse_move(QPoint(100 + i, 100 + i))
            end_time = time.perf_counter()
            results.put(('mouse', (end_time - start_time) * 1000))
        
        # 同時実行
        keyboard_thread = threading.Thread(target=keyboard_operations)
        mouse_thread = threading.Thread(target=mouse_operations)
        
        start_time = time.perf_counter()
        keyboard_thread.start()
        mouse_thread.start()
        
        keyboard_thread.join()
        mouse_thread.join()
        end_time = time.perf_counter()
        
        total_time = (end_time - start_time) * 1000
        
        # 結果確認
        keyboard_time = None
        mouse_time = None
        
        while not results.empty():
            operation_type, operation_time = results.get()
            if operation_type == 'keyboard':
                keyboard_time = operation_time
            elif operation_type == 'mouse':
                mouse_time = operation_time
        
        assert keyboard_time is not None, "キーボード操作時間が取得できない"
        assert mouse_time is not None, "マウス操作時間が取得できない"
        assert total_time <= 100.0, f"同時操作総時間{total_time:.2f}msが100ms超過"