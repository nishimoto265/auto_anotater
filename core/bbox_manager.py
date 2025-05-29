import time
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from src.utils.coordinate_converter import CoordinateConverter
from src.utils.color_manager import ColorManager

@dataclass
class BoundingBox:
    id: int
    individual_id: int
    action_id: int
    yolo_coords: np.ndarray  # [x, y, w, h] in YOLO format
    confidence: float
    timestamp: float
    selected: bool = False
    tracking: bool = False

class BBoxManager:
    def __init__(self):
        self.boxes: List[BoundingBox] = []
        self.coord_converter = CoordinateConverter()
        self.color_manager = ColorManager()
        self.next_box_id = 0
        self.selected_box: Optional[BoundingBox] = None
        
    def create_box(self, screen_coords: Tuple[float, float, float, float], 
                   individual_id: int, action_id: int) -> BoundingBox:
        yolo_coords = self.coord_converter.screen_to_yolo(screen_coords)
        box = BoundingBox(
            id=self.next_box_id,
            individual_id=individual_id,
            action_id=action_id,
            yolo_coords=np.array(yolo_coords),
            confidence=1.0,
            timestamp=float(time.time())
        )
        self.next_box_id += 1
        self.boxes.append(box)
        return box

    def update_box(self, box_id: int, screen_coords: Tuple[float, float, float, float]) -> None:
        box = self._get_box_by_id(box_id)
        if box:
            box.yolo_coords = np.array(self.coord_converter.screen_to_yolo(screen_coords))
            box.timestamp = float(time.time())

    def delete_box(self, box_id: int) -> None:
        self.boxes = [box for box in self.boxes if box.id != box_id]
        if self.selected_box and self.selected_box.id == box_id:
            self.selected_box = None

    def select_box(self, screen_point: Tuple[float, float]) -> Optional[BoundingBox]:
        yolo_point = self.coord_converter.screen_to_yolo_point(screen_point)
        for box in self.boxes:
            if self._point_in_box(yolo_point, box.yolo_coords):
                if self.selected_box:
                    self.selected_box.selected = False
                box.selected = True
                self.selected_box = box
                return box
        return None

    def check_overlap(self, box: BoundingBox) -> List[BoundingBox]:
        overlaps = []
        for other in self.boxes:
            if other.id != box.id and self._calculate_iou(box.yolo_coords, other.yolo_coords) >= 0.8:
                overlaps.append(other)
        return overlaps

    def _calculate_iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        intersection_x = max(0, min(x1 + w1/2, x2 + w2/2) - max(x1 - w1/2, x2 - w2/2))
        intersection_y = max(0, min(y1 + h1/2, y2 + h2/2) - max(y1 - h1/2, y2 - h2/2))
        intersection = intersection_x * intersection_y
        
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0

    def _point_in_box(self, point: Tuple[float, float], box: np.ndarray) -> bool:
        px, py = point
        x, y, w, h = box
        return (x - w/2 <= px <= x + w/2) and (y - h/2 <= py <= y + h/2)

    def _get_box_by_id(self, box_id: int) -> Optional[BoundingBox]:
        for box in self.boxes:
            if box.id == box_id:
                return box
        return None

    def validate_box(self, box: BoundingBox) -> bool:
        x, y, w, h = box.yolo_coords
        return (0 <= x <= 1 and 0 <= y <= 1 and 
                0 < w <= 1 and 0 < h <= 1 and
                0 <= box.confidence <= 1)

    def get_box_color(self, box: BoundingBox) -> str:
        return self.color_manager.get_color(box.individual_id, box.action_id)