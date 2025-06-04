"""
Unit tests for FrameExtractor - High-performance frame extraction engine
Performance target: 30fps→5fps real-time conversion
"""

import pytest
import os
import time
import cv2
import numpy as np
from unittest.mock import patch, MagicMock, call
from concurrent.futures import Future

from src.infrastructure.video.frame_extractor import (
    FrameExtractor, FrameExtractionResult
)
from src.infrastructure.video.video_loader import VideoMetadata, VideoProcessingError


class TestFrameExtractorPerformance:
    """Performance tests for FrameExtractor"""
    
    @pytest.fixture
    def frame_extractor(self):
        return FrameExtractor(thread_count=2)  # Use 2 threads for testing
    
    @pytest.fixture
    def sample_video_metadata(self):
        return VideoMetadata(
            path="test.mp4",
            width=640,
            height=480,
            fps=30.0,
            frame_count=150,  # 5 seconds at 30fps
            duration=5.0
        )
    
    @patch('src.infrastructure.video.frame_extractor.VideoLoader')
    @patch('cv2.VideoCapture')
    def test_fps_conversion_30_to_5_real_time(self, mock_capture, mock_loader_class, 
                                             frame_extractor, sample_video_metadata, tmp_path):
        """Test 30fps→5fps conversion meets real-time performance"""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load_video.return_value = sample_video_metadata
        mock_loader.get_video_stream.return_value = self._create_mock_video_stream(150)
        mock_loader_class.return_value = mock_loader
        
        output_dir = tmp_path / "frames"
        
        start_time = time.perf_counter()
        
        result = frame_extractor.extract_frames(
            "test.mp4",
            str(output_dir),
            target_fps=5
        )
        
        elapsed_time = time.perf_counter() - start_time
        
        # Should process 5 seconds of video in less than 5 seconds (real-time)
        assert elapsed_time < 5.0, f"Frame extraction took {elapsed_time}s, should be < 5s"
        assert result.success is True
        # Should extract 25 frames (5 seconds * 5 fps)
        assert result.total_frames == 25
    
    def test_parallel_frame_extraction_efficiency(self, frame_extractor):
        """Test parallel processing efficiency with multiple threads"""
        # Test with different thread counts
        extractors = [
            FrameExtractor(thread_count=1),
            FrameExtractor(thread_count=4)
        ]
        
        processing_times = []
        
        for extractor in extractors:
            # Mock heavy frame saving operation
            with patch.object(extractor, '_save_frame_optimized', 
                            side_effect=lambda *args: time.sleep(0.01)):  # 10ms per frame
                
                with patch.object(extractor.video_loader, 'load_video',
                                return_value=VideoMetadata("test.mp4", 640, 480, 30.0, 30, 1.0)):
                    with patch.object(extractor.video_loader, 'get_video_stream',
                                    return_value=self._create_mock_video_stream(30)):
                        
                        start_time = time.perf_counter()
                        extractor._extract_frames_optimized("test.mp4", "/tmp", 6.0, 90, 5, None)
                        elapsed = time.perf_counter() - start_time
                        processing_times.append(elapsed)
            
            extractor.cleanup()
        
        # Multi-threaded should be faster than single-threaded
        assert processing_times[1] < processing_times[0], "Multi-threading should improve performance"
    
    def test_jpeg_quality_90_output_performance(self, frame_extractor, tmp_path):
        """Test JPEG quality 90% output meets performance requirements"""
        # Create test frame
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        output_path = tmp_path / "test_frame.jpg"
        
        start_time = time.perf_counter()
        
        success = frame_extractor._save_frame_optimized(test_frame, str(output_path), 90)
        
        elapsed_time = time.perf_counter() - start_time
        
        assert success is True
        assert elapsed_time < 0.1, f"Frame saving took {elapsed_time}s, should be < 0.1s"
        assert output_path.exists()
    
    def _create_mock_video_stream(self, frame_count):
        """Helper to create mock video stream"""
        mock_cap = MagicMock()
        
        # Create frames that will be "read" from video
        frames = []
        for i in range(frame_count):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:, :, i % 3] = 255  # Different color pattern
            frames.append(frame)
        
        # Mock read() to return frames sequentially
        read_calls = [(True, frame) for frame in frames] + [(False, None)]
        mock_cap.read.side_effect = read_calls
        
        return mock_cap


