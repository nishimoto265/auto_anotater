import os
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

@dataclass
class FrameState:
    frame_number: int
    is_loaded: bool
    is_annotated: bool
    bb_count: int
    error_state: Optional[str] = None

class ChangeType(Enum):
    BB_ADDED = "added"
    BB_REMOVED = "removed"
    BB_MODIFIED = "modified"
    NO_CHANGE = "no_change"

class FrameManager:
    def __init__(self, image_cache, annotation_manager):
        self.image_cache = image_cache
        self.annotation_manager = annotation_manager
        self.current_frame = 0
        self.total_frames = 0
        self.frame_states: Dict[int, FrameState] = {}
        self.change_frames: List[int] = []
        self.preload_range = 100

    def initialize(self, total_frames: int) -> None:
        self.total_frames = total_frames
        self.current_frame = 0
        self.frame_states.clear()
        self.change_frames.clear()
        self._preload_frames()

    def move_to_frame(self, frame_number: int) -> bool:
        if not 0 <= frame_number < self.total_frames:
            return False
            
        self.current_frame = frame_number
        self._preload_frames()
        self._update_frame_state(frame_number)
        return True

    def next_frame(self) -> bool:
        return self.move_to_frame(self.current_frame + 1)

    def prev_frame(self) -> bool:
        return self.move_to_frame(self.current_frame - 1)

    def jump_to_next_change(self) -> bool:
        next_changes = [f for f in self.change_frames if f > self.current_frame]
        if next_changes:
            return self.move_to_frame(min(next_changes))
        return False

    def jump_to_prev_change(self) -> bool:
        prev_changes = [f for f in self.change_frames if f < self.current_frame]
        if prev_changes:
            return self.move_to_frame(max(prev_changes))
        return False

    def get_frame_state(self, frame_number: int) -> Optional[FrameState]:
        return self.frame_states.get(frame_number)

    def detect_changes(self, frame_range: Optional[Tuple[int, int]] = None) -> List[int]:
        if frame_range is None:
            frame_range = (0, self.total_frames)
            
        start, end = frame_range
        changes = []
        
        for frame in range(start, end):
            prev_bbs = self.annotation_manager.get_annotations(frame - 1)
            curr_bbs = self.annotation_manager.get_annotations(frame)
            
            if self._detect_bb_changes(prev_bbs, curr_bbs):
                changes.append(frame)
                
        self.change_frames = sorted(list(set(self.change_frames + changes)))
        return changes

    def _preload_frames(self) -> None:
        start = max(0, self.current_frame - self.preload_range)
        end = min(self.total_frames, self.current_frame + self.preload_range)
        
        self.image_cache.preload_range(start, end)

    def _update_frame_state(self, frame_number: int) -> None:
        annotations = self.annotation_manager.get_annotations(frame_number)
        
        self.frame_states[frame_number] = FrameState(
            frame_number=frame_number,
            is_loaded=self.image_cache.is_loaded(frame_number),
            is_annotated=bool(annotations),
            bb_count=len(annotations) if annotations else 0
        )

    def _detect_bb_changes(self, prev_bbs: List[dict], curr_bbs: List[dict]) -> bool:
        if len(prev_bbs) != len(curr_bbs):
            return True
            
        prev_set = {tuple(bb.items()) for bb in prev_bbs}
        curr_set = {tuple(bb.items()) for bb in curr_bbs}
        
        return prev_set != curr_set

    def get_progress_stats(self) -> dict:
        annotated = sum(1 for state in self.frame_states.values() if state.is_annotated)
        return {
            "total_frames": self.total_frames,
            "annotated_frames": annotated,
            "progress_percentage": (annotated / self.total_frames * 100) if self.total_frames else 0,
            "change_frames_count": len(self.change_frames)
        }

    def cleanup(self) -> None:
        self.frame_states.clear()
        self.change_frames.clear()
        self.image_cache.clear()