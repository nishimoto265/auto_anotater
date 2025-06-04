# 値オブジェクト - Agent3専用
# 座標・信頼度・色マッピング等の不変値オブジェクト

from .coordinates import Coordinates, PixelCoordinates
from .confidence import Confidence
from .color_mapping import ColorMapping

__all__ = [
    'Coordinates',
    'PixelCoordinates', 
    'Confidence',
    'ColorMapping'
]