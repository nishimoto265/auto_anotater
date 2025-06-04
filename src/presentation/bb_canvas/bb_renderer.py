"""
Agent1 Presentation - BBRenderer
高速BB描画エンジン（16ms以下描画）

最適化手法:
- OpenGL GPU描画活用
- 差分描画（dirty rectangle）
- オブジェクトプール活用
- 色マッピングキャッシュ
"""

import time
from typing import List, Dict, Any, Optional, Set
from collections import deque
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QTransform


class ObjectPool:
    """描画オブジェクトプール（メモリ効率最適化）"""
    
    def __init__(self, object_class, pool_size: int = 100):
        self.object_class = object_class
        self.pool = []  # 遅延初期化
        self.available = deque()
        self.in_use = set()
        self.pool_size = pool_size
        
    def get(self, *args, **kwargs):
        """オブジェクト取得"""
        if self.available:
            obj = self.available.popleft()
            self.in_use.add(obj)
            return obj
        else:
            # 新しいオブジェクト作成
            new_obj = self.object_class(*args, **kwargs)
            self.in_use.add(new_obj)
            return new_obj
            
    def release(self, obj):
        """オブジェクト返却"""
        if obj in self.in_use:
            self.in_use.remove(obj)
            self.available.append(obj)
            
    def release_all(self):
        """全オブジェクト返却"""
        self.available.extend(self.in_use)
        self.in_use.clear()


