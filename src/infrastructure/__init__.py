"""
Infrastructure Layer - Agent4
External resources, technical foundation, OpenCV video processing
"""

# Initialize OpenCV first to handle version compatibility
from .opencv_init import get_opencv_version
_opencv_version = get_opencv_version()

from .video.video_loader import VideoLoader, VideoMetadata
from .video.frame_extractor import FrameExtractor, FrameExtractionResult
from .image.image_processor import ImageProcessor
from .system.memory_manager import MemoryManager, MemoryUsage

__all__ = [
    'VideoLoader',
    'VideoMetadata', 
    'FrameExtractor',
    'FrameExtractionResult',
    'ImageProcessor',
    'MemoryManager',
    'MemoryUsage'
]