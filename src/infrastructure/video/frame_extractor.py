"""
Frame Extractor - High-performance frame extraction engine
Performance target: 30fps→5fps real-time conversion
"""

import cv2
import os
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Optional, List
from dataclasses import dataclass

from .video_loader import VideoLoader, VideoProcessingError


@dataclass
class FrameExtractionResult:
    """Frame extraction operation result"""
    total_frames: int
    output_dir: str
    target_fps: int
    processing_time: float
    success: bool = True
    error_message: Optional[str] = None


class FrameExtractor:
    """
    High-performance frame extraction engine
    
    Performance requirements:
    - Frame conversion: 30fps→5fps real-time
    - Output quality: JPEG 90% quality
    - Parallel processing: Multi-threaded execution
    - Progress reporting: Real-time progress callbacks
    """
    
    def __init__(self, thread_count: Optional[int] = None):
        self.thread_count = thread_count or min(multiprocessing.cpu_count(), 8)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.thread_count)
        self.video_loader = VideoLoader()
        
        # Configure OpenCV for optimal performance
        cv2.setUseOptimized(True)
        cv2.setNumThreads(self.thread_count)
        
    def extract_frames(self, 
                      video_path: str, 
                      output_dir: str,
                      target_fps: int = 5, 
                      quality: int = 90,
                      progress_callback: Optional[Callable[[float], None]] = None) -> FrameExtractionResult:
        """
        Extract frames from video with real-time performance
        
        Args:
            video_path: Input video path
            output_dir: Output directory for frames
            target_fps: Target FPS (default 5)
            quality: JPEG quality (default 90)
            progress_callback: Progress callback function
            
        Returns:
            FrameExtractionResult: Extraction result with statistics
        """
        start_time = time.time()
        
        try:
            # Load video metadata
            video_metadata = self.video_loader.load_video(video_path)
            
            # Calculate frame skip ratio
            fps_ratio = video_metadata.fps / target_fps
            expected_frames = int(video_metadata.frame_count / fps_ratio)
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract frames with optimized processing
            extracted_count = self._extract_frames_optimized(
                video_path, 
                output_dir, 
                fps_ratio, 
                quality,
                expected_frames,
                progress_callback
            )
            
            processing_time = time.time() - start_time
            
            return FrameExtractionResult(
                total_frames=extracted_count,
                output_dir=output_dir,
                target_fps=target_fps,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return FrameExtractionResult(
                total_frames=0,
                output_dir=output_dir,
                target_fps=target_fps,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
            
    def _extract_frames_optimized(self,
                                 video_path: str,
                                 output_dir: str,
                                 fps_ratio: float,
                                 quality: int,
                                 expected_frames: int,
                                 progress_callback: Optional[Callable[[float], None]]) -> int:
        """
        Optimized frame extraction with parallel processing
        """
        cap = self.video_loader.get_video_stream(video_path)
        
        try:
            frame_number = 0
            extracted_count = 0
            futures: List[Future] = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Check if this frame should be extracted based on FPS ratio
                if frame_number % int(fps_ratio) == 0:
                    output_path = os.path.join(output_dir, f"{extracted_count:06d}.jpg")
                    
                    # Submit frame saving to thread pool
                    future = self.thread_pool.submit(
                        self._save_frame_optimized, 
                        frame.copy(),  # Copy frame to avoid race conditions
                        output_path, 
                        quality
                    )
                    futures.append(future)
                    extracted_count += 1
                    
                    # Report progress
                    if progress_callback and expected_frames > 0:
                        progress = min(extracted_count / expected_frames, 1.0)
                        progress_callback(progress)
                    
                    # Manage thread pool size to prevent memory overflow
                    if len(futures) >= self.thread_count * 2:
                        self._wait_for_completed_futures(futures)
                        
                frame_number += 1
                
            # Wait for all remaining tasks to complete
            self._wait_for_all_futures(futures)
            
            return extracted_count
            
        finally:
            cap.release()
            
    def _save_frame_optimized(self, frame, output_path: str, quality: int) -> bool:
        """
        Optimized frame saving with error handling
        
        Args:
            frame: Frame data (numpy array)
            output_path: Output file path
            quality: JPEG quality (0-100)
            
        Returns:
            bool: True if successful
        """
        try:
            # Use optimized JPEG encoding parameters
            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, quality,
                cv2.IMWRITE_JPEG_OPTIMIZE, 1,
                cv2.IMWRITE_JPEG_PROGRESSIVE, 1
            ]
            
            success = cv2.imwrite(output_path, frame, encode_params)
            return success
            
        except Exception as e:
            print(f"Error saving frame {output_path}: {e}")
            return False
            
    def _wait_for_completed_futures(self, futures: List[Future], max_wait: int = 10):
        """
        Wait for some futures to complete to manage memory usage
        """
        completed = 0
        for future in futures[:]:
            if future.done():
                futures.remove(future)
                completed += 1
                if completed >= max_wait:
                    break
                    
    def _wait_for_all_futures(self, futures: List[Future]):
        """
        Wait for all futures to complete
        """
        for future in futures:
            future.result()  # This will raise exception if task failed
            
    def extract_single_frame(self, 
                           video_path: str, 
                           frame_number: int, 
                           output_path: str,
                           quality: int = 90) -> bool:
        """
        Extract single frame from video
        
        Args:
            video_path: Input video path
            frame_number: Frame number to extract (0-based)
            output_path: Output file path
            quality: JPEG quality
            
        Returns:
            bool: True if successful
        """
        try:
            frame = self.video_loader.get_frame_at_position(video_path, frame_number)
            if frame is not None:
                return self._save_frame_optimized(frame, output_path, quality)
            return False
            
        except Exception:
            return False
            
    def get_frame_count_estimate(self, video_path: str, target_fps: int = 5) -> int:
        """
        Estimate number of frames that will be extracted
        
        Args:
            video_path: Input video path
            target_fps: Target FPS
            
        Returns:
            int: Estimated frame count
        """
        try:
            metadata = self.video_loader.load_video(video_path)
            fps_ratio = metadata.fps / target_fps
            return int(metadata.frame_count / fps_ratio)
        except VideoProcessingError:
            return 0
            
    def cleanup(self):
        """
        Cleanup resources
        """
        self.thread_pool.shutdown(wait=True)
        
    def __del__(self):
        """
        Destructor to ensure cleanup
        """
        try:
            self.cleanup()
        except:
            pass