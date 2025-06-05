"""
Agent1 Presentation - KeyboardHandler
キーボードショートカット処理（1ms応答）

性能要件:
- キー検知: 1ms以下
- 処理実行: 用途別最適化
- イベント伝播: 最小遅延

必須ショートカット:
- A: 前フレーム（50ms以下）
- D: 次フレーム（50ms以下）  
- W: BB作成モード（1ms以下）
- S: BB削除（1ms以下）
- Ctrl+Z: 元に戻す（10ms以下）
"""

import time
from typing import Dict, Callable, Optional, Any
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QObject, QEvent, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QKeyEvent


class ShortcutAction:
    """ショートカットアクション"""
    
    def __init__(self, name: str, handler: Callable, target_time: float = 1.0):
        self.name = name
        self.handler = handler
        self.target_time = target_time  # ms
        self.call_count = 0
        self.total_time = 0
        self.max_time = 0
        self.last_time = 0
        
    def execute(self):
        """アクション実行（時間測定付き）"""
        start_time = time.perf_counter()
        
        try:
            if callable(self.handler):
                self.handler()
            else:
                print(f"Handler is not callable: {type(self.handler)} = {self.handler}")
        except Exception as e:
            print(f"Shortcut action error ({self.handler}): {e}")
            import traceback
            traceback.print_exc()
            
        elapsed = (time.perf_counter() - start_time) * 1000
        
        # 統計更新
        self.call_count += 1
        self.total_time += elapsed
        self.max_time = max(self.max_time, elapsed)
        self.last_time = elapsed
        
        # 性能警告
        if elapsed > self.target_time:
            print(f"WARNING: {self.name} took {elapsed:.2f}ms (>{self.target_time}ms)")
            
        return elapsed
        
    def get_stats(self) -> Dict[str, Any]:
        """統計取得"""
        avg_time = self.total_time / self.call_count if self.call_count > 0 else 0
        return {
            'name': self.name,
            'call_count': self.call_count,
            'avg_time': avg_time,
            'max_time': self.max_time,
            'last_time': self.last_time,
            'target_time': self.target_time,
            'performance_ok': avg_time <= self.target_time,
        }


