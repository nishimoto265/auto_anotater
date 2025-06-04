"""
Image Processor - High-performance image processing engine
Performance target: 4K→display size 50ms or less
"""

import cv2
import numpy as np
import os
from typing import Tuple, Optional
from dataclasses import dataclass

from ..video.video_loader import InfrastructureError


class ImageProcessingError(InfrastructureError):
    """Image processing specific error"""
    pass


@dataclass
class ImageInfo:
    """Image information container"""
    width: int
    height: int
    channels: int
    dtype: str
    size_bytes: int


class ImageProcessor:
    """
    High-performance image processing engine using OpenCV
    
    Performance requirements:
    - 4K→display size conversion: 50ms or less
    - Resize processing: High quality & high speed
    - Cache layer coordination: Efficient cache integration
    - Memory efficiency: Large capacity image support
    """
    
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        
        # Configure OpenCV for optimal performance
        cv2.setUseOptimized(True)
        cv2.setNumThreads(-1)  # Use all available cores
        
        # Set optimal buffer size for large images
        cv2.setBufferAreaMaxSize(1024 * 1024 * 100)  # 100MB buffer
        
    def load_image(self, image_path: str) -> np.ndarray:
        """
        Load image with high performance (50ms or less required)
        
        Args:
            image_path: Path to image file
            
        Returns:
            np.ndarray: Image data
            
        Raises:
            ImageProcessingError: If image cannot be loaded
        """
        if not os.path.exists(image_path):
            raise ImageProcessingError(f"Image not found: {image_path}")
            
        # Use optimized OpenCV loading
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            raise ImageProcessingError(f"Cannot load image: {image_path}")
            
        return image
        
    def resize_for_display(self, 
                          image: np.ndarray, 
                          target_width: int, 
                          target_height: int,
                          maintain_aspect: bool = True) -> np.ndarray:
        """
        Resize image for display (50ms or less required)
        
        Optimized for Cache layer integration and high-speed resizing
        
        Args:
            image: Source image
            target_width: Target width
            target_height: Target height
            maintain_aspect: Whether to maintain aspect ratio
            
        Returns:
            np.ndarray: Resized image
        """
        if image is None or image.size == 0:
            raise ImageProcessingError("Invalid input image")
            
        current_height, current_width = image.shape[:2]
        
        if maintain_aspect:
            # Calculate optimal scale to maintain aspect ratio
            scale = min(target_width / current_width, target_height / current_height)
            new_width = int(current_width * scale)
            new_height = int(current_height * scale)
        else:
            new_width = target_width
            new_height = target_height
            
        # Select optimal interpolation method based on scale
        interpolation = self._get_optimal_interpolation(
            current_width, current_height, new_width, new_height
        )
        
        # Perform optimized resize
        resized = cv2.resize(image, (new_width, new_height), interpolation=interpolation)
        
        return resized
        
    def create_thumbnail(self, image: np.ndarray, size: int = 200) -> np.ndarray:
        """
        Create thumbnail for cache optimization
        
        Args:
            image: Source image
            size: Thumbnail size (square)
            
        Returns:
            np.ndarray: Thumbnail image
        """
        return self.resize_for_display(image, size, size, maintain_aspect=True)
        
    def resize_to_multiple_sizes(self, 
                                image: np.ndarray, 
                                sizes: list) -> dict:
        """
        Resize image to multiple sizes efficiently
        
        Args:
            image: Source image
            sizes: List of (width, height) tuples
            
        Returns:
            dict: Dictionary of size -> resized image
        """
        results = {}
        
        # Sort sizes by area for optimal processing order
        sorted_sizes = sorted(sizes, key=lambda x: x[0] * x[1], reverse=True)
        
        for width, height in sorted_sizes:
            resized = self.resize_for_display(image, width, height, maintain_aspect=True)
            results[(width, height)] = resized
            
        return results
        
    def optimize_for_cache(self, image: np.ndarray) -> np.ndarray:
        """
        Optimize image for Cache layer (memory efficiency & transfer efficiency)
        
        Args:
            image: Source image
            
        Returns:
            np.ndarray: Optimized image
        """
        # For now, return as-is. Can be extended with compression/optimization
        return image
        
    def get_image_info(self, image: np.ndarray) -> ImageInfo:
        """
        Get image information for memory management
        
        Args:
            image: Image data
            
        Returns:
            ImageInfo: Image information
        """
        if image is None:
            raise ImageProcessingError("Invalid image")
            
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        
        return ImageInfo(
            width=width,
            height=height,
            channels=channels,
            dtype=str(image.dtype),
            size_bytes=image.nbytes
        )
        
    def convert_color_space(self, 
                           image: np.ndarray, 
                           target_space: str) -> np.ndarray:
        """
        Convert image color space
        
        Args:
            image: Source image
            target_space: Target color space ('RGB', 'BGR', 'GRAY', 'HSV')
            
        Returns:
            np.ndarray: Converted image
        """
        if target_space == 'RGB':
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif target_space == 'BGR':
            return image  # OpenCV default is BGR
        elif target_space == 'GRAY':
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif target_space == 'HSV':
            return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        else:
            raise ImageProcessingError(f"Unsupported color space: {target_space}")
            
    def enhance_image_quality(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image quality for better display
        
        Args:
            image: Source image
            
        Returns:
            np.ndarray: Enhanced image
        """
        # Apply subtle enhancement for better visual quality
        enhanced = cv2.convertScaleAbs(image, alpha=1.1, beta=10)
        return enhanced
        
    def crop_image(self, 
                   image: np.ndarray, 
                   x: int, y: int, 
                   width: int, height: int) -> np.ndarray:
        """
        Crop image region
        
        Args:
            image: Source image
            x, y: Top-left corner coordinates
            width, height: Crop dimensions
            
        Returns:
            np.ndarray: Cropped image
        """
        img_height, img_width = image.shape[:2]
        
        # Validate crop boundaries
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        width = min(width, img_width - x)
        height = min(height, img_height - y)
        
        return image[y:y+height, x:x+width]
        
    def _get_optimal_interpolation(self, 
                                  src_width: int, src_height: int,
                                  dst_width: int, dst_height: int) -> int:
        """
        Get optimal interpolation method based on scale factor
        
        Args:
            src_width, src_height: Source dimensions
            dst_width, dst_height: Destination dimensions
            
        Returns:
            int: OpenCV interpolation constant
        """
        scale_x = dst_width / src_width
        scale_y = dst_height / src_height
        scale = min(scale_x, scale_y)
        
        if scale > 1.0:
            # Upscaling - use cubic for better quality
            return cv2.INTER_CUBIC
        elif scale < 0.5:
            # Major downscaling - use area for better results
            return cv2.INTER_AREA
        else:
            # Minor downscaling - use linear for speed
            return cv2.INTER_LINEAR
            
    def batch_resize_images(self, 
                           images: list, 
                           target_width: int, 
                           target_height: int) -> list:
        """
        Resize multiple images in batch for efficiency
        
        Args:
            images: List of image arrays
            target_width: Target width
            target_height: Target height
            
        Returns:
            list: List of resized images
        """
        resized_images = []
        
        for image in images:
            if image is not None:
                resized = self.resize_for_display(image, target_width, target_height)
                resized_images.append(resized)
            else:
                resized_images.append(None)
                
        return resized_images
        
    def calculate_optimal_display_size(self, 
                                     image_width: int, 
                                     image_height: int,
                                     max_width: int, 
                                     max_height: int) -> Tuple[int, int]:
        """
        Calculate optimal display size maintaining aspect ratio
        
        Args:
            image_width, image_height: Original image dimensions
            max_width, max_height: Maximum display dimensions
            
        Returns:
            Tuple[int, int]: Optimal (width, height)
        """
        scale = min(max_width / image_width, max_height / image_height)
        
        optimal_width = int(image_width * scale)
        optimal_height = int(image_height * scale)
        
        return optimal_width, optimal_height