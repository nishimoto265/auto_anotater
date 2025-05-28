import pytest
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
import cv2
import numpy as np

from src.ui.main_window import MainWindow
from src.ui.frame_viewer import FrameViewer

class TestUIComponents:
    @pytest.fixture
    def app(self):
        return QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        return MainWindow()
    
    @pytest.fixture
    def frame_viewer(self, app):
        return FrameViewer()

    def test_frame_display(self, frame_viewer):
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_viewer.display_frame(test_image)
        assert frame_viewer.current_frame is not None
        assert frame_viewer.current_frame.shape == (480, 640, 3)

    def test_bb_operations(self, frame_viewer):
        # BB作成テスト
        start_pos = QPoint(100, 100)
        end_pos = QPoint(200, 200)
        QTest.mousePress(frame_viewer, Qt.MouseButton.LeftButton, pos=start_pos)
        QTest.mouseMove(frame_viewer, end_pos)
        QTest.mouseRelease(frame_viewer, Qt.MouseButton.LeftButton, pos=end_pos)
        assert len(frame_viewer.bounding_boxes) == 1

        # BB編集テスト
        bb = frame_viewer.bounding_boxes[0]
        edit_pos = QPoint(150, 150)
        QTest.mousePress(frame_viewer, Qt.MouseButton.LeftButton, pos=edit_pos)
        QTest.mouseMove(frame_viewer, QPoint(160, 160))
        QTest.mouseRelease(frame_viewer, Qt.MouseButton.LeftButton)
        assert bb.pos() != edit_pos

    def test_keyboard_shortcuts(self, main_window):
        # 次フレームへの移動
        QTest.keyClick(main_window, Qt.Key.Key_Right)
        assert main_window.current_frame_index == 1

        # 前フレームへの移動
        QTest.keyClick(main_window, Qt.Key.Key_Left)
        assert main_window.current_frame_index == 0

        # ズームイン
        QTest.keyClick(main_window, Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier)
        assert main_window.frame_viewer.zoom_factor > 1.0

    def test_responsive_behavior(self, main_window):
        original_size = main_window.size()
        new_size = QSize(800, 600)
        main_window.resize(new_size)
        QTest.qWait(100)
        assert main_window.frame_viewer.size().width() <= new_size.width()
        assert main_window.frame_viewer.size().height() <= new_size.height()

    def test_performance(self, frame_viewer):
        test_image = np.zeros((2160, 3840, 3), dtype=np.uint8)  # 4K
        start_time = cv2.getTickCount()
        frame_viewer.display_frame(test_image)
        end_time = cv2.getTickCount()
        processing_time = (end_time - start_time) / cv2.getTickFrequency() * 1000
        assert processing_time < 100  # 100ms以下

    def test_bb_drawing_speed(self, frame_viewer):
        # 100個のBBを描画
        for i in range(100):
            x = i % 10 * 50
            y = i // 10 * 50
            frame_viewer.add_bounding_box(QPoint(x, y), QPoint(x+40, y+40))

        start_time = cv2.getTickCount()
        frame_viewer.update()
        end_time = cv2.getTickCount()
        drawing_time = (end_time - start_time) / cv2.getTickFrequency() * 1000
        assert drawing_time < 16  # 16ms以下

    def test_ui_responsiveness(self, main_window):
        for _ in range(10):
            QTest.keyClick(main_window, Qt.Key.Key_Right)
            start_time = cv2.getTickCount()
            QTest.qWait(1)  # UIイベント処理待ち
            end_time = cv2.getTickCount()
            response_time = (end_time - start_time) / cv2.getTickFrequency() * 1000
            assert response_time < 50  # 50ms以下

    def test_mock_events(self, frame_viewer, qtbot):
        qtbot.mouseClick(frame_viewer, Qt.MouseButton.LeftButton)
        qtbot.keyClick(frame_viewer, Qt.Key.Key_Delete)
        qtbot.mouseClick(frame_viewer, Qt.MouseButton.RightButton)
        assert frame_viewer.context_menu_shown

    def test_screen_capture(self, frame_viewer):
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_viewer.display_frame(test_image)
        capture = frame_viewer.grab().toImage()
        assert not capture.isNull()
        assert capture.size() == frame_viewer.size()