import os
import cv2
import numpy as np
from typing import List, Optional, Callable, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """Video information container"""
    path: str
    fps: float
    total_frames: int
    width: int
    height: int
    duration: float
    

class VideoProcessingError(Exception):
    """Custom exception for video processing errors"""
    pass


class VideoProcessor(QObject):
    """
    Video processor for PyQt6 application.
    Handles video loading, frame extraction with frame rate conversion,
    and supports 4K resolution videos with memory-efficient processing.
    """
    
    # Signals
    progress_updated = pyqtSignal(int, str)  # progress percentage, status message
    frame_processed = pyqtSignal(int, str)  # frame number, output path
    video_loaded = pyqtSignal(dict)  # video info dict
    processing_started = pyqtSignal(str)  # video path
    processing_completed = pyqtSignal(str, int)  # video path, total frames extracted
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.current_video: Optional[cv2.VideoCapture] = None
        self.video_info: Optional[VideoInfo] = None
        self.is_processing = False
        self.should_stop = False
        
        # Processing parameters
        self.target_fps = 5  # Target frame rate for extraction
        self.source_fps = 30  # Default source fps, will be updated per video
        self.output_quality = 95  # JPEG quality (0-100)
        
    def load_video(self, video_path: str) -> VideoInfo:
        """
        Load a video file and extract its information.
        
        Args:
            video_path: Path to the video file (mp4, avi supported)
            
        Returns:
            VideoInfo object containing video metadata
            
        Raises:
            VideoProcessingError: If video cannot be loaded
        """
        if not os.path.exists(video_path):
            raise VideoProcessingError(f"Video file not found: {video_path}")
            
        # Release previous video if any
        if self.current_video:
            self.current_video.release()
            
        # Open video
        self.current_video = cv2.VideoCapture(video_path)
        if not self.current_video.isOpened():
            raise VideoProcessingError(f"Failed to open video: {video_path}")
            
        # Extract video information
        fps = self.current_video.get(cv2.CAP_PROP_FPS)
        total_frames = int(self.current_video.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self.current_video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.current_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        
        self.video_info = VideoInfo(
            path=video_path,
            fps=fps,
            total_frames=total_frames,
            width=width,
            height=height,
            duration=duration
        )
        
        self.source_fps = fps
        
        # Emit signal with video info
        self.video_loaded.emit({
            'path': video_path,
            'fps': fps,
            'total_frames': total_frames,
            'width': width,
            'height': height,
            'duration': duration,
            'is_4k': width >= 3840 or height >= 2160
        })
        
        logger.info(f"Loaded video: {video_path}, {width}x{height}, {fps:.2f}fps, {total_frames} frames")
        
        return self.video_info
        
    def process_video(self, video_path: str, output_dir: str, 
                     target_fps: Optional[float] = None) -> int:
        """
        Process a single video, extracting frames at specified frame rate.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory to save extracted frames
            target_fps: Target frame rate (default: 5 fps)
            
        Returns:
            Number of frames extracted
        """
        if self.is_processing:
            raise VideoProcessingError("Already processing a video")
            
        self.is_processing = True
        self.should_stop = False
        frames_extracted = 0
        
        try:
            # Load video
            video_info = self.load_video(video_path)
            
            # Set target fps
            if target_fps:
                self.target_fps = target_fps
                
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Calculate frame skip interval
            frame_interval = int(self.source_fps / self.target_fps)
            if frame_interval < 1:
                frame_interval = 1
                
            self.processing_started.emit(video_path)
            
            # Process frames
            frame_count = 0
            while True:
                if self.should_stop:
                    logger.info("Processing stopped by user")
                    break
                    
                ret, frame = self.current_video.read()
                if not ret:
                    break
                    
                # Extract frame at target fps interval
                if frame_count % frame_interval == 0:
                    # Generate output filename with 6-digit numbering
                    output_filename = f"{frames_extracted:06d}.jpg"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # Save frame with specified quality
                    # For 4K videos, we might want to consider resizing for memory efficiency
                    # but the requirement asks for full resolution, so we keep it
                    cv2.imwrite(output_path, frame, 
                              [cv2.IMWRITE_JPEG_QUALITY, self.output_quality])
                    
                    frames_extracted += 1
                    self.frame_processed.emit(frames_extracted, output_path)
                    
                frame_count += 1
                
                # Update progress
                progress = int((frame_count / video_info.total_frames) * 100)
                status_msg = f"Processing frame {frame_count}/{video_info.total_frames}"
                self.progress_updated.emit(progress, status_msg)
                
            self.processing_completed.emit(video_path, frames_extracted)
            logger.info(f"Extracted {frames_extracted} frames from {video_path}")
            
            return frames_extracted
            
        except Exception as e:
            error_msg = f"Error processing video: {str(e)}"
            self.error_occurred.emit(error_msg)
            logger.error(error_msg)
            raise VideoProcessingError(error_msg)
            
        finally:
            self.is_processing = False
            if self.current_video:
                self.current_video.release()
                self.current_video = None
                
    def process_multiple_videos(self, video_paths: List[str], 
                              output_base_dir: str,
                              target_fps: Optional[float] = None) -> dict:
        """
        Process multiple videos in sequence.
        
        Args:
            video_paths: List of video file paths
            output_base_dir: Base directory for outputs (subdirs created per video)
            target_fps: Target frame rate for all videos
            
        Returns:
            Dictionary mapping video paths to number of frames extracted
        """
        results = {}
        
        for idx, video_path in enumerate(video_paths):
            if self.should_stop:
                break
                
            # Create output directory for this video
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = os.path.join(output_base_dir, f"{video_name}_frames")
            
            # Update overall progress
            overall_progress = int((idx / len(video_paths)) * 100)
            self.progress_updated.emit(overall_progress, 
                                     f"Processing video {idx+1}/{len(video_paths)}: {video_name}")
            
            try:
                frames = self.process_video(video_path, output_dir, target_fps)
                results[video_path] = frames
            except VideoProcessingError as e:
                logger.error(f"Failed to process {video_path}: {e}")
                results[video_path] = 0
                
        return results
        
    def stop_processing(self):
        """Stop current video processing"""
        self.should_stop = True
        
    def get_memory_efficient_frame(self, frame_number: int) -> Optional[np.ndarray]:
        """
        Get a specific frame from the current video without loading all frames.
        Memory-efficient for 4K videos.
        
        Args:
            frame_number: Frame number to retrieve
            
        Returns:
            Frame as numpy array or None if failed
        """
        if not self.current_video or not self.video_info:
            return None
            
        if frame_number >= self.video_info.total_frames:
            return None
            
        # Seek to specific frame
        self.current_video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.current_video.read()
        
        return frame if ret else None
        
    def estimate_processing_time(self, video_path: str) -> float:
        """
        Estimate processing time for a video based on its properties.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Estimated time in seconds
        """
        try:
            info = self.load_video(video_path)
            
            # Estimate based on resolution and number of frames to extract
            frames_to_extract = info.total_frames / (info.fps / self.target_fps)
            
            # Base time per frame (seconds) - adjust based on resolution
            if info.width >= 3840 or info.height >= 2160:  # 4K
                time_per_frame = 0.1
            elif info.width >= 1920 or info.height >= 1080:  # Full HD
                time_per_frame = 0.05
            else:
                time_per_frame = 0.03
                
            return frames_to_extract * time_per_frame
            
        except Exception:
            return 0.0


class VideoProcessorThread(QThread):
    """
    QThread wrapper for VideoProcessor to enable non-blocking processing.
    """
    
    def __init__(self, processor: VideoProcessor):
        super().__init__()
        self.processor = processor
        self.video_paths: List[str] = []
        self.output_dir = ""
        self.target_fps = 5
        
    def setup(self, video_paths: List[str], output_dir: str, target_fps: float = 5):
        """Setup processing parameters"""
        self.video_paths = video_paths
        self.output_dir = output_dir
        self.target_fps = target_fps
        
    def run(self):
        """Run video processing in thread"""
        try:
            if len(self.video_paths) == 1:
                self.processor.process_video(
                    self.video_paths[0], 
                    self.output_dir, 
                    self.target_fps
                )
            else:
                self.processor.process_multiple_videos(
                    self.video_paths,
                    self.output_dir,
                    self.target_fps
                )
        except Exception as e:
            self.processor.error_occurred.emit(str(e))