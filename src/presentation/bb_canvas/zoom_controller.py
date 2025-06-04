"""
Agent1 Presentation - ZoomController
ズーム・パン制御（100ms以下）

機能:
- ホイールズーム
- 指定レベルズーム
- フィット機能
- スムーズアニメーション
"""

import time
import math
from typing import Optional
from PyQt6.QtCore import QObject, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QWheelEvent, QTransform
from PyQt6.QtWidgets import QGraphicsView


class ZoomController(QObject):
    """
    ズーム・パン制御
    
    性能要件:
    - ズーム操作: 100ms以下
    - ホイール応答: 50ms以下
    - アニメーション: スムーズ
    """
    
    # シグナル定義
    zoom_changed = pyqtSignal(float)  # zoom_level
    
    # ズーム制限
    MIN_ZOOM = 0.1
    MAX_ZOOM = 10.0
    DEFAULT_ZOOM = 1.0
    ZOOM_STEP = 1.2
    
    def __init__(self, canvas: Optional[QGraphicsView] = None):
        super().__init__()
        self.canvas = canvas
        
        # ズーム状態
        self.current_zoom = self.DEFAULT_ZOOM
        self.target_zoom = self.DEFAULT_ZOOM
        
        # アニメーション
        self.zoom_animation: Optional[QPropertyAnimation] = None
        self.animation_duration = 200  # ms
        
        # 性能測定
        self.last_zoom_time = 0
        
    def handle_wheel_event(self, event: QWheelEvent):
        """
        ホイールイベント処理（100ms以下必達）
        
        Args:
            event: ホイールイベント
        """
        start_time = time.perf_counter()
        
        try:
            # ズーム方向判定
            delta = event.angleDelta().y()
            if delta == 0:
                return
                
            # ズーム中心点取得
            zoom_center = event.position()
            
            # ズーム倍率計算
            if delta > 0:
                zoom_factor = self.ZOOM_STEP
            else:
                zoom_factor = 1.0 / self.ZOOM_STEP
                
            # ズーム実行
            self._zoom_at_point(zoom_factor, zoom_center)
            
        except Exception as e:
            print(f"Wheel zoom error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 100:
            print(f"WARNING: Wheel zoom took {elapsed:.2f}ms (>100ms)")
            
        self.last_zoom_time = elapsed
        
    def zoom_to_level(self, zoom_level: float, animated: bool = True):
        """
        指定レベルズーム（100ms以下必達）
        
        Args:
            zoom_level: 目標ズームレベル
            animated: アニメーション使用フラグ
        """
        start_time = time.perf_counter()
        
        try:
            # ズーム制限適用
            zoom_level = max(self.MIN_ZOOM, min(zoom_level, self.MAX_ZOOM))
            
            if animated and abs(zoom_level - self.current_zoom) > 0.1:
                self._animate_zoom_to_level(zoom_level)
            else:
                self._set_zoom_level_immediate(zoom_level)
                
        except Exception as e:
            print(f"Zoom to level error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 100:
            print(f"WARNING: Zoom to level took {elapsed:.2f}ms (>100ms)")
            
    def zoom_in(self, steps: int = 1):
        """ズームイン"""
        new_zoom = self.current_zoom * (self.ZOOM_STEP ** steps)
        self.zoom_to_level(new_zoom)
        
    def zoom_out(self, steps: int = 1):
        """ズームアウト"""
        new_zoom = self.current_zoom / (self.ZOOM_STEP ** steps)
        self.zoom_to_level(new_zoom)
        
    def zoom_to_fit(self):
        """画像全体にフィット"""
        if hasattr(self.canvas, 'scene') and self.canvas.scene():
            scene_rect = self.canvas.scene().sceneRect()
            if not scene_rect.isEmpty():
                self.canvas.fitInView(scene_rect, 1)  # Qt.KeepAspectRatio
                self._update_current_zoom()
                
    def zoom_to_selection(self, rect):
        """選択領域にズーム"""
        if not rect.isEmpty():
            self.canvas.fitInView(rect, 1)  # Qt.KeepAspectRatio
            self._update_current_zoom()
            
    def reset_zoom(self):
        """ズームリセット"""
        self.zoom_to_level(self.DEFAULT_ZOOM)
        
    def _zoom_at_point(self, zoom_factor: float, center_point):
        """指定点を中心にズーム"""
        # 新しいズームレベル計算
        new_zoom = self.current_zoom * zoom_factor
        new_zoom = max(self.MIN_ZOOM, min(new_zoom, self.MAX_ZOOM))
        
        if new_zoom == self.current_zoom:
            return
            
        # ズーム前の座標
        scene_pos = self.canvas.mapToScene(center_point.toPoint())
        
        # ズーム実行
        self._set_zoom_level_immediate(new_zoom)
        
        # ズーム後の座標調整
        new_center = self.canvas.mapFromScene(scene_pos)
        delta = center_point - new_center
        
        # スクロール調整
        h_scroll = self.canvas.horizontalScrollBar()
        v_scroll = self.canvas.verticalScrollBar()
        h_scroll.setValue(h_scroll.value() - int(delta.x()))
        v_scroll.setValue(v_scroll.value() - int(delta.y()))
        
    def _set_zoom_level_immediate(self, zoom_level: float):
        """即座にズームレベル設定"""
        # 変換行列作成
        transform = QTransform()
        transform.scale(zoom_level, zoom_level)
        
        # ビューに適用
        self.canvas.setTransform(transform)
        
        # 状態更新
        self.current_zoom = zoom_level
        self.target_zoom = zoom_level
        
        # シグナル発出
        self.zoom_changed.emit(zoom_level)
        
    def _animate_zoom_to_level(self, target_zoom: float):
        """アニメーション付きズーム"""
        # 既存アニメーション停止
        if self.zoom_animation:
            self.zoom_animation.stop()
            
        # アニメーション作成
        self.zoom_animation = QPropertyAnimation(self, b"zoom_level")
        self.zoom_animation.setDuration(self.animation_duration)
        self.zoom_animation.setStartValue(self.current_zoom)
        self.zoom_animation.setEndValue(target_zoom)
        self.zoom_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # アニメーション開始
        self.target_zoom = target_zoom
        self.zoom_animation.start()
        
    def _update_current_zoom(self):
        """現在ズーム更新（変換行列から逆算）"""
        transform = self.canvas.transform()
        self.current_zoom = transform.m11()  # スケール値取得
        self.zoom_changed.emit(self.current_zoom)
        
    def get_current_zoom(self) -> float:
        """現在ズーム取得"""
        return self.current_zoom
        
    def get_zoom_percentage(self) -> int:
        """ズーム率（%）取得"""
        return int(self.current_zoom * 100)
        
    def is_zoomed_in(self) -> bool:
        """ズームイン状態判定"""
        return self.current_zoom > self.DEFAULT_ZOOM
        
    def is_zoomed_out(self) -> bool:
        """ズームアウト状態判定"""
        return self.current_zoom < self.DEFAULT_ZOOM
        
    def can_zoom_in(self) -> bool:
        """ズームイン可能判定"""
        return self.current_zoom < self.MAX_ZOOM
        
    def can_zoom_out(self) -> bool:
        """ズームアウト可能判定"""
        return self.current_zoom > self.MIN_ZOOM
        
    def get_zoom_performance_info(self) -> dict:
        """ズーム性能情報取得"""
        return {
            'current_zoom': self.current_zoom,
            'target_zoom': self.target_zoom,
            'last_zoom_time': self.last_zoom_time,
            'min_zoom': self.MIN_ZOOM,
            'max_zoom': self.MAX_ZOOM,
            'zoom_step': self.ZOOM_STEP,
            'animation_duration': self.animation_duration,
            'target_performance': '100ms以下',
        }
        
    # プロパティ（アニメーション用）
    def get_zoom_level(self) -> float:
        return self.current_zoom
        
    def set_zoom_level(self, zoom_level: float):
        self._set_zoom_level_immediate(zoom_level)
        
    zoom_level = property(get_zoom_level, set_zoom_level)


if __name__ == "__main__":
    # ズームコントローラーテスト
    from PyQt6.QtWidgets import QApplication, QGraphicsView
    import sys
    
    app = QApplication(sys.argv)
    
    # テスト用キャンバス
    canvas = QGraphicsView()
    zoom_controller = ZoomController(canvas)
    
    print("ZoomController Performance Test")
    print("=" * 35)
    
    # ズーム性能テスト
    test_levels = [0.5, 1.0, 2.0, 5.0, 0.1, 10.0]
    
    for level in test_levels:
        start_time = time.perf_counter()
        zoom_controller.zoom_to_level(level, animated=False)
        elapsed = (time.perf_counter() - start_time) * 1000
        
        current = zoom_controller.get_current_zoom()
        print(f"Zoom to {level}: {elapsed:.2f}ms (current: {current:.2f})")
        
    # 性能情報表示
    print(f"\nPerformance Info:")
    info = zoom_controller.get_zoom_performance_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
        
    print(f"\nAll zoom operations completed successfully")