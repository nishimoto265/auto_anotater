import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QPixmap

from src.core.image_cache import ImageCache
from src.core.bbox_manager import BBoxManager
from src.utils.coordinate_converter import CoordinateConverter

class FrameViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_cache = ImageCache()
        self.bbox_manager = BBoxManager(800, 600)
        self.coord_converter = CoordinateConverter(800, 600)
        
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.current_frame = None
        self.selected_bbox = None
        self.drag_start = None
        self.drag_mode = None
        
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
            
            color = QColor(bbox.color)
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.drawRect(screen_coords)
            
            if bbox == self.selected_bbox:
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawRect(screen_coords.adjusted(-2, -2, 2, 2))
                
        painter.end()
        self.image_label.setPixmap(QPixmap.fromImage(display_image))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            
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
        
    def update_view(self):
        """ビューを更新"""
        self.update_display()
        
    def delete_selected_bb(self):
        """選択されたバウンディングボックスを削除"""
        if self.selected_bbox:
            self.bbox_manager.delete_box(self.selected_bbox.id)
            self.selected_bbox = None
            self.update_display()
            
    def update(self):
        """表示を更新"""
        self.update_display()