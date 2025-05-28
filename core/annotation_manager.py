import os
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

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
        
    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return json.load(f)

    def load_annotations(self, frame_dir: str) -> None:
        self.annotations.clear()
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
        self._auto_save()

    def update_bbox(self, frame_num: int, bbox_idx: int, bbox: BoundingBox) -> None:
        if frame_num in self.annotations and bbox_idx < len(self.annotations[frame_num]):
            self.annotations[frame_num][bbox_idx] = bbox
            self.modified = True
            self._auto_save()

    def delete_bbox(self, frame_num: int, bbox_idx: int) -> None:
        if frame_num in self.annotations and bbox_idx < len(self.annotations[frame_num]):
            del self.annotations[frame_num][bbox_idx]
            self.modified = True
            self._auto_save()

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

    def _auto_save(self) -> None:
        current_time = time.time()
        if (current_time - self.last_save_time) >= self.auto_save_interval:
            self.save_annotations(self.current_frame)
            self.last_save_time = current_time
            self.modified = False

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
        };