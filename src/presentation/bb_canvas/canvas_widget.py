"""
Agent1 Presentation - BBCanvas
バウンディングボックス描画キャンバス・OpenGL高速描画

性能要件:
- フレーム表示更新: 50ms以下（Cache連携）
- BB描画更新: 16ms以下（60fps維持）
- マウス応答: 5ms以下
- ズーム操作: 100ms以下
"""

import time
import math
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, 
    QApplication
)
from PyQt6.QtCore import (
    Qt, QPointF, QRectF, QSizeF, QTimer, pyqtSignal,
    QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPixmap, 
    QWheelEvent, QMouseEvent, QPaintEvent, QFont
)
try:
    from PyQt6.QtOpenGL import QOpenGLWidget as OpenGLWidget
    OPENGL_AVAILABLE = True
except ImportError:
    OpenGLWidget = None
    OPENGL_AVAILABLE = False

from .bb_renderer import BBRenderer
from .mouse_handler import MouseHandler
from .zoom_controller import ZoomController


@dataclass
class BBEntity:
    """BBエンティティ"""
    id: str
    x: float  # YOLO normalized coordinates
    y: float
    w: float
    h: float
    individual_id: int  # 0-15
    action_id: int      # 0-4
    confidence: float   # 0.0-1.0
    color: QColor
    
    def to_pixel_rect(self, image_width: int, image_height: int) -> QRectF:
        """YOLO座標からピクセル座標に変換"""
        px = self.x * image_width - (self.w * image_width) / 2
        py = self.y * image_height - (self.h * image_height) / 2
        pw = self.w * image_width
        ph = self.h * image_height
        return QRectF(px, py, pw, ph)


