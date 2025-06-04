"""
フレーム表示テスト
Cache連携50ms以下・ズーム操作100ms以下確認
"""
import time
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap, QImage
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.presentation.bb_canvas.canvas_widget import BBCanvas
from src.presentation.bb_canvas.zoom_controller import ZoomController


class TestFrameDisplay:
    """フレーム表示テスト"""
    
    @pytest.fixture
    def app(self):
        """PyQt6アプリケーション"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def bb_canvas(self, app):
        """BBCanvas instance"""
        return BBCanvas()
    
    @pytest.fixture
    def zoom_controller(self, app):
        """ZoomController instance"""
        return ZoomController()
    
    @pytest.fixture
    def mock_frame_data(self):
        """モックフレームデータ"""
        frame_data = Mock()
        
        # 4K画像データシミュレーション
        image_array = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
        height, width, channel = image_array.shape
        bytes_per_line = 3 * width
        
        qimage = QImage(image_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        frame_data.qimage = qimage
        frame_data.pixmap = QPixmap.fromImage(qimage)
        frame_data.frame_id = "000001"
        frame_data.width = width
        frame_data.height = height
        
        return frame_data
    
    @patch('src.presentation.bb_canvas.canvas_widget.CacheInterface')
    def test_frame_display_50ms_with_cache(self, mock_cache, bb_canvas, mock_frame_data):
        """Cache連携フレーム表示50ms以下確認"""
        # Cache Agentのモック設定
        mock_cache.request_frame_display.return_value = mock_frame_data
        
        frame_id = "000001"
        
        start_time = time.perf_counter()
        bb_canvas.display_frame(frame_id)
        end_time = time.perf_counter()
        
        display_time = (end_time - start_time) * 1000
        assert display_time <= 50.0, f"フレーム表示時間{display_time:.2f}msが50ms超過"
        
        # Cache呼び出し確認
        mock_cache.request_frame_display.assert_called_once_with(frame_id)
    
    def test_frame_display_without_cache_miss(self, bb_canvas, mock_frame_data):
        """キャッシュミス時のフレーム表示確認"""
        with patch('src.presentation.bb_canvas.canvas_widget.CacheInterface') as mock_cache:
            # キャッシュミスをシミュレーション
            mock_cache.request_frame_display.side_effect = [None, mock_frame_data]
            
            frame_id = "000001"
            
            start_time = time.perf_counter()
            bb_canvas.display_frame(frame_id)
            end_time = time.perf_counter()
            
            display_time = (end_time - start_time) * 1000
            # キャッシュミス時も合理的な時間内
            assert display_time <= 200.0, f"キャッシュミス時表示時間{display_time:.2f}msが200ms超過"
    
    def test_zoom_operation_100ms(self, zoom_controller):
        """ズーム操作100ms以下確認"""
        zoom_levels = [0.25, 0.5, 1.0, 2.0, 4.0]
        center_point = (1920, 1080)  # 画面中央
        
        for zoom_level in zoom_levels:
            start_time = time.perf_counter()
            zoom_controller.set_zoom(zoom_level, center_point)
            end_time = time.perf_counter()
            
            zoom_time = (end_time - start_time) * 1000
            assert zoom_time <= 100.0, f"ズーム{zoom_level}x操作時間{zoom_time:.2f}msが100ms超過"
    
    def test_sequential_frame_switching(self, bb_canvas):
        """連続フレーム切り替え性能確認"""
        with patch('src.presentation.bb_canvas.canvas_widget.CacheInterface') as mock_cache:
            # 複数フレームのモック作成
            frames = []
            for i in range(10):
                frame_data = Mock()
                frame_data.frame_id = f"{i:06d}"
                frame_data.pixmap = QPixmap(100, 100)  # 軽量テスト用
                frames.append(frame_data)
            
            mock_cache.request_frame_display.side_effect = frames
            
            switch_times = []
            
            for i, frame in enumerate(frames):
                start_time = time.perf_counter()
                bb_canvas.display_frame(frame.frame_id)
                end_time = time.perf_counter()
                
                switch_time = (end_time - start_time) * 1000
                switch_times.append(switch_time)
                
                assert switch_time <= 50.0, f"フレーム{i}切り替え時間{switch_time:.2f}msが50ms超過"
            
            # 平均切り替え時間確認
            average_time = sum(switch_times) / len(switch_times)
            assert average_time <= 50.0, f"平均切り替え時間{average_time:.2f}msが50ms超過"
    
    def test_zoom_with_frame_display(self, bb_canvas, zoom_controller, mock_frame_data):
        """ズーム状態でのフレーム表示確認"""
        with patch('src.presentation.bb_canvas.canvas_widget.CacheInterface') as mock_cache:
            mock_cache.request_frame_display.return_value = mock_frame_data
            
            # ズーム設定
            zoom_controller.set_zoom(2.0, (1920, 1080))
            bb_canvas.set_zoom_controller(zoom_controller)
            
            start_time = time.perf_counter()
            bb_canvas.display_frame("000001")
            end_time = time.perf_counter()
            
            display_time = (end_time - start_time) * 1000
            assert display_time <= 50.0, f"ズーム状態フレーム表示{display_time:.2f}msが50ms超過"
    
    def test_pan_operation_performance(self, zoom_controller):
        """パン操作性能確認"""
        # 2倍ズーム状態でパン
        zoom_controller.set_zoom(2.0, (1920, 1080))
        
        pan_distances = [(100, 0), (0, 100), (-100, 0), (0, -100)]
        
        for dx, dy in pan_distances:
            start_time = time.perf_counter()
            zoom_controller.pan(dx, dy)
            end_time = time.perf_counter()
            
            pan_time = (end_time - start_time) * 1000
            assert pan_time <= 10.0, f"パン操作({dx},{dy})時間{pan_time:.2f}msが10ms超過"
    
    def test_frame_size_adaptation(self, bb_canvas):
        """フレームサイズ適応確認"""
        with patch('src.presentation.bb_canvas.canvas_widget.CacheInterface') as mock_cache:
            # 異なるサイズのフレーム
            sizes = [(1920, 1080), (3840, 2160), (1280, 720)]
            
            for width, height in sizes:
                frame_data = Mock()
                frame_data.frame_id = f"frame_{width}x{height}"
                frame_data.pixmap = QPixmap(width, height)
                frame_data.width = width
                frame_data.height = height
                
                mock_cache.request_frame_display.return_value = frame_data
                
                start_time = time.perf_counter()
                bb_canvas.display_frame(frame_data.frame_id)
                end_time = time.perf_counter()
                
                adapt_time = (end_time - start_time) * 1000
                assert adapt_time <= 50.0, f"サイズ{width}x{height}適応時間{adapt_time:.2f}msが50ms超過"
    
    def test_continuous_zoom_operations(self, zoom_controller):
        """連続ズーム操作確認"""
        center = (1920, 1080)
        zoom_sequence = [1.0, 1.5, 2.0, 2.5, 3.0, 2.5, 2.0, 1.5, 1.0]
        
        total_start = time.perf_counter()
        
        for zoom_level in zoom_sequence:
            start_time = time.perf_counter()
            zoom_controller.set_zoom(zoom_level, center)
            end_time = time.perf_counter()
            
            zoom_time = (end_time - start_time) * 1000
            assert zoom_time <= 100.0, f"連続ズーム{zoom_level}x時間{zoom_time:.2f}msが100ms超過"
        
        total_end = time.perf_counter()
        total_time = (total_end - total_start) * 1000
        average_time = total_time / len(zoom_sequence)
        
        assert average_time <= 100.0, f"連続ズーム平均時間{average_time:.2f}msが100ms超過"
    
    def test_frame_cache_preload_efficiency(self, bb_canvas):
        """フレームキャッシュ先読み効率確認"""
        with patch('src.presentation.bb_canvas.canvas_widget.CacheInterface') as mock_cache:
            # 現在フレーム表示
            current_frame = Mock()
            current_frame.frame_id = "000050"
            current_frame.pixmap = QPixmap(100, 100)
            mock_cache.request_frame_display.return_value = current_frame
            
            start_time = time.perf_counter()
            bb_canvas.display_frame("000050")
            end_time = time.perf_counter()
            
            display_time = (end_time - start_time) * 1000
            
            # 先読み要求確認
            bb_canvas.request_preload_frames("000050")
            
            assert display_time <= 50.0, f"先読み対応表示時間{display_time:.2f}msが50ms超過"
            mock_cache.prefetch_display_frames.assert_called()
    
    def test_memory_efficient_frame_display(self, bb_canvas, mock_frame_data):
        """メモリ効率的フレーム表示確認"""
        import tracemalloc
        
        with patch('src.presentation.bb_canvas.canvas_widget.CacheInterface') as mock_cache:
            mock_cache.request_frame_display.return_value = mock_frame_data
            
            tracemalloc.start()
            
            # 50フレーム連続表示
            for i in range(50):
                bb_canvas.display_frame(f"{i:06d}")
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # メモリ使用量が妥当な範囲内
            assert peak < 500 * 1024 * 1024, f"ピークメモリ使用量{peak/1024/1024:.2f}MBが500MB超過"