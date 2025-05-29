import sys
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QPixmap

from src.core.image_cache import ImageCache
from src.core.bbox_manager import BBoxManager
from src.utils.coordinate_converter import CoordinateConverter
from typing import Dict, Optional

class FrameViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_cache = ImageCache()
        self.bbox_manager = BBoxManager()
        self.coord_converter = CoordinateConverter()
        
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.current_frame = None
        self.selected_bbox = None
        self.drag_start = None
        self.drag_mode = None
        
        # 追跡関連の状態
        self.tracking_states: Dict[int, bool] = {}  # individual_id -> is_tracking
        self.tracking_confidence: Dict[int, float] = {}  # individual_id -> confidence
        self.manual_correction_mode = False
        self.correction_target_id = None
        
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        layout = QVBoxLayout()
        self.image_label = QLabel()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

    def set_frame(self, frame_number):
        self.current_frame = self.image_cache.get_frame(frame_number)
        self.update_display()

    def update_display(self):
        if not self.current_frame:
            return
            
        display_image = QImage(self.current_frame)
        painter = QPainter(display_image)
        
        for bbox in self.bbox_manager.get_bboxes():
            screen_coords = self.coord_converter.yolo_to_screen(
                bbox.coords, 
                self.size(),
                self.zoom_level,
                self.pan_offset
            )
            
            # 追跡中のBBは特別な表示
            is_tracking = self.tracking_states.get(bbox.individual_id, False)
            confidence = self.tracking_confidence.get(bbox.individual_id, 1.0)
            
            if is_tracking:
                # 追跡中は太い線で表示
                color = QColor(bbox.color)
                if confidence < 0.7:
                    # 信頼度が低い場合は色を薄くする
                    color.setAlpha(int(255 * confidence))
                pen = QPen(color, 4)
                
                # 追跡インジケータを描画
                painter.setPen(pen)
                painter.drawRect(screen_coords)
                
                # 追跡マーカー（四隅に小さい正方形）
                marker_size = 6
                corners = [
                    screen_coords.topLeft(),
                    screen_coords.topRight(),
                    screen_coords.bottomLeft(),
                    screen_coords.bottomRight()
                ]
                for corner in corners:
                    marker_rect = QRect(
                        corner.x() - marker_size//2,
                        corner.y() - marker_size//2,
                        marker_size, marker_size
                    )
                    painter.fillRect(marker_rect, color)
                
                # 信頼度の表示
                painter.setPen(QPen(Qt.GlobalColor.white, 1))
                painter.drawText(
                    screen_coords.topLeft() + QPoint(5, -5),
                    f"Track: {confidence:.2f}"
                )
            else:
                # 通常のBB表示
                color = QColor(bbox.color)
                pen = QPen(color, 2)
                painter.setPen(pen)
                painter.drawRect(screen_coords)
            
            if bbox == self.selected_bbox:
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawRect(screen_coords.adjusted(-2, -2, 2, 2))
        
        # 手動修正モードの表示
        if self.manual_correction_mode:
            painter.setPen(QPen(Qt.GlobalColor.red, 3))
            painter.drawText(10, 30, "手動修正モード - クリックして位置を指定")
                
        painter.end()
        self.image_label.setPixmap(QPixmap.fromImage(display_image))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            
            # 手動修正モードの処理
            if self.manual_correction_mode and self.correction_target_id is not None:
                # 修正位置を設定
                yolo_pos = self.coord_converter.screen_to_yolo_point(
                    (pos.x(), pos.y()),
                    self.size(),
                    self.zoom_level,
                    self.pan_offset
                )
                
                # BBの位置を更新
                for bbox in self.bbox_manager.get_bboxes():
                    if bbox.individual_id == self.correction_target_id:
                        # 既存のサイズを維持しつつ位置を更新
                        w, h = bbox.yolo_coords[2], bbox.yolo_coords[3]
                        bbox.yolo_coords = np.array([yolo_pos[0], yolo_pos[1], w, h])
                        break
                
                # 修正モードを終了
                self.manual_correction_mode = False
                self.correction_target_id = None
                self.update_display()
                return
            
            # Check for bbox selection
            clicked_bbox = None
            for bbox in self.bbox_manager.get_bboxes():
                screen_coords = self.coord_converter.yolo_to_screen(
                    bbox.coords,
                    self.size(),
                    self.zoom_level, 
                    self.pan_offset
                )
                if screen_coords.contains(pos):
                    clicked_bbox = bbox
                    break
                    
            if clicked_bbox:
                self.selected_bbox = clicked_bbox
                self.drag_start = pos
                self.drag_mode = 'move'
            else:
                self.drag_start = pos
                self.drag_mode = 'create'
                
            self.update_display()

    def mouseMoveEvent(self, event):
        if self.drag_mode == 'move' and self.selected_bbox:
            delta = event.pos() - self.drag_start
            yolo_delta = self.coord_converter.screen_to_yolo_delta(
                delta,
                self.size(),
                self.zoom_level
            )
            self.bbox_manager.move_bbox(self.selected_bbox, yolo_delta)
            self.drag_start = event.pos()
            self.update_display()
            
        elif self.drag_mode == 'create':
            rect = QRect(self.drag_start, event.pos()).normalized()
            yolo_coords = self.coord_converter.screen_to_yolo(
                rect,
                self.size(),
                self.zoom_level,
                self.pan_offset
            )
            self.bbox_manager.update_temp_bbox(yolo_coords)
            self.update_display()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drag_mode == 'create':
                rect = QRect(self.drag_start, event.pos()).normalized()
                if rect.width() > 10 and rect.height() > 10:
                    yolo_coords = self.coord_converter.screen_to_yolo(
                        rect,
                        self.size(),
                        self.zoom_level,
                        self.pan_offset
                    )
                    self.bbox_manager.create_bbox(yolo_coords)
                    
            self.drag_mode = None
            self.drag_start = None
            self.update_display()

    def wheelEvent(self, event):
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.zoom_level *= zoom_factor
        self.zoom_level = max(0.1, min(5.0, self.zoom_level))
        self.update_display()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete and self.selected_bbox:
            self.bbox_manager.delete_bbox(self.selected_bbox)
            self.selected_bbox = None
            self.update_display()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()
    
    def get_selected_bbox(self):
        """選択されているBBを返す"""
        return self.selected_bbox
    
    def set_tracking_state(self, individual_id: int, is_tracking: bool):
        """指定個体の追跡状態を設定"""
        self.tracking_states[individual_id] = is_tracking
        if not is_tracking and individual_id in self.tracking_confidence:
            del self.tracking_confidence[individual_id]
        self.update_display()
    
    def update_tracking_confidence(self, individual_id: int, confidence: float):
        """追跡信頼度を更新"""
        self.tracking_confidence[individual_id] = confidence
        self.update_display()
    
    def enable_manual_correction_mode(self, individual_id: int):
        """手動修正モードを有効化"""
        self.manual_correction_mode = True
        self.correction_target_id = individual_id
        self.update_display()
    
    def update_view(self):
        """ビューを更新（リサイズ時など）"""
        self.update_display()