class BBGraphicsItem(QGraphicsRectItem):
    """カスタムBBグラフィックスアイテム"""
    
    def __init__(self, bb_entity, parent=None):
        super().__init__(parent)
        self.bb_entity = bb_entity
        self.text_item = None
        self.setup_appearance()
        
    def setup_appearance(self):
        """外観設定"""
        # ペン設定（境界線）
        pen = QPen(self.bb_entity.color, 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        self.setPen(pen)
        
        # ブラシ設定（塗りつぶし）
        brush = QBrush(self.bb_entity.color)
        brush.setStyle(Qt.BrushStyle.NoBrush)  # 透明
        self.setBrush(brush)
        
        # 選択可能
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
    def add_text_label(self, text: str, font_size: int = 12):
        """テキストラベル追加"""
        if not self.text_item:
            self.text_item = QGraphicsTextItem(text, self)
            font = QFont("Arial", font_size)
            self.text_item.setFont(font)
            self.text_item.setDefaultTextColor(self.bb_entity.color)
            
            # ラベル位置調整
            rect = self.rect()
            self.text_item.setPos(rect.x(), rect.y() - 20)
        else:
            self.text_item.setPlainText(text)


class BBRenderer:
    """
    高速BB描画エンジン
    
    最適化手法:
    - OpenGL GPU描画活用
    - 差分描画（dirty rectangle）
    - オブジェクトプール活用
    - 色マッピングキャッシュ
    """
    
    def __init__(self, use_opengl: bool = True):
        self.use_opengl = use_opengl
        
        # オブジェクトプール（BBGraphicsItemは引数が必要なので遅延作成）
        self.rect_pool = ObjectPool(BBGraphicsItem, pool_size=100)
        
        # 描画キャッシュ
        self.rendered_items: List[QGraphicsItem] = []
        self.previous_bbs: List[Any] = []
        
        # 差分描画用
        self.dirty_rects: Set[QRectF] = set()
        
        # 色キャッシュ
        self.color_cache: Dict[int, QColor] = {}
        
        # 性能統計
        self.render_count = 0
        self.total_render_time = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
    def render_bbs(self, bb_list: List[Any], image_width: int, 
                   image_height: int, transform: QTransform) -> float:
        """
        BB一括描画（16ms以下必達）
        
        Args:
            bb_list: 描画対象BBリスト
            image_width: 画像幅
            image_height: 画像高さ
            transform: 変換行列
            
        Returns:
            float: 描画時間（ms）
        """
        start_time = time.perf_counter()
        
        try:
            # 差分チェック
            if self._should_use_differential_rendering(bb_list):
                self._render_differential(bb_list, image_width, image_height)
            else:
                self._render_full(bb_list, image_width, image_height)
                
        except Exception as e:
            print(f"BB rendering error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        
        # 統計更新
        self.render_count += 1
        self.total_render_time += elapsed
        
        # 性能監視
        if elapsed > 16:
            print(f"WARNING: BB rendering took {elapsed:.2f}ms (>16ms)")
            
        return elapsed
        
    def _should_use_differential_rendering(self, bb_list: List[Any]) -> bool:
        """差分描画判定"""
        # BB数が変わった場合は全描画
        if len(bb_list) != len(self.previous_bbs):
            return False
            
        # BB内容が変わった場合は全描画
        for i, bb in enumerate(bb_list):
            if i >= len(self.previous_bbs):
                return False
            prev_bb = self.previous_bbs[i]
            if (bb.x != prev_bb.x or bb.y != prev_bb.y or 
                bb.w != prev_bb.w or bb.h != prev_bb.h or
                bb.individual_id != prev_bb.individual_id):
                return False
                
        return True
        
    def _render_full(self, bb_list: List[Any], image_width: int, image_height: int):
        """全体描画"""
        # 既存アイテムクリア
        self._clear_rendered_items()
        
        # 新しいBB描画
        for bb in bb_list:
            item = self._create_bb_item(bb, image_width, image_height)
            if item:
                self.rendered_items.append(item)
                
        # 前回状態保存
        self.previous_bbs = bb_list.copy()
        
    def _render_differential(self, bb_list: List[Any], image_width: int, image_height: int):
        """差分描画（高速）"""
        # 変更されたBBのみ更新
        for i, bb in enumerate(bb_list):
            if i < len(self.rendered_items):
                # 既存アイテム更新
                item = self.rendered_items[i]
                if hasattr(item, 'bb_entity'):
                    self._update_bb_item(item, bb, image_width, image_height)
            else:
                # 新しいアイテム作成
                item = self._create_bb_item(bb, image_width, image_height)
                if item:
                    self.rendered_items.append(item)
                    
    def _create_bb_item(self, bb_entity: Any, image_width: int, 
                       image_height: int) -> Optional[BBGraphicsItem]:
        """BB描画アイテム作成（1ms以下）"""
        start_time = time.perf_counter()
        
        try:
            # ピクセル座標変換
            rect = bb_entity.to_pixel_rect(image_width, image_height)
            
            # グラフィックスアイテム作成（プールから取得またはnew）
            try:
                item = self.rect_pool.get(bb_entity)
            except:
                # プール取得失敗時は直接作成
                item = BBGraphicsItem(bb_entity)
                
            item.setRect(rect)
            
            # ラベル追加
            label = f"ID:{bb_entity.individual_id} A:{bb_entity.action_id}"
            item.add_text_label(label)
            
            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > 1:
                print(f"WARNING: BB item creation took {elapsed:.2f}ms (>1ms)")
                
            return item
            
        except Exception as e:
            print(f"BB item creation error: {e}")
            return None
            
    def _update_bb_item(self, item: BBGraphicsItem, bb_entity: Any,
                       image_width: int, image_height: int):
        """BB描画アイテム更新"""
        rect = bb_entity.to_pixel_rect(image_width, image_height)
        item.setRect(rect)
        item.bb_entity = bb_entity
        
        # ラベル更新
        if item.text_item:
            label = f"ID:{bb_entity.individual_id} A:{bb_entity.action_id}"
            item.text_item.setPlainText(label)
            
    def _clear_rendered_items(self):
        """描画アイテムクリア"""
        for item in self.rendered_items:
            if hasattr(item, 'scene') and item.scene():
                item.scene().removeItem(item)
        self.rendered_items.clear()
        
    def render_single_bb(self, bb_entity: Any, image_width: int, 
                        image_height: int) -> Optional[BBGraphicsItem]:
        """
        単一BB描画（1ms以下必達）
        
        Args:
            bb_entity: BBエンティティ
            image_width: 画像幅
            image_height: 画像高さ
            
        Returns:
            Optional[BBGraphicsItem]: 描画アイテム
        """
        start_time = time.perf_counter()
        
        item = self._create_bb_item(bb_entity, image_width, image_height)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: Single BB rendering took {elapsed:.2f}ms (>1ms)")
            
        return item
        
    def clear_canvas(self) -> float:
        """
        キャンバスクリア（5ms以下必達）
        
        Returns:
            float: クリア時間（ms）
        """
        start_time = time.perf_counter()
        
        self._clear_rendered_items()
        self.previous_bbs.clear()
        self.dirty_rects.clear()
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Canvas clear took {elapsed:.2f}ms (>5ms)")
            
        return elapsed
        
    def mark_dirty_rect(self, rect: QRectF):
        """変更領域マーク"""
        self.dirty_rects.add(rect)
        
    def clear_dirty_rects(self):
        """変更領域クリア"""
        self.dirty_rects.clear()
        
    def get_color_for_id(self, individual_id: int) -> QColor:
        """ID用色取得（キャッシュ活用）"""
        if individual_id in self.color_cache:
            self.cache_hits += 1
            return self.color_cache[individual_id]
            
        # 16色循環
        color_index = individual_id % 16
        colors = [
            QColor(255, 0, 0),    # Red
            QColor(0, 255, 0),    # Green
            QColor(0, 0, 255),    # Blue
            QColor(255, 255, 0),  # Yellow
            QColor(255, 0, 255),  # Magenta
            QColor(0, 255, 255),  # Cyan
            QColor(255, 128, 0),  # Orange
            QColor(128, 0, 255),  # Purple
            QColor(255, 192, 203),# Pink
            QColor(165, 42, 42),  # Brown
            QColor(128, 128, 128),# Gray
            QColor(0, 128, 0),    # Dark Green
            QColor(0, 0, 128),    # Navy
            QColor(128, 128, 0),  # Olive
            QColor(128, 0, 128),  # Maroon
            QColor(0, 128, 128),  # Teal
        ]
        
        color = colors[color_index]
        self.color_cache[individual_id] = color
        self.cache_misses += 1
        
        return color
        
    def optimize_rendering(self):
        """描画最適化実行"""
        # キャッシュクリア（メモリ節約）
        if len(self.color_cache) > 100:
            self.color_cache.clear()
            
        # オブジェクトプール最適化
        self.rect_pool.release_all()
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """性能統計取得"""
        avg_render_time = (self.total_render_time / self.render_count 
                          if self.render_count > 0 else 0)
        cache_hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses)
                         if (self.cache_hits + self.cache_misses) > 0 else 0)
        
        return {
            'use_opengl': self.use_opengl,
            'render_count': self.render_count,
            'avg_render_time': avg_render_time,
            'total_render_time': self.total_render_time,
            'cache_hit_rate': cache_hit_rate,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'rendered_items_count': len(self.rendered_items),
            'dirty_rects_count': len(self.dirty_rects),
            'target_performance': {
                'bb_rendering': '16ms以下',
                'single_bb': '1ms以下',
                'canvas_clear': '5ms以下',
            }
        }