class TestFrameExtractorFunctionality:
    """Functionality tests for FrameExtractor"""
    
    @pytest.fixture
    def frame_extractor(self):
        return FrameExtractor(thread_count=2)
    
    def test_extract_frames_with_progress(self, frame_extractor, tmp_path):
        """Test frame extraction with progress callback"""
        progress_calls = []
        
        def progress_callback(progress):
            progress_calls.append(progress)
        
        with patch.object(frame_extractor.video_loader, 'load_video',
                         return_value=VideoMetadata("test.mp4", 640, 480, 30.0, 60, 2.0)):
            with patch.object(frame_extractor.video_loader, 'get_video_stream',
                            return_value=self._create_mock_video_stream(60)):
                
                result = frame_extractor.extract_frames(
                    "test.mp4",
                    str(tmp_path),
                    target_fps=5,
                    progress_callback=progress_callback
                )
        
        assert result.success is True
        assert len(progress_calls) > 0
        assert all(0.0 <= p <= 1.0 for p in progress_calls)
        assert progress_calls[-1] == pytest.approx(1.0, rel=0.1)
    
    def test_fps_conversion_accuracy(self, frame_extractor):
        """Test FPS conversion accuracy"""
        # 30fps → 5fps should extract every 6th frame
        with patch.object(frame_extractor.video_loader, 'load_video',
                         return_value=VideoMetadata("test.mp4", 640, 480, 30.0, 30, 1.0)):
            
            frame_count_estimate = frame_extractor.get_frame_count_estimate("test.mp4", 5)
            
            # 30 frames at 30fps → 5 frames at 5fps
            assert frame_count_estimate == 5
    
    def test_output_filename_format(self, frame_extractor, tmp_path):
        """Test output filename format (000000.jpg～)"""
        with patch.object(frame_extractor.video_loader, 'load_video',
                         return_value=VideoMetadata("test.mp4", 640, 480, 30.0, 18, 0.6)):
            with patch.object(frame_extractor.video_loader, 'get_video_stream',
                            return_value=self._create_mock_video_stream(18)):
                
                result = frame_extractor.extract_frames("test.mp4", str(tmp_path), target_fps=5)
        
        # Check that files are created with correct naming pattern
        expected_files = ["000000.jpg", "000001.jpg", "000002.jpg"]
        for expected_file in expected_files:
            assert (tmp_path / expected_file).exists(), f"Expected file {expected_file} not found"
    
    def test_jpeg_quality_settings(self, frame_extractor, tmp_path):
        """Test JPEG quality settings"""
        test_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Test different quality settings
        qualities = [50, 90, 95]
        file_sizes = []
        
        for quality in qualities:
            output_path = tmp_path / f"test_q{quality}.jpg"
            success = frame_extractor._save_frame_optimized(test_frame, str(output_path), quality)
            
            assert success is True
            assert output_path.exists()
            file_sizes.append(output_path.stat().st_size)
        
        # Higher quality should produce larger files
        assert file_sizes[0] < file_sizes[1] < file_sizes[2]
    
    def test_async_frame_saving(self, frame_extractor, tmp_path):
        """Test asynchronous frame saving"""
        test_frames = [
            np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            for _ in range(5)
        ]
        
        futures = []
        for i, frame in enumerate(test_frames):
            output_path = tmp_path / f"async_frame_{i}.jpg"
            future = frame_extractor.thread_pool.submit(
                frame_extractor._save_frame_optimized,
                frame, str(output_path), 90
            )
            futures.append(future)
        
        # Wait for all to complete
        results = [future.result() for future in futures]
        
        assert all(results), "All async frame saves should succeed"
        for i in range(5):
            assert (tmp_path / f"async_frame_{i}.jpg").exists()
    
    def test_extract_single_frame(self, frame_extractor, tmp_path):
        """Test single frame extraction"""
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        with patch.object(frame_extractor.video_loader, 'get_frame_at_position',
                         return_value=test_frame):
            
            output_path = tmp_path / "single_frame.jpg"
            success = frame_extractor.extract_single_frame(
                "test.mp4", 100, str(output_path), 90
            )
        
        assert success is True
        assert output_path.exists()
    
    def test_extract_single_frame_failure(self, frame_extractor, tmp_path):
        """Test single frame extraction failure handling"""
        with patch.object(frame_extractor.video_loader, 'get_frame_at_position',
                         return_value=None):
            
            output_path = tmp_path / "failed_frame.jpg"
            success = frame_extractor.extract_single_frame(
                "test.mp4", 100, str(output_path), 90
            )
        
        assert success is False
        assert not output_path.exists()
    
    def test_cleanup_resources(self, frame_extractor):
        """Test resource cleanup"""
        # Submit some tasks
        futures = []
        for i in range(3):
            future = frame_extractor.thread_pool.submit(time.sleep, 0.1)
            futures.append(future)
        
        # Cleanup should wait for tasks to complete
        frame_extractor.cleanup()
        
        # All futures should be done after cleanup
        assert all(future.done() for future in futures)
    
    def _create_mock_video_stream(self, frame_count):
        """Helper to create mock video stream"""
        mock_cap = MagicMock()
        
        frames = []
        for i in range(frame_count):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:, :, i % 3] = 255
            frames.append(frame)
        
        read_calls = [(True, frame) for frame in frames] + [(False, None)]
        mock_cap.read.side_effect = read_calls
        
        return mock_cap


class TestFrameExtractionResult:
    """Test FrameExtractionResult dataclass"""
    
    def test_successful_result(self):
        """Test successful extraction result"""
        result = FrameExtractionResult(
            total_frames=100,
            output_dir="/tmp/frames",
            target_fps=5,
            processing_time=2.5,
            success=True
        )
        
        assert result.total_frames == 100
        assert result.output_dir == "/tmp/frames"
        assert result.target_fps == 5
        assert result.processing_time == 2.5
        assert result.success is True
        assert result.error_message is None
    
    def test_failed_result(self):
        """Test failed extraction result"""
        result = FrameExtractionResult(
            total_frames=0,
            output_dir="/tmp/frames",
            target_fps=5,
            processing_time=0.1,
            success=False,
            error_message="Video not found"
        )
        
        assert result.success is False
        assert result.error_message == "Video not found"


class TestFrameExtractorIntegration:
    """Integration tests for FrameExtractor"""
    
    def test_opencv_optimization_configuration(self):
        """Test OpenCV optimization configuration"""
        with patch('cv2.setUseOptimized') as mock_optimized:
            with patch('cv2.setNumThreads') as mock_threads:
                
                extractor = FrameExtractor(thread_count=4)
                
                mock_optimized.assert_called_with(True)
                mock_threads.assert_called_with(4)
                
                extractor.cleanup()
    
    def test_thread_pool_management(self):
        """Test thread pool initialization and cleanup"""
        extractor = FrameExtractor(thread_count=3)
        
        assert extractor.thread_count == 3
        assert extractor.thread_pool._max_workers == 3
        
        # Test cleanup
        extractor.cleanup()
        
        # Thread pool should be shutdown
        assert extractor.thread_pool._shutdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])