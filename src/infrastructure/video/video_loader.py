"""
Video Loader - OpenCV based video loading engine
Performance target: Real-time loading (1 second video / 1 second processing)
"""

import cv2
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class VideoMetadata:
    """Video metadata container"""
    path: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration: float


class InfrastructureError(Exception):
    """Infrastructure layer base error"""
    pass


class VideoProcessingError(InfrastructureError):
    """Video processing specific error"""
    pass


class VideoLoader:
    """
    Video loading engine using OpenCV
    
    Performance requirements:
    - Video loading: Real-time speed (1 second video / 1 second processing)
    - Supported formats: mp4, avi
    - Supported resolutions: Up to 4K (3840x2160)
    - Memory efficiency: Streaming loading
    """
    
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi']
        # Configure OpenCV for optimal performance
        cv2.setUseOptimized(True)
        cv2.setNumThreads(-1)  # Use all available cores
        
    def load_video(self, video_path: str) -> VideoMetadata:
        """
        Load video and extract metadata (real-time performance required)
        
        Args:
            video_path: Path to video file
            
        Returns:
            VideoMetadata: Video metadata information
            
        Raises:
            VideoProcessingError: If video cannot be loaded or unsupported format
        """
        if not os.path.exists(video_path):
            raise VideoProcessingError(f"Video file not found: {video_path}")
            
        if not self._is_supported_format(video_path):
            raise VideoProcessingError(f"Unsupported format: {video_path}")
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise VideoProcessingError(f"Cannot open video: {video_path}")
            
        try:
            # Extract metadata efficiently
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0.0
            
            metadata = VideoMetadata(
                path=video_path,
                width=width,
                height=height,
                fps=fps,
                frame_count=frame_count,
                duration=duration
            )
            
            return metadata
            
        finally:
            cap.release()
            
    def get_video_stream(self, video_path: str) -> cv2.VideoCapture:
        """
        Get video stream for efficient frame-by-frame processing
        
        Args:
            video_path: Path to video file
            
        Returns:
            cv2.VideoCapture: Video capture object
            
        Raises:
            VideoProcessingError: If video cannot be opened
        """
        if not os.path.exists(video_path):
            raise VideoProcessingError(f"Video file not found: {video_path}")
            
        if not self._is_supported_format(video_path):
            raise VideoProcessingError(f"Unsupported format: {video_path}")
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise VideoProcessingError(f"Cannot open video: {video_path}")
            
        # Optimize for performance
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer
        
        return cap
        
    def validate_video(self, video_path: str) -> bool:
        """
        Validate video file integrity and format support
        
        Args:
            video_path: Path to video file
            
        Returns:
            bool: True if video is valid and supported
        """
        try:
            metadata = self.load_video(video_path)
            return (metadata.width > 0 and 
                   metadata.height > 0 and 
                   metadata.frame_count > 0 and
                   metadata.fps > 0)
        except VideoProcessingError:
            return False
            
    def _is_supported_format(self, video_path: str) -> bool:
        """
        Check if video format is supported
        
        Args:
            video_path: Path to video file
            
        Returns:
            bool: True if format is supported
        """
        return any(video_path.lower().endswith(fmt) for fmt in self.supported_formats)
        
    def get_frame_at_position(self, video_path: str, frame_number: int) -> Optional[cv2.Mat]:
        """
        Extract specific frame from video
        
        Args:
            video_path: Path to video file
            frame_number: Frame number to extract (0-based)
            
        Returns:
            cv2.Mat or None: Frame data if successful
        """
        cap = self.get_video_stream(video_path)
        
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            if ret:
                return frame
            return None
            
        finally:
            cap.release()