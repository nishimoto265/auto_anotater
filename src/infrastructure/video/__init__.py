"""Video processing module - OpenCV based video handling"""

from .video_loader import VideoLoader, VideoMetadata
from .frame_extractor import FrameExtractor, FrameExtractionResult

__all__ = [
    'VideoLoader',
    'VideoMetadata',
    'FrameExtractor', 
    'FrameExtractionResult'
]