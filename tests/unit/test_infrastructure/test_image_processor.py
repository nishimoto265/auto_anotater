"""
Unit tests for ImageProcessor - High-performance image processing engine
Performance target: 4K→display size 50ms or less
"""

import pytest
import os
import time
import cv2
import numpy as np
from unittest.mock import patch, MagicMock

from src.infrastructure.image.image_processor import (
    ImageProcessor, ImageInfo, ImageProcessingError
)


class TestImageProcessorPerformance:
    """Performance tests for ImageProcessor"""
    
    @pytest.fixture
    def image_processor(self):
        return ImageProcessor()
    
    @pytest.fixture
    def sample_4k_image(self):
        """Create a sample 4K image for testing"""
        return np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
    
    @pytest.fixture
    def sample_1080p_image(self):
        """Create a sample 1080p image for testing"""
        return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    def test_4k_to_display_resize_50ms(self, image_processor, sample_4k_image):
        """Test 4K→display size resize under 50ms (critical requirement)"""
        target_sizes = [
            (1920, 1080),  # 1080p
            (1280, 720),   # 720p
            (640, 360)     # 360p
        ]
        
        for target_width, target_height in target_sizes:
            start_time = time.perf_counter()
            
            resized = image_processor.resize_for_display(
                sample_4k_image, target_width, target_height
            )
            
            elapsed_time = time.perf_counter() - start_time
            
            assert elapsed_time < 0.05, f"4K resize to {target_width}x{target_height} took {elapsed_time}s, should be < 0.05s"
            assert resized.shape[:2] == (target_height, target_width) or resized.shape[0] <= target_height
    
    def test_thumbnail_generation_10ms(self, image_processor, sample_1080p_image):
        """Test thumbnail generation under 10ms"""
        start_time = time.perf_counter()
        
        thumbnail = image_processor.create_thumbnail(sample_1080p_image, size=200)
        
        elapsed_time = time.perf_counter() - start_time
        
        assert elapsed_time < 0.01, f"Thumbnail generation took {elapsed_time}s, should be < 0.01s"
        assert max(thumbnail.shape[:2]) <= 200
    
    def test_memory_efficient_processing(self, image_processor, sample_4k_image):
        """Test memory efficiency with large images"""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Force garbage collection before test
        gc.collect()
        initial_memory = process.memory_info().rss
        
        # Process multiple large images
        for i in range(5):
            resized = image_processor.resize_for_display(sample_4k_image, 1920, 1080)
            del resized
        
        gc.collect()
        final_memory = process.memory_info().rss
        
        # Memory usage should not increase significantly
        memory_increase = (final_memory - initial_memory) / (1024 * 1024)  # MB
        assert memory_increase < 100, f"Memory usage increased by {memory_increase}MB, should be < 100MB"
    
    def test_batch_resize_efficiency(self, image_processor):
        """Test batch processing efficiency"""
        # Create test images
        test_images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(10)
        ]
        
        start_time = time.perf_counter()
        
        resized_images = image_processor.batch_resize_images(test_images, 320, 240)
        
        elapsed_time = time.perf_counter() - start_time
        
        assert elapsed_time < 0.1, f"Batch resize took {elapsed_time}s, should be < 0.1s"
        assert len(resized_images) == 10
        assert all(img.shape[:2] == (240, 320) for img in resized_images if img is not None)


