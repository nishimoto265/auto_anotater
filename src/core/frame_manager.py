import os
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, Future
import time

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
        
        # Threading support
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.state_update_futures: Dict[int, Future] = {}
        
        # Performance tracking
        self.frame_switch_times: List[float] = []
        self.last_switch_time = 0.0

    def initialize(self, total_frames: int) -> None:
        self.total_frames = total_frames
        self.current_frame = 0
        
        with self.lock:
            self.frame_states.clear()
            self.change_frames.clear()
            self.frame_switch_times.clear()
            
        self._preload_frames_async()

    def move_to_frame(self, frame_number: int) -> bool:
        start_time = time.time()
        
        if not 0 <= frame_number < self.total_frames:
            return False
            
        with self.lock:
            self.current_frame = frame_number
            
        # Start async operations
        self._preload_frames_async()
        self._update_frame_state_async(frame_number)
        
        # Track performance
        switch_time = time.time() - start_time
        self.frame_switch_times.append(switch_time)
        self.last_switch_time = switch_time
        
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

    def _preload_frames_async(self) -> None:
        """非同期でフレームを先読み"""
        # Submit preload task to thread pool
        self.executor.submit(self._do_preload_frames)

    def _do_preload_frames(self) -> None:
        """実際の先読み処理"""
        with self.lock:
            current = self.current_frame
            
        # Call image cache to preload range
        self.image_cache.preload_range(current)
        
        # Also update frame states for nearby frames
        start = max(0, current - 10)
        end = min(self.total_frames, current + 10)
        
        for frame_num in range(start, end):
            if frame_num != current:  # Current frame is updated separately
                self._update_frame_state_async(frame_num)
    
    def _update_frame_state_async(self, frame_number: int) -> None:
        """非同期でフレーム状態を更新"""
        # Check if already updating
        if frame_number in self.state_update_futures:
            future = self.state_update_futures[frame_number]
            if not future.done():
                return  # Already updating
                
        # Submit update task
        future = self.executor.submit(self._do_update_frame_state, frame_number)
        self.state_update_futures[frame_number] = future
        
    def _do_update_frame_state(self, frame_number: int) -> None:
        """実際のフレーム状態更新処理"""
        try:
            annotations = self.annotation_manager.get_annotations(frame_number)
            
            state = FrameState(
                frame_number=frame_number,
                is_loaded=self.image_cache.is_loaded(frame_number),
                is_annotated=bool(annotations),
                bb_count=len(annotations) if annotations else 0
            )
            
            with self.lock:
                self.frame_states[frame_number] = state
                
            # Clean up future reference
            if frame_number in self.state_update_futures:
                del self.state_update_futures[frame_number]
                
        except Exception as e:
            print(f"Error updating frame state {frame_number}: {e}")

    def _detect_bb_changes(self, prev_bbs: List[dict], curr_bbs: List[dict]) -> bool:
        if len(prev_bbs) != len(curr_bbs):
            return True
            
        prev_set = {tuple(bb.items()) for bb in prev_bbs}
        curr_set = {tuple(bb.items()) for bb in curr_bbs}
        
        return prev_set != curr_set

    def get_progress_stats(self) -> dict:
        with self.lock:
            annotated = sum(1 for state in self.frame_states.values() if state.is_annotated)
            avg_switch_time = sum(self.frame_switch_times) / len(self.frame_switch_times) if self.frame_switch_times else 0.0
            
        return {
            "total_frames": self.total_frames,
            "annotated_frames": annotated,
            "progress_percentage": (annotated / self.total_frames * 100) if self.total_frames else 0,
            "change_frames_count": len(self.change_frames),
            "avg_frame_switch_ms": avg_switch_time * 1000,
            "last_switch_ms": self.last_switch_time * 1000,
            "cache_stats": self.image_cache.get_cache_stats()
        }

    def cleanup(self) -> None:
        # Cancel pending tasks
        for future in self.state_update_futures.values():
            future.cancel()
            
        with self.lock:
            self.frame_states.clear()
            self.change_frames.clear()
            self.state_update_futures.clear()
            self.frame_switch_times.clear()
            
        self.image_cache.clear()
        
    def shutdown(self) -> None:
        """スレッドプールをシャットダウン"""
        self.executor.shutdown(wait=True)
        self.image_cache.shutdown()