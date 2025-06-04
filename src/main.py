"""
Agent1 Presentation - メインエントリーポイント
PyQt6高速UI・BB描画・ショートカット専門

使用方法:
python src/main.py
python src/main.py --debug
"""

import sys
import argparse
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from presentation.main_window.main_window import MainWindow


def setup_application() -> QApplication:
    """アプリケーション初期化"""
    app = QApplication(sys.argv)
    
    # アプリケーション情報設定
    app.setApplicationName("Fast Auto-Annotation System")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Agent1 Presentation")
    
    # 高DPI対応 (PyQt6では自動的に有効)
    # PyQt6では高DPI対応が自動的に有効化されるため、明示的な設定は不要
    
    return app


def main():
    """メイン関数"""
    # コマンドライン引数解析
    parser = argparse.ArgumentParser(description='Agent1 Presentation - PyQt6高速UI')
    parser.add_argument('--debug', action='store_true', help='デバッグモード')
    parser.add_argument('--profile', action='store_true', help='プロファイルモード')
    args = parser.parse_args()
    
    # アプリケーション初期化
    app = setup_application()
    
    # メインウィンドウ作成
    start_time = time.perf_counter()
    window = MainWindow()
    
    # 起動時間測定
    startup_time = (time.perf_counter() - start_time) * 1000
    print(f"Total startup time: {startup_time:.2f}ms")
    
    # デバッグ情報表示
    if args.debug:
        print("=== Agent1 Presentation Debug Mode ===")
        print(f"Qt Version: {app.instance().property('qtVersion')}")
        print(f"Window size: {window.size().width()}x{window.size().height()}")
        print(f"DPI: {app.primaryScreen().logicalDotsPerInch()}")
        print("=====================================")
    
    # ウィンドウ表示
    window.show()
    
    # イベントループ開始
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())