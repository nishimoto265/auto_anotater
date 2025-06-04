"""
Agent1 Presentation - LayoutManager
レイアウト管理（70%:30%分割最適化）

性能要件:
- レイアウト更新: 10ms以下
- サイズ計算: 1ms以下
- 描画領域最適化: リアルタイム
"""

import time
from typing import Tuple, Dict, Any
from PyQt6.QtCore import QSize, QRect
from PyQt6.QtWidgets import QWidget


class LayoutManager:
    """
    レイアウト管理（70%:30%分割最適化）
    
    性能要件:
    - レイアウト更新: 10ms以下
    - サイズ計算: 1ms以下
    - 描画領域最適化: リアルタイム
    """
    
    # レイアウト定数
    CANVAS_RATIO = 0.7  # キャンバス領域比率
    PANEL_RATIO = 0.3   # パネル領域比率
    MARGIN = 5          # マージン
    SPLITTER_WIDTH = 3  # スプリッター幅
    
    # 最小サイズ制限
    MIN_CANVAS_WIDTH = 800
    MIN_PANEL_WIDTH = 300
    MIN_HEIGHT = 600
    
    def __init__(self):
        """初期化"""
        self.last_window_size = QSize()
        self.cached_layout = {}
        
    def update_layout(self, window_size: QSize) -> Dict[str, QRect]:
        """
        レイアウト更新（10ms以下必達）
        
        Args:
            window_size: ウィンドウサイズ
            
        Returns:
            Dict[str, QRect]: レイアウト情報
        """
        start_time = time.perf_counter()
        
        # キャッシュチェック
        if window_size == self.last_window_size and self.cached_layout:
            return self.cached_layout
            
        # レイアウト計算
        layout = self._calculate_layout(window_size)
        
        # キャッシュ更新
        self.last_window_size = window_size
        self.cached_layout = layout
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 10:
            print(f"WARNING: Layout update took {elapsed:.2f}ms (>10ms)")
            
        return layout
        
    def _calculate_layout(self, window_size: QSize) -> Dict[str, QRect]:
        """レイアウト計算（内部処理）"""
        width = window_size.width()
        height = window_size.height()
        
        # 有効領域計算（マージン除外）
        effective_width = width - (self.MARGIN * 2)
        effective_height = height - (self.MARGIN * 2)
        
        # キャンバス・パネル幅計算
        canvas_width = int(effective_width * self.CANVAS_RATIO - self.SPLITTER_WIDTH / 2)
        panel_width = int(effective_width * self.PANEL_RATIO - self.SPLITTER_WIDTH / 2)
        
        # 最小サイズ制限適用
        canvas_width = max(canvas_width, self.MIN_CANVAS_WIDTH)
        panel_width = max(panel_width, self.MIN_PANEL_WIDTH)
        effective_height = max(effective_height, self.MIN_HEIGHT)
        
        # レイアウト情報作成
        layout = {
            'window': QRect(0, 0, width, height),
            'canvas': QRect(
                self.MARGIN,
                self.MARGIN,
                canvas_width,
                effective_height
            ),
            'panel': QRect(
                self.MARGIN + canvas_width + self.SPLITTER_WIDTH,
                self.MARGIN,
                panel_width,
                effective_height
            ),
            'canvas_size': QSize(canvas_width, effective_height),
            'panel_size': QSize(panel_width, effective_height),
        }
        
        return layout
        
    def calculate_canvas_size(self, window_size: QSize) -> QSize:
        """
        キャンバスサイズ計算（1ms以下必達）
        
        Args:
            window_size: ウィンドウサイズ
            
        Returns:
            QSize: キャンバスサイズ
        """
        start_time = time.perf_counter()
        
        # 高速計算（浮動小数点演算最小化）
        effective_width = window_size.width() - (self.MARGIN * 2)
        canvas_width = max(
            int(effective_width * self.CANVAS_RATIO - self.SPLITTER_WIDTH / 2),
            self.MIN_CANVAS_WIDTH
        )
        canvas_height = max(
            window_size.height() - (self.MARGIN * 2),
            self.MIN_HEIGHT
        )
        
        result = QSize(canvas_width, canvas_height)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: Canvas size calculation took {elapsed:.2f}ms (>1ms)")
            
        return result
        
    def calculate_panel_size(self, window_size: QSize) -> QSize:
        """
        パネルサイズ計算（1ms以下必達）
        
        Args:
            window_size: ウィンドウサイズ
            
        Returns:
            QSize: パネルサイズ
        """
        start_time = time.perf_counter()
        
        # 高速計算
        effective_width = window_size.width() - (self.MARGIN * 2)
        panel_width = max(
            int(effective_width * self.PANEL_RATIO - self.SPLITTER_WIDTH / 2),
            self.MIN_PANEL_WIDTH
        )
        panel_height = max(
            window_size.height() - (self.MARGIN * 2),
            self.MIN_HEIGHT
        )
        
        result = QSize(panel_width, panel_height)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: Panel size calculation took {elapsed:.2f}ms (>1ms)")
            
        return result
        
    def get_optimal_splitter_sizes(self, total_width: int) -> Tuple[int, int]:
        """
        最適スプリッターサイズ取得
        
        Args:
            total_width: 総幅
            
        Returns:
            Tuple[int, int]: (キャンバス幅, パネル幅)
        """
        effective_width = total_width - self.SPLITTER_WIDTH
        canvas_width = int(effective_width * self.CANVAS_RATIO)
        panel_width = effective_width - canvas_width
        
        # 最小サイズ制限
        if canvas_width < self.MIN_CANVAS_WIDTH:
            canvas_width = self.MIN_CANVAS_WIDTH
            panel_width = max(effective_width - canvas_width, self.MIN_PANEL_WIDTH)
        elif panel_width < self.MIN_PANEL_WIDTH:
            panel_width = self.MIN_PANEL_WIDTH
            canvas_width = effective_width - panel_width
            
        return canvas_width, panel_width
        
    def validate_layout(self, layout: Dict[str, QRect]) -> bool:
        """
        レイアウト妥当性確認
        
        Args:
            layout: レイアウト情報
            
        Returns:
            bool: 妥当性
        """
        try:
            # 必須キーチェック
            required_keys = ['window', 'canvas', 'panel']
            if not all(key in layout for key in required_keys):
                return False
                
            # サイズチェック
            canvas_rect = layout['canvas']
            panel_rect = layout['panel']
            
            if (canvas_rect.width() < self.MIN_CANVAS_WIDTH or
                panel_rect.width() < self.MIN_PANEL_WIDTH or
                canvas_rect.height() < self.MIN_HEIGHT or
                panel_rect.height() < self.MIN_HEIGHT):
                return False
                
            return True
            
        except Exception as e:
            print(f"Layout validation error: {e}")
            return False
            
    def get_layout_info(self) -> Dict[str, Any]:
        """レイアウト情報取得"""
        return {
            'canvas_ratio': self.CANVAS_RATIO,
            'panel_ratio': self.PANEL_RATIO,
            'margin': self.MARGIN,
            'splitter_width': self.SPLITTER_WIDTH,
            'min_canvas_width': self.MIN_CANVAS_WIDTH,
            'min_panel_width': self.MIN_PANEL_WIDTH,
            'min_height': self.MIN_HEIGHT,
            'last_window_size': (
                self.last_window_size.width(),
                self.last_window_size.height()
            ),
            'cache_status': bool(self.cached_layout),
        }
        
    def clear_cache(self):
        """キャッシュクリア"""
        self.cached_layout.clear()
        self.last_window_size = QSize()


if __name__ == "__main__":
    # テスト実行
    layout_manager = LayoutManager()
    
    # テストサイズ
    test_sizes = [
        QSize(1920, 1080),
        QSize(1280, 720),
        QSize(1024, 768),
        QSize(800, 600),
    ]
    
    for size in test_sizes:
        print(f"\nTesting size: {size.width()}x{size.height()}")
        
        # レイアウト計算テスト
        start_time = time.perf_counter()
        layout = layout_manager.update_layout(size)
        elapsed = (time.perf_counter() - start_time) * 1000
        
        print(f"Layout calculation time: {elapsed:.3f}ms")
        print(f"Canvas size: {layout['canvas'].width()}x{layout['canvas'].height()}")
        print(f"Panel size: {layout['panel'].width()}x{layout['panel'].height()}")
        print(f"Valid: {layout_manager.validate_layout(layout)}")
        
        # キャッシュテスト
        start_time = time.perf_counter()
        cached_layout = layout_manager.update_layout(size)
        cached_elapsed = (time.perf_counter() - start_time) * 1000
        
        print(f"Cached layout time: {cached_elapsed:.3f}ms")
        print(f"Cache hit: {layout == cached_layout}")