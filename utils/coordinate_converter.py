import numpy as np
from typing import Tuple, Union, Optional

class CoordinateConverter:
    def __init__(self, image_width: int, image_height: int):
        self.image_width = image_width
        self.image_height = image_height
        self._coordinate_cache = {}

    def screen_to_yolo(self, x: float, y: float, w: float, h: float) -> Tuple[float, float, float, float]:
        cache_key = ('s2y', x, y, w, h)
        if cache_key in self._coordinate_cache:
            return self._coordinate_cache[cache_key]

        x_center = (x + w/2) / self.image_width
        y_center = (y + h/2) / self.image_height
        width = w / self.image_width
        height = h / self.image_height

        result = self._validate_yolo_coordinates(x_center, y_center, width, height)
        self._coordinate_cache[cache_key] = result
        return result

    def yolo_to_screen(self, x: float, y: float, w: float, h: float) -> Tuple[float, float, float, float]:
        cache_key = ('y2s', x, y, w, h)
        if cache_key in self._coordinate_cache:
            return self._coordinate_cache[cache_key]

        screen_x = (x - w/2) * self.image_width
        screen_y = (y - h/2) * self.image_height
        screen_w = w * self.image_width
        screen_h = h * self.image_height

        result = self._validate_screen_coordinates(screen_x, screen_y, screen_w, screen_h)
        self._coordinate_cache[cache_key] = result
        return result

    def apply_zoom(self, coords: Tuple[float, float, float, float], zoom_factor: float) -> Tuple[float, float, float, float]:
        x, y, w, h = coords
        return (x * zoom_factor, y * zoom_factor, w * zoom_factor, h * zoom_factor)

    def apply_rotation(self, coords: Tuple[float, float, float, float], angle: float) -> Tuple[float, float, float, float]:
        x, y, w, h = coords
        rad = np.radians(angle)
        cos_a = np.cos(rad)
        sin_a = np.sin(rad)
        
        x_rot = x * cos_a - y * sin_a
        y_rot = x * sin_a + y * cos_a
        
        return (x_rot, y_rot, w, h)

    def _validate_yolo_coordinates(self, x: float, y: float, w: float, h: float) -> Tuple[float, float, float, float]:
        x = np.clip(x, 0.0, 1.0)
        y = np.clip(y, 0.0, 1.0)
        w = np.clip(w, 0.0, 1.0)
        h = np.clip(h, 0.0, 1.0)
        return (x, y, w, h)

    def _validate_screen_coordinates(self, x: float, y: float, w: float, h: float) -> Tuple[float, float, float, float]:
        x = np.clip(x, 0, self.image_width)
        y = np.clip(y, 0, self.image_height)
        w = np.clip(w, 0, self.image_width - x)
        h = np.clip(h, 0, self.image_height - y)
        return (x, y, w, h)

    def clear_cache(self):
        self._coordinate_cache.clear()

    def batch_convert_screen_to_yolo(self, coords_list: list) -> list:
        return [self.screen_to_yolo(*coords) for coords in coords_list]

    def batch_convert_yolo_to_screen(self, coords_list: list) -> list:
        return [self.yolo_to_screen(*coords) for coords in coords_list]

    def is_valid_bbox(self, x: float, y: float, w: float, h: float) -> bool:
        return (w > 0 and h > 0 and 
                0 <= x <= self.image_width and 
                0 <= y <= self.image_height and
                x + w <= self.image_width and 
                y + h <= self.image_height)