import os
import json
import time
import numpy as np
import threading
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

class SaveStatus(Enum):
    IDLE = "idle"
    SAVING = "saving" 
    SUCCESS = "success"
    ERROR = "error"

@dataclass
class BoundingBox:
    individual_id: int
    x: float  # YOLO format (normalized)
    y: float
    w: float 
    h: float
    action_id: int
    confidence: float

class AnnotationManager:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.annotations: Dict[int, List[BoundingBox]] = {}
        self.current_frame = 0
        self.auto_save_interval = self.config["performance"]["auto_save_interval"]
        self.last_save_time = 0
        self.modified = False
        self.frame_dir = None
        
        # Auto-save state
        self.save_status = SaveStatus.IDLE
        self.save_status_callback: Optional[Callable[[SaveStatus], None]] = None
        self.save_error_callback: Optional[Callable[[str], None]] = None
        self.auto_save_timer = None
        self.save_thread = None
        self.save_lock = threading.Lock()
        self.retry_count = 0
        self.max_retries = 3
        
    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return json.load(f)

    def load_annotations(self, frame_dir: str) -> None:
        self.frame_dir = frame_dir
        self.annotations.clear()
        
        # Start auto-save timer
        self._start_auto_save_timer()
        
        for file in sorted(Path(frame_dir).glob("*.txt")):
            frame_num = int(file.stem)
            self.annotations[frame_num] = []
            
            try:
                with open(file, 'r') as f:
                    for line in f:
                        values = line.strip().split()
                        if len(values) != 7:
                            continue
                        
                        bbox = BoundingBox(
                            individual_id=int(values[0]),
                            x=float(values[1]),
                            y=float(values[2]), 
                            w=float(values[3]),
                            h=float(values[4]),
                            action_id=int(values[5]),
                            confidence=float(values[6])
                        )
                        self.annotations[frame_num].append(bbox)
            except Exception as e:
                print(f"Error loading frame {frame_num}: {e}")
                self._restore_backup(file)

    def save_annotations(self, frame_dir: str, frame_num: Optional[int] = None) -> None:
        if frame_num is not None:
            frames = [frame_num]
        else:
            frames = list(self.annotations.keys())
            
        for frame in frames:
            if frame not in self.annotations:
                continue
                
            file_path = Path(frame_dir) / f"{frame:06d}.txt"
            backup_path = file_path.with_suffix(".bak")
            
            # Create backup
            if file_path.exists():
                file_path.rename(backup_path)
            
            try:
                with open(file_path, 'w') as f:
                    for bbox in self.annotations[frame]:
                        line = f"{bbox.individual_id} {bbox.x:.6f} {bbox.y:.6f} "
                        line += f"{bbox.w:.6f} {bbox.h:.6f} {bbox.action_id} "
                        line += f"{bbox.confidence:.6f}\n"
                        f.write(line)
                        
                if backup_path.exists():
                    backup_path.unlink()
                    
            except Exception as e:
                print(f"Error saving frame {frame}: {e}")
                if backup_path.exists():
                    backup_path.rename(file_path)

    def add_bbox(self, frame_num: int, bbox: BoundingBox) -> None:
        if frame_num not in self.annotations:
            self.annotations[frame_num] = []
        self.annotations[frame_num].append(bbox)
        self.modified = True

    def update_bbox(self, frame_num: int, bbox_idx: int, bbox: BoundingBox) -> None:
        if frame_num in self.annotations and bbox_idx < len(self.annotations[frame_num]):
            self.annotations[frame_num][bbox_idx] = bbox
            self.modified = True

    def delete_bbox(self, frame_num: int, bbox_idx: int) -> None:
        if frame_num in self.annotations and bbox_idx < len(self.annotations[frame_num]):
            del self.annotations[frame_num][bbox_idx]
            self.modified = True

    def get_frame_annotations(self, frame_num: int) -> List[BoundingBox]:
        return self.annotations.get(frame_num, [])

    def validate_bbox(self, bbox: BoundingBox) -> bool:
        if not (0 <= bbox.x <= 1 and 0 <= bbox.y <= 1):
            return False
        if not (0 < bbox.w <= 1 and 0 < bbox.h <= 1):
            return False
        if not (0 <= bbox.individual_id < 16):
            return False
        if not (0 <= bbox.confidence <= 1):
            return False
        return True

    def _start_auto_save_timer(self) -> None:
        """Start the auto-save timer."""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
        
        self.auto_save_timer = threading.Timer(
            self.auto_save_interval, 
            self._auto_save_check
        )
        self.auto_save_timer.daemon = True
        self.auto_save_timer.start()
    
    def _auto_save_check(self) -> None:
        """Check if auto-save is needed and perform it."""
        if self.modified and self.frame_dir:
            self._perform_background_save()
        
        # Restart the timer
        self._start_auto_save_timer()
    
    def _perform_background_save(self) -> None:
        """Perform save operation in background thread."""
        if self.save_thread and self.save_thread.is_alive():
            return  # Previous save still in progress
        
        self.save_thread = threading.Thread(
            target=self._background_save_with_retry
        )
        self.save_thread.daemon = True
        self.save_thread.start()
    
    def _background_save_with_retry(self) -> None:
        """Background save with retry logic."""
        with self.save_lock:
            self._update_save_status(SaveStatus.SAVING)
            self.retry_count = 0
            
            while self.retry_count < self.max_retries:
                try:
                    self.save_annotations(self.frame_dir)
                    self.modified = False
                    self.last_save_time = time.time()
                    self._update_save_status(SaveStatus.SUCCESS)
                    return
                except Exception as e:
                    self.retry_count += 1
                    error_msg = f"Auto-save failed (attempt {self.retry_count}/{self.max_retries}): {str(e)}"
                    
                    if self.retry_count < self.max_retries:
                        time.sleep(2)  # Wait before retry
                    else:
                        self._update_save_status(SaveStatus.ERROR)
                        if self.save_error_callback:
                            self.save_error_callback(error_msg)
    
    def _update_save_status(self, status: SaveStatus) -> None:
        """Update save status and notify callback."""
        self.save_status = status
        if self.save_status_callback:
            self.save_status_callback(status)

    def _restore_backup(self, file_path: Path) -> None:
        backup_path = file_path.with_suffix(".bak")
        if backup_path.exists():
            backup_path.rename(file_path)
            print(f"Restored backup for {file_path}")

    def batch_process(self, frame_dir: str, process_func) -> None:
        for frame_num in sorted(self.annotations.keys()):
            try:
                self.annotations[frame_num] = process_func(self.annotations[frame_num])
                self.save_annotations(frame_dir, frame_num)
            except Exception as e:
                print(f"Error in batch processing frame {frame_num}: {e}")
                continue

    def get_statistics(self) -> Dict:
        total_frames = len(self.annotations)
        total_bboxes = sum(len(bboxes) for bboxes in self.annotations.values())
        individual_counts = {i: 0 for i in range(16)}
        action_counts = {}
        
        for bboxes in self.annotations.values():
            for bbox in bboxes:
                individual_counts[bbox.individual_id] += 1
                action_counts[bbox.action_id] = action_counts.get(bbox.action_id, 0) + 1
                
        return {
            "total_frames": total_frames,
            "total_bboxes": total_bboxes,
            "individual_counts": individual_counts,
            "action_counts": action_counts
        }
    
    def set_save_status_callback(self, callback: Callable[[SaveStatus], None]) -> None:
        """Set callback for save status updates."""
        self.save_status_callback = callback
    
    def set_save_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for save errors."""
        self.save_error_callback = callback
    
    def stop_auto_save(self) -> None:
        """Stop the auto-save timer."""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
            self.auto_save_timer = None
    
    def force_save(self) -> None:
        """Force an immediate save."""
        if self.modified and self.frame_dir:
            self._perform_background_save()
    
    def get_save_status(self) -> SaveStatus:
        """Get current save status."""
        return self.save_status
    
    def set_auto_save_interval(self, interval: int) -> None:
        """Update auto-save interval in seconds."""
        self.auto_save_interval = interval
        if self.auto_save_timer:
            self._start_auto_save_timer()