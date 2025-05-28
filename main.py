import sys
import argparse
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.main_window import MainWindow
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

def initialize_system(config_path: str):
    Logger.setup()
    config_manager = ConfigManager(config_path)
    return config_manager

def main():
    try:
        args = parse_arguments()
        config_manager = initialize_system(args.config)

        app = QApplication(sys.argv)
        app.setStyle('Fusion')

        main_window = MainWindow(
            source_type=args.source,
            start_frame=args.start_frame,
            config_manager=config_manager
        )
        main_window.show()

        return app.exec()

    except Exception as e:
        Logger.critical(f"Application startup failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())