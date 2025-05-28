import numpy as np
from typing import Dict, List, Tuple, Optional
from colorsys import hsv_to_rgb, rgb_to_hsv

class ColorManager:
    def __init__(self):
        self._color_cache: Dict[int, str] = {}
        self._action_colors: Dict[str, str] = {}
        self._state_colors = {
            'selected': '#FF0000',
            'tracking': '#00FF00',
            'new': '#0000FF'
        }
        self._color_scheme = 'individual'  # 'individual', 'action', 'state', 'grayscale'
        self._initialize_colors()

    def _initialize_colors(self) -> None:
        for i in range(16):
            hue = i / 16
            rgb = hsv_to_rgb(hue, 0.8, 1.0)
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            self._color_cache[i] = hex_color

    def get_individual_color(self, id: int) -> str:
        if id not in self._color_cache:
            hue = (id % 16) / 16
            rgb = hsv_to_rgb(hue, 0.8, 1.0)
            self._color_cache[id] = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
        return self._color_cache[id]

    def set_action_color(self, action: str, color: str) -> None:
        self._action_colors[action] = color

    def get_action_color(self, action: str) -> str:
        return self._action_colors.get(action, '#808080')

    def get_state_color(self, state: str) -> str:
        return self._state_colors.get(state, '#808080')

    def set_color_scheme(self, scheme: str) -> None:
        if scheme in ['individual', 'action', 'state', 'grayscale']:
            self._color_scheme = scheme

    def get_color(self, id: int, action: str, state: str) -> str:
        if self._color_scheme == 'grayscale':
            return self._to_grayscale(self.get_individual_color(id))
        elif self._color_scheme == 'action':
            return self.get_action_color(action)
        elif self._color_scheme == 'state':
            return self.get_state_color(state)
        return self.get_individual_color(id)

    def _to_grayscale(self, hex_color: str) -> str:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        gray = int(0.299 * r + 0.587 * g + 0.114 * b)
        return '#{:02x}{:02x}{:02x}'.format(gray, gray, gray)

    def adjust_contrast(self, color: str, background: str = '#FFFFFF') -> str:
        fg_rgb = tuple(int(color[i:i+2], 16) / 255 for i in (1, 3, 5))
        bg_rgb = tuple(int(background[i:i+2], 16) / 255 for i in (1, 3, 5))
        
        contrast = self._calculate_contrast(fg_rgb, bg_rgb)
        if contrast < 4.5:  # WCAG AA基準
            hsv = rgb_to_hsv(*fg_rgb)
            adjusted = hsv_to_rgb(hsv[0], hsv[1], min(1.0, hsv[2] * 1.2))
            return '#{:02x}{:02x}{:02x}'.format(
                int(adjusted[0] * 255),
                int(adjusted[1] * 255),
                int(adjusted[2] * 255)
            )
        return color

    def _calculate_contrast(self, fg: Tuple[float, float, float], 
                          bg: Tuple[float, float, float]) -> float:
        def luminance(rgb):
            rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
            return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        
        l1 = luminance(fg)
        l2 = luminance(bg)
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

    def save_colors(self) -> Dict:
        return {
            'individual_colors': self._color_cache.copy(),
            'action_colors': self._action_colors.copy(),
            'state_colors': self._state_colors.copy(),
            'color_scheme': self._color_scheme
        }

    def load_colors(self, config: Dict) -> None:
        self._color_cache = config.get('individual_colors', {})
        self._action_colors = config.get('action_colors', {})
        self._state_colors = config.get('state_colors', self._state_colors)
        self._color_scheme = config.get('color_scheme', 'individual')
        
    def get_id_color(self, id: int) -> str:
        """IDの色を取得（get_individual_colorのエイリアス）"""
        return self.get_individual_color(id)