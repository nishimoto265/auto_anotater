"""
色マッピング値オブジェクト - Agent3専用
16個体ID色分け管理
"""

from dataclasses import dataclass
from typing import Tuple, Dict
from ..exceptions import ValidationError


# 16個体用固定色パレット (RGB) - クラス外定義
INDIVIDUAL_COLORS: Dict[int, Tuple[int, int, int]] = {
    0:  (255, 0, 0),     # 赤
    1:  (0, 255, 0),     # 緑
    2:  (0, 0, 255),     # 青
    3:  (255, 255, 0),   # 黄
    4:  (255, 0, 255),   # マゼンタ
    5:  (0, 255, 255),   # シアン
    6:  (255, 128, 0),   # オレンジ
    7:  (128, 0, 255),   # 紫
    8:  (255, 128, 128), # ライトレッド
    9:  (128, 255, 128), # ライトグリーン
    10: (128, 128, 255), # ライトブルー
    11: (255, 255, 128), # ライトイエロー
    12: (255, 128, 255), # ライトマゼンタ
    13: (128, 255, 255), # ライトシアン
    14: (128, 64, 0),    # ブラウン
    15: (64, 64, 64),    # グレー
}


@dataclass(frozen=True)
class ColorMapping:
    """
    個体ID色マッピング値オブジェクト
    
    16個体(ID: 0-15)に対応する色分け管理
    RGB値による色指定
    """
    
    individual_id: int
    
    def __post_init__(self):
        """個体ID検証"""
        if not 0 <= self.individual_id <= 15:
            raise ValidationError("individual_id", self.individual_id, "0-15")
    
    def get_rgb(self) -> Tuple[int, int, int]:
        """RGB色取得"""
        return INDIVIDUAL_COLORS[self.individual_id]
    
    def get_rgba(self, alpha: int = 255) -> Tuple[int, int, int, int]:
        """RGBA色取得"""
        r, g, b = self.get_rgb()
        return (r, g, b, alpha)
    
    def get_hex(self) -> str:
        """16進数色コード取得"""
        r, g, b = self.get_rgb()
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def get_css_color(self) -> str:
        """CSS色文字列取得"""
        r, g, b = self.get_rgb()
        return f"rgb({r}, {g}, {b})"
    
    @classmethod
    def get_all_colors(cls) -> Dict[int, Tuple[int, int, int]]:
        """全個体色マッピング取得"""
        return INDIVIDUAL_COLORS.copy()
    
    @classmethod
    def is_valid_individual_id(cls, individual_id: int) -> bool:
        """個体ID有効性確認"""
        return 0 <= individual_id <= 15