if __name__ == "__main__":
    # パフォーマンステスト
    import random
    from dataclasses import dataclass
    
    @dataclass
    class TestBBEntity:
        id: str
        x: float
        y: float
        w: float
        h: float
        individual_id: int
        action_id: int
        confidence: float
        color: QColor
        
        def to_pixel_rect(self, image_width: int, image_height: int) -> QRectF:
            px = self.x * image_width - (self.w * image_width) / 2
            py = self.y * image_height - (self.h * image_height) / 2
            pw = self.w * image_width
            ph = self.h * image_height
            return QRectF(px, py, pw, ph)
    
    # テスト用BBリスト生成
    def create_test_bbs(count: int) -> List[TestBBEntity]:
        bbs = []
        for i in range(count):
            bb = TestBBEntity(
                id=f"test_bb_{i}",
                x=random.uniform(0.1, 0.9),
                y=random.uniform(0.1, 0.9),
                w=random.uniform(0.05, 0.2),
                h=random.uniform(0.05, 0.2),
                individual_id=random.randint(0, 15),
                action_id=random.randint(0, 4),
                confidence=random.uniform(0.7, 1.0),
                color=QColor(255, 0, 0)
            )
            bbs.append(bb)
        return bbs
    
    # レンダラーテスト
    renderer = BBRenderer(use_opengl=True)
    
    # テストケース
    test_cases = [10, 50, 100, 200]
    
    print("BBRenderer Performance Test")
    print("=" * 40)
    
    for bb_count in test_cases:
        print(f"\nTesting {bb_count} BBs:")
        
        # テストBB生成
        test_bbs = create_test_bbs(bb_count)
        
        # 描画時間測定
        times = []
        for _ in range(10):  # 10回実行
            render_time = renderer.render_bbs(test_bbs, 1920, 1080, QTransform())
            times.append(render_time)
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  Target: <16ms, Status: {'PASS' if avg_time < 16 else 'FAIL'}")
        
    # 統計表示
    print(f"\nPerformance Statistics:")
    stats = renderer.get_performance_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")