class BBCanvas(QGraphicsView):
    """
    バウンディングボックス描画キャンバス
    
    性能要件:
    - フレーム表示更新: 50ms以下（Cache連携）
    - BB描画更新: 16ms以下（60fps維持）
    - マウス応答: 5ms以下
    - ズーム操作: 100ms以下
    """
    
    # シグナル定義
    bb_created = pyqtSignal(float, float, float, float)  # x, y, w, h
    bb_selected = pyqtSignal(str)  # bb_id
    zoom_changed = pyqtSignal(float)  # zoom_level
    frame_display_time = pyqtSignal(float)  # フレーム表示時間（ms）
    
    # 色定義（16個体用）
    ID_COLORS = [
        QColor(255, 0, 0),    # 0: Red
        QColor(0, 255, 0),    # 1: Green
        QColor(0, 0, 255),    # 2: Blue
        QColor(255, 255, 0),  # 3: Yellow
        QColor(255, 0, 255),  # 4: Magenta
        QColor(0, 255, 255),  # 5: Cyan
        QColor(255, 128, 0),  # 6: Orange
        QColor(128, 0, 255),  # 7: Purple
        QColor(255, 192, 203),# 8: Pink
        QColor(165, 42, 42),  # 9: Brown
        QColor(128, 128, 128),# 10: Gray
        QColor(0, 128, 0),    # 11: Dark Green
        QColor(0, 0, 128),    # 12: Navy
        QColor(128, 128, 0),  # 13: Olive
        QColor(128, 0, 128),  # 14: Maroon
        QColor(0, 128, 128),  # 15: Teal
    ]
    
    def __init__(self, parent=None, use_opengl: bool = True):
        super().__init__(parent)
        
        # 性能監視
        self.performance_timer = QTimer()
        self.frame_times = []
        self.render_times = []
        
        # OpenGL設定
        self.use_opengl = use_opengl and OPENGL_AVAILABLE
        if self.use_opengl and OpenGLWidget:
            try:
                self.setViewport(OpenGLWidget())
                self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
            except Exception as e:
                print(f"OpenGL setup failed: {e}, falling back to software rendering")
                self.use_opengl = False
        
        # 基本設定
        self.setup_graphics_view()
        
        # 描画エンジン
        self.bb_renderer = BBRenderer(use_opengl=use_opengl)
        
        # マウス・ズーム制御
        self.mouse_handler = MouseHandler(self)
        self.zoom_controller = ZoomController(self)
        
        # 状態管理
        self.current_frame_pixmap: Optional[QPixmap] = None
        self.current_bbs: List[BBEntity] = []
        self.selected_bb_id: Optional[str] = None
        self.creation_mode = False
        self.current_id = 0
        self.current_action = 0
        
        # 画像情報
        self.image_width = 1920
        self.image_height = 1080
        
        # 性能測定用
        self.last_render_time = 0
        self.fps_counter = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)  # 1秒毎にFPS更新
        
        # シグナル接続
        self.connect_signals()
        
    def setup_graphics_view(self):
        """グラフィックスビュー初期化"""
        # シーン作成
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 描画設定（高速化）
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        
        # キャッシュ設定
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        
        # スクロールバー設定
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # マウス追跡
        self.setMouseTracking(True)
        
        # ドラッグモード
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
    def connect_signals(self):
        """シグナル接続"""
        self.mouse_handler.bb_drag_finished.connect(self.on_bb_drag_finished)
        self.mouse_handler.bb_selection_changed.connect(self.on_bb_selection_changed)
        self.zoom_controller.zoom_changed.connect(self.on_zoom_changed)
        
    # ==================== フレーム表示（50ms以下必達） ====================
    
    def display_frame(self, frame_pixmap: QPixmap) -> float:
        """
        フレーム表示（50ms以下必達）
        
        Args:
            frame_pixmap: 表示するフレーム画像
            
        Returns:
            float: 表示時間（ms）
        """
        start_time = time.perf_counter()
        
        try:
            # 前回の画像をクリア
            if hasattr(self, 'frame_item') and self.frame_item:
                self.scene.removeItem(self.frame_item)
                
            # 新しい画像設定
            self.current_frame_pixmap = frame_pixmap
            self.frame_item = QGraphicsPixmapItem(frame_pixmap)
            self.scene.addItem(self.frame_item)
            
            # 画像サイズ更新
            self.image_width = frame_pixmap.width()
            self.image_height = frame_pixmap.height()
            
            # シーンサイズ調整
            self.scene.setSceneRect(frame_pixmap.rect())
            
            # ビューを画像にフィット（初回のみ）
            if not hasattr(self, 'view_fitted'):
                self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
                self.view_fitted = True
                
            # BBを再描画
            self.update_bounding_boxes_fast()
            
        except Exception as e:
            print(f"Frame display error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        
        # 性能監視
        if elapsed > 50:
            print(f"WARNING: Frame display took {elapsed:.2f}ms (>50ms)")
        
        self.frame_display_time.emit(elapsed)
        return elapsed
        
    # ==================== BB描画（16ms以下必達） ====================
    
    def update_bounding_boxes(self, bb_list: List[Dict[str, Any]]) -> float:
        """
        BB描画更新（16ms以下必達）
        
        Args:
            bb_list: BBリスト
            
        Returns:
            float: 描画時間（ms）
        """
        start_time = time.perf_counter()
        
        # BBエンティティ変換
        self.current_bbs = []
        for bb_data in bb_list:
            bb_entity = BBEntity(
                id=bb_data.get('id', f"bb_{len(self.current_bbs)}"),
                x=bb_data.get('x', 0.5),
                y=bb_data.get('y', 0.5),
                w=bb_data.get('w', 0.1),
                h=bb_data.get('h', 0.1),
                individual_id=bb_data.get('individual_id', 0),
                action_id=bb_data.get('action_id', 0),
                confidence=bb_data.get('confidence', 1.0),
                color=self.ID_COLORS[bb_data.get('individual_id', 0) % 16]
            )
            self.current_bbs.append(bb_entity)
            
        # 高速描画実行
        elapsed = self.update_bounding_boxes_fast()
        
        # 性能監視
        if elapsed > 16:
            print(f"WARNING: BB rendering took {elapsed:.2f}ms (>16ms)")
            
        return elapsed
        
    def update_bounding_boxes_fast(self) -> float:
        """高速BB描画（差分描画）"""
        start_time = time.perf_counter()
        
        if not self.current_frame_pixmap:
            return 0
            
        # BBレンダラーで描画
        render_time = self.bb_renderer.render_bbs(
            self.current_bbs,
            self.image_width,
            self.image_height,
            self.transform()
        )
        
        # 描画結果をシーンに適用
        if hasattr(self.bb_renderer, 'rendered_items'):
            for item in self.bb_renderer.rendered_items:
                if item not in self.scene.items():
                    self.scene.addItem(item)
                    
        elapsed = (time.perf_counter() - start_time) * 1000
        self.last_render_time = elapsed
        self.fps_counter += 1
        
        return elapsed
        
    # ==================== マウス操作（5ms以下） ====================
    
    def mousePressEvent(self, event: QMouseEvent):
        """マウス押下処理（5ms以下必達）"""
        start_time = time.perf_counter()
        
        self.mouse_handler.handle_mouse_press(event)
        super().mousePressEvent(event)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Mouse press took {elapsed:.2f}ms (>5ms)")
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """マウス移動処理（5ms以下必達）"""
        start_time = time.perf_counter()
        
        self.mouse_handler.handle_mouse_move(event)
        super().mouseMoveEvent(event)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Mouse move took {elapsed:.2f}ms (>5ms)")
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """マウス離上処理（5ms以下必達）"""
        start_time = time.perf_counter()
        
        self.mouse_handler.handle_mouse_release(event)
        super().mouseReleaseEvent(event)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Mouse release took {elapsed:.2f}ms (>5ms)")
            
    # ==================== ズーム操作（100ms以下） ====================
    
    def wheelEvent(self, event: QWheelEvent):
        """ホイールイベント処理（100ms以下必達）"""
        start_time = time.perf_counter()
        
        self.zoom_controller.handle_wheel_event(event)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 100:
            print(f"WARNING: Wheel event took {elapsed:.2f}ms (>100ms)")
            
    def zoom_to_level(self, zoom_level: float):
        """指定レベルまでズーム"""
        self.zoom_controller.zoom_to_level(zoom_level)
        
    def zoom_to_fit(self):
        """画像全体にフィット"""
        if self.current_frame_pixmap:
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
    # ==================== イベントハンドラー ====================
    
    def on_bb_drag_finished(self, start_pos: QPointF, end_pos: QPointF):
        """BBドラッグ完了処理"""
        if not self.creation_mode:
            return
            
        # ピクセル座標をYOLO座標に変換
        scene_start = self.mapToScene(start_pos.toPoint())
        scene_end = self.mapToScene(end_pos.toPoint())
        
        x = (scene_start.x() + scene_end.x()) / 2 / self.image_width
        y = (scene_start.y() + scene_end.y()) / 2 / self.image_height
        w = abs(scene_end.x() - scene_start.x()) / self.image_width
        h = abs(scene_end.y() - scene_start.y()) / self.image_height
        
        # 範囲チェック
        if w > 0.01 and h > 0.01:  # 最小サイズチェック
            self.bb_created.emit(x, y, w, h)
            
    def on_bb_selection_changed(self, bb_id: Optional[str]):
        """BB選択変更処理"""
        self.selected_bb_id = bb_id
        if bb_id:
            self.bb_selected.emit(bb_id)
            
    def on_zoom_changed(self, zoom_level: float):
        """ズーム変更処理"""
        self.zoom_changed.emit(zoom_level)
        
    # ==================== 公開メソッド ====================
    
    def toggle_creation_mode(self):
        """BB作成モード切り替え"""
        self.creation_mode = not self.creation_mode
        self.mouse_handler.set_creation_mode(self.creation_mode)
        
    def set_current_id(self, id_number: int):
        """現在ID設定"""
        self.current_id = max(0, min(id_number, 15))
        
    def set_current_action(self, action_id: int):
        """現在行動設定"""
        self.current_action = max(0, min(action_id, 4))
        
    def get_selected_bb(self):
        """選択BB取得"""
        if self.selected_bb_id:
            for bb in self.current_bbs:
                if bb.id == self.selected_bb_id:
                    return bb
        return None
        
    def select_bb(self, bb_id: str):
        """BB選択"""
        self.selected_bb_id = bb_id
        self.bb_selected.emit(bb_id)
        
    def cancel_current_action(self):
        """現在アクションキャンセル"""
        self.creation_mode = False
        self.mouse_handler.cancel_current_action()
        
    def get_current_zoom(self) -> float:
        """現在ズーム取得"""
        return self.zoom_controller.get_current_zoom()
        
    # ==================== 性能監視 ====================
    
    def update_fps(self):
        """FPS更新"""
        current_fps = self.fps_counter
        self.fps_counter = 0
        
        # 性能情報表示（デバッグ用）
        if hasattr(self, 'parent') and hasattr(self.parent(), 'update_status'):
            status = f"FPS: {current_fps} | Render: {self.last_render_time:.1f}ms"
            self.parent().update_status(status)
            
    def get_performance_info(self) -> Dict[str, Any]:
        """性能情報取得"""
        return {
            'use_opengl': self.use_opengl,
            'last_render_time': self.last_render_time,
            'current_fps': self.fps_counter,
            'bb_count': len(self.current_bbs),
            'zoom_level': self.zoom_controller.get_current_zoom(),
            'image_size': (self.image_width, self.image_height),
        }