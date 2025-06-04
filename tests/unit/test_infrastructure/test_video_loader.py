"""
Unit tests for VideoLoader - OpenCV video loading engine
Performance target: Real-time loading (1 second video / 1 second processing)
"""

import pytest
import os
import time
import cv2
import numpy as np
from unittest.mock import patch, MagicMock

from src.infrastructure.video.video_loader import (
    VideoLoader, VideoMetadata, VideoProcessingError
)


class TestVideoLoaderPerformance:
    """Performance tests for VideoLoader"""
    
    @pytest.fixture
    def video_loader(self):
        return VideoLoader()
    
    @pytest.fixture
    def sample_video_path(self, tmp_path):
        """Create a sample video for testing"""
        video_path = tmp_path / "test_video.mp4"
        
        # Create a simple test video using OpenCV
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))
        
        # Write 30 frames (1 second at 30fps)
        for i in range(30):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:, :, i % 3] = 255  # Different color each frame
            out.write(frame)
            
        out.release()
        return str(video_path)
    
    def test_video_loading_real_time(self, video_loader, sample_video_path):
        """Test video loading meets real-time performance (1 second video / 1 second processing)"""
        start_time = time.perf_counter()
        
        metadata = video_loader.load_video(sample_video_path)
        
        elapsed_time = time.perf_counter() - start_time
        
        # Should load 1 second video in less than 1 second
        assert elapsed_time < 1.0, f"Video loading took {elapsed_time}s, should be < 1s"
        assert metadata.duration == pytest.approx(1.0, rel=0.1)
        assert metadata.fps == 30.0
        assert metadata.frame_count == 30
    
    def test_metadata_extraction_100ms(self, video_loader, sample_video_path):
        """Test metadata extraction under 100ms"""
        start_time = time.perf_counter()
        
        metadata = video_loader.load_video(sample_video_path)
        
        elapsed_time = time.perf_counter() - start_time
        
        assert elapsed_time < 0.1, f"Metadata extraction took {elapsed_time}s, should be < 0.1s"
        assert isinstance(metadata, VideoMetadata)
    
    def test_supported_format_validation_1ms(self, video_loader):
        """Test format validation under 1ms"""
        test_paths = [
            "test.mp4", "test.avi", "test.mov", "test.mkv"
        ]
        
        start_time = time.perf_counter()
        
        for path in test_paths:
            video_loader._is_supported_format(path)
            
        elapsed_time = time.perf_counter() - start_time
        
        assert elapsed_time < 0.001, f"Format validation took {elapsed_time}s, should be < 0.001s"


class TestVideoLoaderFunctionality:
    """Functionality tests for VideoLoader"""
    
    @pytest.fixture
    def video_loader(self):
        return VideoLoader()
    
    def test_supported_formats(self, video_loader):
        """Test supported format detection"""
        assert video_loader._is_supported_format("test.mp4")
        assert video_loader._is_supported_format("test.avi")
        assert video_loader._is_supported_format("TEST.MP4")  # Case insensitive
        assert not video_loader._is_supported_format("test.mov")
        assert not video_loader._is_supported_format("test.mkv")
    
    def test_unsupported_format_error(self, video_loader):
        """Test error handling for unsupported formats"""
        with pytest.raises(VideoProcessingError, match="Unsupported format"):
            video_loader.load_video("test.mov")
    
    def test_video_not_found_error(self, video_loader):
        """Test error handling for missing files"""
        with pytest.raises(VideoProcessingError, match="Video file not found"):
            video_loader.load_video("nonexistent.mp4")
    
    @patch('cv2.VideoCapture')
    def test_corrupted_video_handling(self, mock_capture, video_loader):
        """Test handling of corrupted video files"""
        # Mock corrupted video that can't be opened
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_capture.return_value = mock_cap
        
        with pytest.raises(VideoProcessingError, match="Cannot open video"):
            video_loader.load_video("corrupted.mp4")
    
    @patch('cv2.VideoCapture')
    def test_video_metadata_accuracy(self, mock_capture, video_loader):
        """Test accuracy of extracted video metadata"""
        # Mock video capture with known properties
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 1920,
            cv2.CAP_PROP_FRAME_HEIGHT: 1080,
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 900
        }.get(prop, 0)
        mock_capture.return_value = mock_cap
        
        metadata = video_loader.load_video("test.mp4")
        
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.fps == 30.0
        assert metadata.frame_count == 900
        assert metadata.duration == 30.0  # 900 frames / 30 fps
    
    @patch('cv2.VideoCapture')
    def test_get_video_stream(self, mock_capture, video_loader):
        """Test video stream acquisition"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_capture.return_value = mock_cap
        
        stream = video_loader.get_video_stream("test.mp4")
        
        assert stream is not None
        # Verify buffer size optimization
        mock_cap.set.assert_called_with(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    @patch('cv2.VideoCapture')
    def test_validate_video_success(self, mock_capture, video_loader):
        """Test video validation for valid video"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 100
        }.get(prop, 0)
        mock_capture.return_value = mock_cap
        
        is_valid = video_loader.validate_video("test.mp4")
        
        assert is_valid is True
    
    def test_validate_video_failure(self, video_loader):
        """Test video validation for invalid video"""
        is_valid = video_loader.validate_video("nonexistent.mp4")
        
        assert is_valid is False
    
    @patch('cv2.VideoCapture')
    def test_get_frame_at_position(self, mock_capture, video_loader):
        """Test specific frame extraction"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        
        # Mock successful frame read
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, test_frame)
        mock_capture.return_value = mock_cap
        
        frame = video_loader.get_frame_at_position("test.mp4", 50)
        
        assert frame is not None
        assert frame.shape == (480, 640, 3)
        mock_cap.set.assert_called_with(cv2.CAP_PROP_POS_FRAMES, 50)
        mock_cap.release.assert_called_once()
    
    @patch('cv2.VideoCapture')
    def test_get_frame_at_position_failure(self, mock_capture, video_loader):
        """Test frame extraction failure"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)  # Failed read
        mock_capture.return_value = mock_cap
        
        frame = video_loader.get_frame_at_position("test.mp4", 50)
        
        assert frame is None


class TestVideoMetadata:
    """Test VideoMetadata dataclass"""
    
    def test_video_metadata_creation(self):
        """Test VideoMetadata object creation"""
        metadata = VideoMetadata(
            path="test.mp4",
            width=1920,
            height=1080,
            fps=30.0,
            frame_count=900,
            duration=30.0
        )
        
        assert metadata.path == "test.mp4"
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.fps == 30.0
        assert metadata.frame_count == 900
        assert metadata.duration == 30.0


class TestVideoLoaderIntegration:
    """Integration tests for VideoLoader"""
    
    @pytest.fixture
    def video_loader(self):
        return VideoLoader()
    
    @patch('cv2.setUseOptimized')
    @patch('cv2.setNumThreads')
    def test_opencv_optimization_configuration(self, mock_set_threads, mock_set_optimized, video_loader):
        """Test OpenCV optimization configuration"""
        # VideoLoader should configure OpenCV optimizations in __init__
        mock_set_optimized.assert_called_with(True)
        mock_set_threads.assert_called_with(-1)  # Use all cores
    
    def test_error_inheritance(self):
        """Test error class inheritance"""
        assert issubclass(VideoProcessingError, Exception)
        
        error = VideoProcessingError("Test error")
        assert str(error) == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])