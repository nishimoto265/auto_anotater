import sys
import argparse
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.main_window import MainWindow
from src.ui.dialogs import StartupDialog
from src.core.config_manager import ConfigManager
from src.utils.logger import Logger

def parse_arguments():
    parser = argparse.ArgumentParser(description='Auto Annotation Tool')
    parser.add_argument('--source', choices=['video', 'frames'], default='video',
                      help='Source type: video or frames')
    parser.add_argument('--start-frame', type=int, default=0,
                      help='Starting frame number')
    parser.add_argument('--config', type=str, default='config/app_config.json',
                      help='Path to config file')
    return parser.parse_args()

def initialize_system():
    Logger.setup()
    ConfigManager.load()
    QApplication.setAttribute(Qt.ApplicationAttribute.HighDpiScaleFactorRoundingPolicy,
                          Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

def main():
    try:
        args = parse_arguments()
        initialize_system()

        app = QApplication(sys.argv)
        app.setStyle('Fusion')

        # 起動時の選択ダイアログを表示
        startup_dialog = StartupDialog()
        result = startup_dialog.exec()
        
        if result == 0:  # キャンセルまたは閉じられた場合
            return 0
        
        # 選択に応じて起動モードを決定
        if result == 1:  # 動画から開始
            source_type = 'video'
            start_frame = 0
        elif result == 2:  # フレームから開始
            source_type = 'frames'
            start_frame = 0
        elif result == 3:  # 前回の続きから
            # TODO: 前回の状態を読み込む処理を実装
            source_type = args.source
            start_frame = args.start_frame
        else:
            source_type = args.source
            start_frame = args.start_frame

        main_window = MainWindow(
            source_type=source_type,
            start_frame=start_frame
        )
        main_window.show()

        return app.exec()

    except Exception as e:
        Logger.critical(f"Application startup failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())