class TestImageProcessorFunctionality:
    """Functionality tests for ImageProcessor"""
    
    @pytest.fixture
    def image_processor(self):
        return ImageProcessor()
    
    @pytest.fixture
    def sample_image(self):
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    def test_load_image_success(self, image_processor, tmp_path):
        """Test successful image loading"""
        # Create test image file
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        image_path = tmp_path / "test_image.jpg"
        cv2.imwrite(str(image_path), test_image)
        
        loaded_image = image_processor.load_image(str(image_path))
        
        assert loaded_image is not None
        assert loaded_image.shape == test_image.shape
    
    def test_load_image_not_found(self, image_processor):
        """Test error handling for missing image files"""
        with pytest.raises(ImageProcessingError, match="Image not found"):
            image_processor.load_image("nonexistent.jpg")
    
    @patch('cv2.imread')
    def test_load_image_corrupted(self, mock_imread, image_processor):
        """Test error handling for corrupted image files"""
        mock_imread.return_value = None  # Simulate corrupted image
        
        with pytest.raises(ImageProcessingError, match="Cannot load image"):
            image_processor.load_image("corrupted.jpg")
    
    def test_resize_maintain_aspect_ratio(self, image_processor, sample_image):
        """Test resize with aspect ratio maintenance"""
        # Original is 640x480 (4:3 ratio)
        resized = image_processor.resize_for_display(sample_image, 800, 600, maintain_aspect=True)
        
        # Should maintain 4:3 ratio
        height, width = resized.shape[:2]
        aspect_ratio = width / height
        original_aspect = 640 / 480
        
        assert abs(aspect_ratio - original_aspect) < 0.01
        assert width <= 800 and height <= 600
    
    def test_resize_without_aspect_ratio(self, image_processor, sample_image):
        """Test resize without aspect ratio maintenance"""
        resized = image_processor.resize_for_display(sample_image, 800, 400, maintain_aspect=False)
        
        assert resized.shape[:2] == (400, 800)
    
    def test_resize_to_multiple_sizes(self, image_processor, sample_image):
        """Test resizing to multiple sizes efficiently"""
        sizes = [(320, 240), (640, 480), (160, 120)]
        
        results = image_processor.resize_to_multiple_sizes(sample_image, sizes)
        
        assert len(results) == 3
        for (width, height) in sizes:
            assert (width, height) in results
            result_img = results[(width, height)]
            assert result_img.shape[1] <= width and result_img.shape[0] <= height
    
    def test_get_image_info(self, image_processor, sample_image):
        """Test image information extraction"""
        info = image_processor.get_image_info(sample_image)
        
        assert isinstance(info, ImageInfo)
        assert info.width == 640
        assert info.height == 480
        assert info.channels == 3
        assert info.dtype == 'uint8'
        assert info.size_bytes == sample_image.nbytes
    
    def test_get_image_info_invalid(self, image_processor):
        """Test image info with invalid input"""
        with pytest.raises(ImageProcessingError, match="Invalid image"):
            image_processor.get_image_info(None)
    
    def test_convert_color_space_rgb(self, image_processor, sample_image):
        """Test color space conversion to RGB"""
        rgb_image = image_processor.convert_color_space(sample_image, 'RGB')
        
        assert rgb_image.shape == sample_image.shape
        # RGB and BGR should be different (unless image is grayscale)
        assert not np.array_equal(rgb_image, sample_image)
    
    def test_convert_color_space_gray(self, image_processor, sample_image):
        """Test color space conversion to grayscale"""
        gray_image = image_processor.convert_color_space(sample_image, 'GRAY')
        
        assert len(gray_image.shape) == 2  # Grayscale has no channel dimension
        assert gray_image.shape == (480, 640)
    
    def test_convert_color_space_hsv(self, image_processor, sample_image):
        """Test color space conversion to HSV"""
        hsv_image = image_processor.convert_color_space(sample_image, 'HSV')
        
        assert hsv_image.shape == sample_image.shape
    
    def test_convert_color_space_unsupported(self, image_processor, sample_image):
        """Test error handling for unsupported color space"""
        with pytest.raises(ImageProcessingError, match="Unsupported color space"):
            image_processor.convert_color_space(sample_image, 'XYZ')
    
    def test_enhance_image_quality(self, image_processor, sample_image):
        """Test image quality enhancement"""
        enhanced = image_processor.enhance_image_quality(sample_image)
        
        assert enhanced.shape == sample_image.shape
        assert enhanced.dtype == sample_image.dtype
    
    def test_crop_image_valid(self, image_processor, sample_image):
        """Test image cropping with valid boundaries"""
        cropped = image_processor.crop_image(sample_image, 100, 50, 200, 150)
        
        assert cropped.shape == (150, 200, 3)
    
    def test_crop_image_boundary_clipping(self, image_processor, sample_image):
        """Test image cropping with boundary clipping"""
        # Try to crop outside image boundaries
        cropped = image_processor.crop_image(sample_image, 600, 400, 200, 200)
        
        # Should clip to image boundaries
        assert cropped.shape[0] <= 200  # Height clipped
        assert cropped.shape[1] <= 200  # Width clipped
    
    def test_calculate_optimal_display_size(self, image_processor):
        """Test optimal display size calculation"""
        optimal_width, optimal_height = image_processor.calculate_optimal_display_size(
            1920, 1080, 800, 600
        )
        
        # Should maintain aspect ratio and fit within constraints
        assert optimal_width <= 800
        assert optimal_height <= 600
        
        # Should maintain 16:9 aspect ratio (approximately)
        aspect_ratio = optimal_width / optimal_height
        original_aspect = 1920 / 1080
        assert abs(aspect_ratio - original_aspect) < 0.01


class TestImageProcessorOptimization:
    """Test optimization features of ImageProcessor"""
    
    @pytest.fixture
    def image_processor(self):
        return ImageProcessor()
    
    def test_get_optimal_interpolation_upscaling(self, image_processor):
        """Test optimal interpolation for upscaling"""
        interpolation = image_processor._get_optimal_interpolation(640, 480, 1280, 960)
        
        # Upscaling should use cubic interpolation
        assert interpolation == cv2.INTER_CUBIC
    
    def test_get_optimal_interpolation_major_downscaling(self, image_processor):
        """Test optimal interpolation for major downscaling"""
        interpolation = image_processor._get_optimal_interpolation(1920, 1080, 480, 270)
        
        # Major downscaling should use area interpolation
        assert interpolation == cv2.INTER_AREA
    
    def test_get_optimal_interpolation_minor_downscaling(self, image_processor):
        """Test optimal interpolation for minor downscaling"""
        interpolation = image_processor._get_optimal_interpolation(640, 480, 480, 360)
        
        # Minor downscaling should use linear interpolation
        assert interpolation == cv2.INTER_LINEAR
    
    def test_optimize_for_cache(self, image_processor):
        """Test cache optimization"""
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        optimized = image_processor.optimize_for_cache(test_image)
        
        # For now, should return the same image
        assert np.array_equal(optimized, test_image)


class TestImageProcessorIntegration:
    """Integration tests for ImageProcessor"""
    
    @patch('cv2.setUseOptimized')
    @patch('cv2.setNumThreads') 
    @patch('cv2.setBufferAreaMaxSize')
    def test_opencv_optimization_configuration(self, mock_buffer, mock_threads, mock_optimized):
        """Test OpenCV optimization configuration"""
        processor = ImageProcessor()
        
        mock_optimized.assert_called_with(True)
        mock_threads.assert_called_with(-1)  # Use all cores
        mock_buffer.assert_called_with(1024 * 1024 * 100)  # 100MB buffer
    
    def test_gpu_mode_initialization(self):
        """Test GPU mode initialization"""
        processor_cpu = ImageProcessor(use_gpu=False)
        processor_gpu = ImageProcessor(use_gpu=True)
        
        assert processor_cpu.use_gpu is False
        assert processor_gpu.use_gpu is True
    
    def test_error_inheritance(self):
        """Test error class inheritance"""
        assert issubclass(ImageProcessingError, Exception)
        
        error = ImageProcessingError("Test error")
        assert str(error) == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])