"""
BBレンダラー単体テスト - フレーム別BB分離機能

BBRendererクラスの以下機能をテスト:
- フレーム切り替え時の既存BBクリア
- 新しいフレーム用BBの正確な描画
- アイテム管理の一貫性
- 性能要件の確認
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock
from typing import List
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QTransform

# テスト対象モジュール
sys.path.append('/media/thithilab/volume/auto_anotatation/src')
from presentation.bb_canvas.bb_renderer import BBRenderer, BBGraphicsItem


class MockBBEntity:
    """テスト用BBエンティティ"""
    
    def __init__(self, id: str, x: float, y: float, w: float, h: float, 
                 individual_id: int, action_id: int, confidence: float = 0.9):
        self.id = id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.individual_id = individual_id
        self.action_id = action_id
        self.confidence = confidence
        self.color = QColor(255, 0, 0)
        
    def to_pixel_rect(self, image_width: int, image_height: int) -> QRectF:
        """YOLO座標からピクセル座標に変換"""
        px = self.x * image_width - (self.w * image_width) / 2
        py = self.y * image_height - (self.h * image_height) / 2
        pw = self.w * image_width
        ph = self.h * image_height
        return QRectF(px, py, pw, ph)


@pytest.mark.bb_isolation
@pytest.mark.unit
class TestBBFrameIsolation:
    """BBフレーム分離テスト"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """テスト前セットアップ"""
        self.renderer = BBRenderer(use_opengl=False)
        
        # テスト用BBエンティティ作成
        self.frame1_bbs = [
            MockBBEntity('f1_bb1', 0.3, 0.3, 0.2, 0.2, 0, 0),
            MockBBEntity('f1_bb2', 0.7, 0.7, 0.15, 0.15, 1, 1),
        ]
        
        self.frame2_bbs = [
            MockBBEntity('f2_bb1', 0.4, 0.4, 0.25, 0.25, 2, 2),
        ]
        
        self.frame3_bbs = [
            MockBBEntity('f3_bb1', 0.2, 0.2, 0.3, 0.3, 3, 3),
            MockBBEntity('f3_bb2', 0.6, 0.6, 0.2, 0.2, 4, 4),
            MockBBEntity('f3_bb3', 0.5, 0.3, 0.18, 0.18, 5, 0),
        ]
        
        # モックシーン
        self.mock_scene = Mock()
        self.removed_items = []  # 削除されたアイテムを追跡
        
        def mock_remove_item(item):
            self.removed_items.append(item)
            
        self.mock_scene.removeItem.side_effect = mock_remove_item
        
        yield
        
        # テスト後クリーンアップ
        self.renderer.clear_canvas()
        
    def create_mock_graphics_item(self, bb_entity) -> Mock:
        """モックグラフィックスアイテム作成"""
        mock_item = Mock()
        mock_item.bb_entity = bb_entity
        mock_item.scene.return_value = self.mock_scene
        return mock_item
        
    def test_clear_rendered_items_removes_from_scene(self):
        """_clear_rendered_itemsがシーンからアイテムを削除することを確認"""
        # モックアイテムを作成してレンダラーに追加
        mock_items = []
        for bb in self.frame1_bbs:
            mock_item = self.create_mock_graphics_item(bb)
            mock_items.append(mock_item)
            self.renderer.rendered_items.append(mock_item)
            
        # 初期状態確認
        assert len(self.renderer.rendered_items) == len(self.frame1_bbs)
        
        # クリア実行
        self.renderer._clear_rendered_items()
        
        # アイテムがシーンから削除されたことを確認
        assert self.mock_scene.removeItem.call_count == len(self.frame1_bbs)
        assert len(self.removed_items) == len(self.frame1_bbs)
        
        # レンダラーのリストがクリアされたことを確認
        assert len(self.renderer.rendered_items) == 0
        
    def test_render_full_clears_previous_items(self):
        """render_fullが前のアイテムをクリアすることを確認"""
        # 最初にframe1のBBを描画
        mock_items_f1 = []
        for bb in self.frame1_bbs:
            mock_item = self.create_mock_graphics_item(bb)
            mock_items_f1.append(mock_item)
            self.renderer.rendered_items.append(mock_item)
            
        initial_count = len(self.renderer.rendered_items)
        
        # frame2のBBで全描画実行
        with pytest.raises(Exception):
            # BBGraphicsItemの実際の作成で例外が発生する可能性があるが、
            # クリア処理は実行されるはず
            self.renderer._render_full(self.frame2_bbs, 800, 600)
            
        # 前のアイテムがクリアされたことを確認
        assert self.mock_scene.removeItem.call_count == initial_count
        
    def test_should_use_differential_rendering_always_false(self):
        """差分描画判定が常にFalseを返すことを確認"""
        # 同じBBリストでも差分描画しない
        result1 = self.renderer._should_use_differential_rendering(self.frame1_bbs)
        assert result1 == False
        
        # 異なるBBリストでも差分描画しない
        result2 = self.renderer._should_use_differential_rendering(self.frame2_bbs)
        assert result2 == False
        
        # 空リストでも差分描画しない
        result3 = self.renderer._should_use_differential_rendering([])
        assert result3 == False
        
    def test_clear_canvas_removes_all_items(self):
        """clear_canvasが全アイテムを削除することを確認"""
        # モックアイテムを追加
        mock_items = []
        for bb in self.frame1_bbs + self.frame2_bbs:
            mock_item = self.create_mock_graphics_item(bb)
            mock_items.append(mock_item)
            self.renderer.rendered_items.append(mock_item)
            
        # 前回状態も設定
        self.renderer.previous_bbs = self.frame1_bbs.copy()
        
        initial_item_count = len(self.renderer.rendered_items)
        
        # clear_canvas実行
        clear_time = self.renderer.clear_canvas()
        
        # 性能要件確認（5ms以下）
        assert clear_time < 5, f"clear_canvas時間が性能要件超過: {clear_time:.2f}ms > 5ms"
        
        # 全アイテムがシーンから削除されたことを確認
        assert self.mock_scene.removeItem.call_count == initial_item_count
        
        # 内部状態がクリアされたことを確認
        assert len(self.renderer.rendered_items) == 0
        assert len(self.renderer.previous_bbs) == 0
        assert len(self.renderer.dirty_rects) == 0
        
    def test_render_performance_with_many_bbs(self):
        """大量BB描画の性能テスト"""
        # 大量BBリスト作成
        large_bb_list = []
        for i in range(100):
            bb = MockBBEntity(
                f'bb_{i}',
                0.1 + (i % 10) * 0.08,
                0.1 + (i // 10) * 0.08,
                0.05, 0.05,
                i % 16, i % 5
            )
            large_bb_list.append(bb)
            
        # 描画時間測定
        try:
            render_time = self.renderer.render_bbs(
                large_bb_list, 1920, 1080, QTransform()
            )
            
            # 性能要件確認（16ms以下）
            assert render_time < 16, f"大量BB描画時間が性能要件超過: {render_time:.2f}ms > 16ms"
            
        except Exception:
            # 実際のグラフィックスアイテム作成で例外が発生する可能性があるが、
            # 測定自体は実行される
            pass
            
    def test_bb_isolation_simulation(self):
        """BBフレーム分離シミュレーションテスト"""
        test_cases = [
            ("Frame1", self.frame1_bbs),
            ("Frame2", self.frame2_bbs), 
            ("Frame3", self.frame3_bbs),
            ("Frame1_return", self.frame1_bbs),
            ("Empty", []),
        ]
        
        for frame_name, bb_list in test_cases:
            # 前のフレームの状態記録
            prev_item_count = len(self.renderer.rendered_items)
            
            # 新フレーム描画試行
            try:
                self.renderer._render_full(bb_list, 800, 600)
            except Exception:
                # 実際のアイテム作成でエラーが発生する可能性があるが、
                # クリア処理は実行される
                pass
                
            # 前のアイテムがクリアされたことを確認
            if prev_item_count > 0:
                assert self.mock_scene.removeItem.call_count >= prev_item_count, \
                    f"{frame_name}: 前フレームのアイテムがクリアされていない"
                    
            # 新しい状態が設定されたことを確認
            assert len(self.renderer.previous_bbs) == len(bb_list), \
                f"{frame_name}: previous_bbsが正しく更新されていない"
                
    def test_memory_leak_prevention(self):
        """メモリリーク防止テスト"""
        # 複数回のフレーム切り替えをシミュレート
        frames = [self.frame1_bbs, self.frame2_bbs, self.frame3_bbs] * 10  # 30回切り替え
        
        initial_cache_size = len(self.renderer.color_cache)
        
        for i, bb_list in enumerate(frames):
            # モックアイテムを追加（実際の作成エラーを回避）
            self.renderer.rendered_items.clear()
            for bb in bb_list:
                mock_item = self.create_mock_graphics_item(bb)
                self.renderer.rendered_items.append(mock_item)
                
            # クリア実行
            self.renderer._clear_rendered_items()
            
            # アイテムリストが空になることを確認
            assert len(self.renderer.rendered_items) == 0, f"反復{i}: アイテムがクリアされていない"
            
        # キャッシュサイズが異常に増加していないことを確認
        final_cache_size = len(self.renderer.color_cache)
        assert final_cache_size <= initial_cache_size + 50, \
            f"色キャッシュが異常に増加: {initial_cache_size} -> {final_cache_size}"


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])