class KeyboardHandler(QObject):
    """
    キーボードショートカット処理
    
    性能要件:
    - キー検知: 1ms以下
    - 処理実行: 用途別最適化
    - イベント伝播: 最小遅延
    """
    
    # シグナル定義
    shortcut_executed = pyqtSignal(str, float)  # action_name, execution_time
    
    # 必須ショートカット定義
    SHORTCUTS = {
        'A': {'name': 'previous_frame', 'target_time': 50.0},
        'D': {'name': 'next_frame', 'target_time': 50.0},
        'W': {'name': 'create_bb_mode', 'target_time': 1.0},
        'S': {'name': 'delete_bb', 'target_time': 1.0},
        'Ctrl+Z': {'name': 'undo', 'target_time': 10.0},
        'Escape': {'name': 'cancel', 'target_time': 1.0},
        'Space': {'name': 'toggle_play', 'target_time': 1.0},
        'Ctrl+S': {'name': 'save', 'target_time': 100.0},
        'Ctrl+O': {'name': 'open', 'target_time': 50.0},
        'F': {'name': 'fit_view', 'target_time': 100.0},
        '+': {'name': 'zoom_in', 'target_time': 50.0},
        '-': {'name': 'zoom_out', 'target_time': 50.0},
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent = parent
        
        # ショートカット管理
        self.shortcuts: Dict[str, QShortcut] = {}
        self.actions: Dict[str, ShortcutAction] = {}
        
        # 性能統計
        self.total_shortcuts_executed = 0
        self.total_execution_time = 0
        
        # キーイベントフィルター
        self.key_filter_enabled = True
        if self.parent:
            self.parent.installEventFilter(self)
        
    def register_shortcut(self, key: str, handler: Callable, 
                         action_name: Optional[str] = None,
                         target_time: float = 1.0):
        """
        ショートカット登録
        
        Args:
            key: キーシーケンス（例: "Ctrl+S"）
            handler: 実行ハンドラー
            action_name: アクション名（省略時はキーから生成）
            target_time: 目標実行時間（ms）
        """
        if not action_name:
            action_name = key.lower().replace('+', '_')
            
        # アクション作成
        action = ShortcutAction(action_name, handler, target_time)
        self.actions[key] = action
        
        # ショートカット作成
        shortcut = QShortcut(QKeySequence(key), self.parent)
        shortcut.activated.connect(lambda: self._execute_action(key))
        self.shortcuts[key] = shortcut
        
        print(f"Registered shortcut: {key} -> {action_name} (target: {target_time}ms)")
        
    def handle_key_press(self, key: str) -> bool:
        """
        キープレス処理（1ms以下必達）
        
        Args:
            key: キー文字列（例: 'A', 'Ctrl+Z'）
            
        Returns:
            bool: 処理成功フラグ
        """
        start_time = time.perf_counter()
        
        try:
            if key in self.actions:
                self.actions[key].execute()
                return True
            elif key in self.SHORTCUTS:
                # デフォルトアクションの場合は空の処理を実行
                return True
            else:
                return False
        except Exception as e:
            print(f"Key press error ({key}): {e}")
            return False
        finally:
            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > 1.0:
                print(f"WARNING: Key press {key} took {elapsed:.3f}ms (>1ms)")
                
    def get_action_for_key(self, key: str) -> str:
        """
        キーに対応するアクション名取得
        
        Args:
            key: キー文字列
            
        Returns:
            str: アクション名
        """
        if key in self.SHORTCUTS:
            return self.SHORTCUTS[key]['name']
        elif key in self.actions:
            return self.actions[key].name
        else:
            return f"unknown_{key.lower().replace('+', '_')}"
            
    def process_key_event(self, key_event: QKeyEvent) -> bool:
        """
        QKeyEvent処理（1ms以下必達）
        
        Args:
            key_event: PyQt6 キーイベント
            
        Returns:
            bool: 処理成功フラグ
        """
        start_time = time.perf_counter()
        
        try:
            # キーシーケンス文字列に変換
            key_str = self._convert_key_event_to_string(key_event)
            return self.handle_key_press(key_str)
        except Exception as e:
            print(f"Key event processing error: {e}")
            return False
        finally:
            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > 1.0:
                print(f"WARNING: Key event processing took {elapsed:.3f}ms (>1ms)")
                
    def _convert_key_event_to_string(self, key_event: QKeyEvent) -> str:
        """QKeyEventを文字列に変換"""
        modifiers = key_event.modifiers()
        key = key_event.key()
        
        # 修飾キー処理
        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
            
        # メインキー処理
        if key == Qt.Key.Key_A:
            parts.append("A")
        elif key == Qt.Key.Key_D:
            parts.append("D")
        elif key == Qt.Key.Key_W:
            parts.append("W")
        elif key == Qt.Key.Key_S:
            parts.append("S")
        elif key == Qt.Key.Key_Z:
            parts.append("Z")
        elif key == Qt.Key.Key_Escape:
            parts.append("Escape")
        elif key == Qt.Key.Key_Space:
            parts.append("Space")
        elif key == Qt.Key.Key_F:
            parts.append("F")
        elif key == Qt.Key.Key_Plus:
            parts.append("+")
        elif key == Qt.Key.Key_Minus:
            parts.append("-")
        else:
            parts.append(key_event.text().upper())
            
        return "+".join(parts)
        
    def register_default_shortcuts(self, handlers: Dict[str, Callable]):
        """
        デフォルトショートカット一括登録
        
        Args:
            handlers: ハンドラー辞書 {action_name: handler}
        """
        for key, config in self.SHORTCUTS.items():
            action_name = config['name']
            target_time = config['target_time']
            
            if action_name in handlers:
                self.register_shortcut(
                    key, 
                    handlers[action_name], 
                    action_name, 
                    target_time
                )
                
    def _execute_action(self, key: str):
        """アクション実行"""
        if key in self.actions:
            action = self.actions[key]
            elapsed = action.execute()
            
            # 統計更新
            self.total_shortcuts_executed += 1
            self.total_execution_time += elapsed
            
            # シグナル発出（name が文字列であることを確認）
            action_name = action.name if isinstance(action.name, str) else str(action.name)
            self.shortcut_executed.emit(action_name, elapsed)
            
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """キーイベントフィルター（高速処理）"""
        if not self.key_filter_enabled:
            return False
            
        if event.type() == QEvent.Type.KeyPress:
            key_event = event
            if isinstance(key_event, QKeyEvent):
                # 特別なキー処理（1ms以下必達）
                start_time = time.perf_counter()
                
                handled = self._handle_key_press_fast(key_event)
                
                elapsed = (time.perf_counter() - start_time) * 1000
                if elapsed > 1:
                    print(f"WARNING: Key event filter took {elapsed:.2f}ms (>1ms)")
                    
                return handled
                
        return False
        
    def _handle_key_press_fast(self, event: QKeyEvent) -> bool:
        """高速キー処理"""
        key = event.key()
        modifiers = event.modifiers()
        
        # 頻繁に使用されるキーの高速処理
        if modifiers == Qt.KeyboardModifier.NoModifier:
            if key == Qt.Key.Key_A:
                if 'A' in self.actions:
                    self._execute_action('A')
                    return True
            elif key == Qt.Key.Key_D:
                if 'D' in self.actions:
                    self._execute_action('D')
                    return True
            elif key == Qt.Key.Key_W:
                if 'W' in self.actions:
                    self._execute_action('W')
                    return True
            elif key == Qt.Key.Key_S:
                if 'S' in self.actions:
                    self._execute_action('S')
                    return True
                    
        return False
        
    def enable_shortcuts(self):
        """ショートカット有効化"""
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(True)
        self.key_filter_enabled = True
        
    def disable_shortcuts(self):
        """ショートカット無効化"""
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(False)
        self.key_filter_enabled = False
        
    def get_action_stats(self, action_name: str) -> Optional[Dict[str, Any]]:
        """アクション統計取得"""
        for action in self.actions.values():
            if action.name == action_name:
                return action.get_stats()
        return None
        
    def get_all_stats(self) -> Dict[str, Any]:
        """全統計取得"""
        action_stats = {}
        for key, action in self.actions.items():
            action_stats[key] = action.get_stats()
            
        avg_execution_time = (self.total_execution_time / self.total_shortcuts_executed 
                             if self.total_shortcuts_executed > 0 else 0)
        
        return {
            'total_shortcuts_executed': self.total_shortcuts_executed,
            'avg_execution_time': avg_execution_time,
            'total_execution_time': self.total_execution_time,
            'registered_shortcuts': len(self.shortcuts),
            'actions': action_stats,
        }
        
    def get_performance_info(self) -> Dict[str, Any]:
        """性能情報取得"""
        stats = self.get_all_stats()
        
        # 性能問題のあるアクション検出
        slow_actions = []
        for action_stats in stats['actions'].values():
            if not action_stats['performance_ok']:
                slow_actions.append(action_stats['name'])
                
        return {
            'avg_execution_time': stats['avg_execution_time'],
            'total_shortcuts': len(self.shortcuts),
            'slow_actions': slow_actions,
            'performance_ok': len(slow_actions) == 0,
            'target_performance': 'A/D: 50ms以下, その他: 1-10ms以下',
        }
        
    def reset_stats(self):
        """統計リセット"""
        for action in self.actions.values():
            action.call_count = 0
            action.total_time = 0
            action.max_time = 0
            action.last_time = 0
            
        self.total_shortcuts_executed = 0
        self.total_execution_time = 0


if __name__ == "__main__":
    # KeyboardHandlerテスト
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
    import sys
    
    app = QApplication(sys.argv)
    
    # テスト用ウィンドウ
    window = QMainWindow()
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    # KeyboardHandler作成
    keyboard_handler = KeyboardHandler(central_widget)
    
    # テスト用ハンドラー
    def test_handler(name):
        def handler():
            print(f"Handler '{name}' executed")
        return handler
        
    # ショートカット登録テスト
    handlers = {
        'previous_frame': test_handler('previous_frame'),
        'next_frame': test_handler('next_frame'),
        'create_bb_mode': test_handler('create_bb_mode'),
        'delete_bb': test_handler('delete_bb'),
        'undo': test_handler('undo'),
    }
    
    keyboard_handler.register_default_shortcuts(handlers)
    
    print("KeyboardHandler Test")
    print("=" * 30)
    
    # 性能情報表示
    perf_info = keyboard_handler.get_performance_info()
    for key, value in perf_info.items():
        print(f"{key}: {value}")
        
    # 統計情報表示
    stats = keyboard_handler.get_all_stats()
    print(f"\nRegistered shortcuts: {stats['registered_shortcuts']}")
    print(f"Actions: {list(stats['actions'].keys())}")
    
    print("\nKeyboardHandler created successfully")
    print("Target performance: A/D: 50ms以下, その他: 1-10ms以下")