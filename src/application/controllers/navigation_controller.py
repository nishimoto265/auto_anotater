"""
NavigationController - Agent2 Application Layer
ナビゲーション制御コントローラー（FrameControllerのサブセット）

機能:
- フレーム間ナビゲーション制御
- ジャンプ機能
- ナビゲーション履歴管理
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import time

from .frame_controller import FrameController, FrameSwitchRequest


@dataclass
class NavigationHistory:
    """ナビゲーション履歴"""
    frame_id: str
    timestamp: float
    action: str  # "next", "previous", "jump"


class NavigationController:
    """
    ナビゲーション制御コントローラー
    """
    
    def __init__(self, frame_controller: FrameController, max_history=50):
        """
        初期化
        
        Args:
            frame_controller: フレームコントローラー
            max_history: 最大履歴保持数
        """
        self.frame_controller = frame_controller
        self.max_history = max_history
        self._history: List[NavigationHistory] = []
        self._current_frame: Optional[str] = None
    
    def go_next(self, auto_save: bool = True) -> bool:
        """次フレームに移動"""
        if not self._current_frame:
            return False
        
        next_frame = self.frame_controller.get_next_frame_id(self._current_frame)
        if not next_frame:
            return False
        
        request = FrameSwitchRequest(
            current_frame_id=self._current_frame,
            target_frame_id=next_frame,
            auto_save=auto_save
        )
        
        result = self.frame_controller.switch_to_frame(request)
        if result.success:
            self._add_history(next_frame, "next")
            self._current_frame = next_frame
        
        return result.success
    
    def go_previous(self, auto_save: bool = True) -> bool:
        """前フレームに移動"""
        if not self._current_frame:
            return False
        
        prev_frame = self.frame_controller.get_previous_frame_id(self._current_frame)
        if not prev_frame:
            return False
        
        request = FrameSwitchRequest(
            current_frame_id=self._current_frame,
            target_frame_id=prev_frame,
            auto_save=auto_save
        )
        
        result = self.frame_controller.switch_to_frame(request)
        if result.success:
            self._add_history(prev_frame, "previous")
            self._current_frame = prev_frame
        
        return result.success
    
    def jump_to(self, target_frame_id: str, auto_save: bool = True) -> bool:
        """指定フレームにジャンプ"""
        if not self.frame_controller.validate_frame_id(target_frame_id):
            return False
        
        current = self._current_frame or "unknown"
        result = self.frame_controller.jump_to_frame(target_frame_id, current)
        
        if result.success:
            self._add_history(target_frame_id, "jump")
            self._current_frame = target_frame_id
        
        return result.success
    
    def set_current_frame(self, frame_id: str):
        """現在フレーム設定"""
        if self.frame_controller.validate_frame_id(frame_id):
            self._current_frame = frame_id
    
    def get_current_frame(self) -> Optional[str]:
        """現在フレーム取得"""
        return self._current_frame
    
    def get_navigation_history(self) -> List[NavigationHistory]:
        """ナビゲーション履歴取得"""
        return self._history.copy()
    
    def _add_history(self, frame_id: str, action: str):
        """履歴追加"""
        history = NavigationHistory(
            frame_id=frame_id,
            timestamp=time.time(),
            action=action
        )
        
        self._history.append(history)
        
        # 履歴サイズ制限
        if len(self._history) > self.max_history:
            self._history.pop(0)
    
    def clear_history(self):
        """履歴クリア"""
        self._history.clear()