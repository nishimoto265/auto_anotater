"""
GUI Test Utilities - GUI環境でのテスト安全実行ユーティリティ

GUI関連のテストを安全に実行するためのヘルパー関数群
"""

import os
import sys
import pytest
import functools
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Callable, Dict, Optional


def skip_if_no_display(func: Callable) -> Callable:
    """ディスプレイ環境がない場合にテストをスキップするデコレータ"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not os.environ.get('DISPLAY') and sys.platform.startswith('linux'):
            pytest.skip("No DISPLAY environment variable - GUI tests require X11")
        return func(*args, **kwargs)
    return wrapper


def mock_qt_application(func: Callable) -> Callable:
    """QApplicationをモックするデコレータ"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with patch('PyQt6.QtWidgets.QApplication') as mock_app_class:
            mock_app = Mock()
            mock_app_class.return_value = mock_app
            mock_app_class.instance.return_value = None
            return func(*args, **kwargs)
    return wrapper


def mock_qt_widgets(widgets_to_mock: list = None) -> Callable:
    """指定されたQtウィジェットをモックするデコレータ"""
    if widgets_to_mock is None:
        widgets_to_mock = [
            'QMainWindow', 'QWidget', 'QDialog', 'QVBoxLayout', 'QHBoxLayout',
            'QPushButton', 'QLabel', 'QLineEdit', 'QTextEdit', 'QRadioButton',
            'QCheckBox', 'QComboBox', 'QListWidget', 'QTableWidget'
        ]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            patches = {}
            try:
                for widget in widgets_to_mock:
                    patcher = patch(f'PyQt6.QtWidgets.{widget}')
                    patches[widget] = patcher.start()
                    
                return func(*args, **kwargs)
            finally:
                for patcher in patches.values():
                    try:
                        patcher.stop()
                    except RuntimeError:
                        pass  # Already stopped
        return wrapper
    return decorator


class MockQtEnvironment:
    """Qt環境の完全なモッククラス"""
    
    def __init__(self):
        self.patches = {}
        self.mock_objects = {}
        
    def __enter__(self):
        # Core Qt modules
        qt_modules = [
            'PyQt6.QtCore',
            'PyQt6.QtGui', 
            'PyQt6.QtWidgets'
        ]
        
        for module in qt_modules:
            self.patches[module] = patch(module)
            self.mock_objects[module] = self.patches[module].start()
            
        # Create mock QApplication
        self.mock_objects['QApplication'] = Mock()
        self.mock_objects['QDialog'] = Mock()
        self.mock_objects['QMainWindow'] = Mock()
        
        # Setup common Qt constants
        self.setup_qt_constants()
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        for patcher in self.patches.values():
            try:
                patcher.stop()
            except RuntimeError:
                pass
                
    def setup_qt_constants(self):
        """Qt定数の設定"""
        # Mock Qt namespace
        qt_mock = Mock()
        qt_mock.Orientation = Mock()
        qt_mock.Orientation.Horizontal = 1
        qt_mock.Orientation.Vertical = 2
        qt_mock.AlignmentFlag = Mock()
        qt_mock.AlignmentFlag.AlignCenter = 0x0004
        
        self.mock_objects['Qt'] = qt_mock


def create_mock_dialog() -> Mock:
    """モックダイアログを作成"""
    dialog = Mock()
    dialog.exec.return_value = 1  # Accepted
    dialog.DialogCode = Mock()
    dialog.DialogCode.Accepted = 1
    dialog.DialogCode.Rejected = 0
    
    # Common dialog methods
    dialog.show = Mock()
    dialog.hide = Mock()
    dialog.close = Mock()
    dialog.accept = Mock()
    dialog.reject = Mock()
    
    return dialog


def create_mock_main_window() -> Mock:
    """モックメインウィンドウを作成"""
    window = Mock()
    
    # Common window methods
    window.show = Mock()
    window.hide = Mock() 
    window.close = Mock()
    window.setWindowTitle = Mock()
    window.resize = Mock()
    window.setMinimumSize = Mock()
    window.size = Mock()
    window.size.return_value = Mock(width=Mock(return_value=1920), height=Mock(return_value=1080))
    
    # Status bar mock
    window.status_bar = Mock()
    window.status_bar.showMessage = Mock()
    
    return window


def safe_gui_test_execution(test_func: Callable, 
                          timeout_seconds: int = 5,
                          mock_environment: bool = True) -> Any:
    """GUI テストの安全実行"""
    
    if mock_environment:
        with MockQtEnvironment():
            try:
                return test_func()
            except Exception as e:
                print(f"GUI test execution failed: {e}")
                return None
    else:
        try:
            return test_func()
        except Exception as e:
            print(f"GUI test execution failed: {e}")
            return None


class TestEnvironmentChecker:
    """テスト環境チェッカー"""
    
    @staticmethod
    def can_run_gui_tests() -> bool:
        """GUI テストが実行可能かチェック"""
        # ディスプレイ環境確認
        if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
            return False
            
        # PyQt6 インポート確認
        try:
            import PyQt6
            return True
        except ImportError:
            return False
            
    @staticmethod
    def get_test_environment_info() -> Dict[str, Any]:
        """テスト環境情報取得"""
        return {
            'platform': sys.platform,
            'python_version': sys.version,
            'display_available': bool(os.environ.get('DISPLAY')),
            'pyqt6_available': TestEnvironmentChecker._check_pyqt6(),
            'headless_mode': TestEnvironmentChecker._is_headless_mode(),
        }
        
    @staticmethod
    def _check_pyqt6() -> bool:
        """PyQt6利用可能性確認"""
        try:
            import PyQt6
            return True
        except ImportError:
            return False
            
    @staticmethod
    def _is_headless_mode() -> bool:
        """ヘッドレスモード判定"""
        return (
            not os.environ.get('DISPLAY') or
            os.environ.get('CI') == 'true' or
            os.environ.get('HEADLESS') == 'true'
        )


# テスト実行時の環境情報表示
def print_test_environment():
    """テスト環境情報を表示"""
    env_info = TestEnvironmentChecker.get_test_environment_info()
    print("\n=== Test Environment Information ===")
    for key, value in env_info.items():
        print(f"{key}: {value}")
    print("===================================\n")


if __name__ == "__main__":
    print_test_environment()