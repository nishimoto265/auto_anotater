"""
BB描画性能テスト
16ms以下BB描画・60fps描画能力確認
"""
import time
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRectF
from unittest.mock import Mock, patch

from src.presentation.bb_canvas.bb_renderer import BBRenderer
from src.presentation.bb_canvas.canvas_widget import BBCanvas


class TestBBRenderingPerformance:
    """BB描画性能テスト"""
    
    @pytest.fixture
    def app(self):
        """PyQt6アプリケーション"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def bb_renderer(self, app):
        """BBRenderer instance"""
        return BBRenderer()
    
    @pytest.fixture
    def bb_canvas(self, app):
        """BBCanvas instance"""
        return BBCanvas()
    
    @pytest.fixture
    def mock_bb_entities(self):
        """モックBBエンティティリスト"""
        bb_entities = []
        for i in range(50):  # 50個のBBテスト
            bb = Mock()
            bb.id = i
            bb.x = 100 + i * 10
            bb.y = 100 + i * 10
            bb.width = 50
            bb.height = 50
            bb.individual_id = i % 16
            bb.action_id = i % 5
            bb.confidence = 0.9
            bb_entities.append(bb)
        return bb_entities
    
    def test_bb_rendering_16ms(self, bb_renderer, mock_bb_entities):
        """BB描画16ms以下確認"""
        start_time = time.perf_counter()
        
        # BB描画実行
        render_time = bb_renderer.render_bbs(mock_bb_entities, update_mode="full")
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # ms変換
        
        # 16ms以下確認
        assert total_time <= 16.0, f"BB描画時間{total_time:.2f}msが16ms超過"
        assert render_time <= 16.0, f"BBRenderer報告時間{render_time:.2f}msが16ms超過"
    
    def test_single_bb_rendering_1ms(self, bb_renderer, mock_bb_entities):
        """単一BB描画1ms以下確認"""
        single_bb = mock_bb_entities[0]
        
        start_time = time.perf_counter()
        bb_renderer.render_single_bb(single_bb)
        end_time = time.perf_counter()
        
        render_time = (end_time - start_time) * 1000
        assert render_time <= 1.0, f"単一BB描画時間{render_time:.2f}msが1ms超過"
    
    def test_multiple_bb_rendering(self, bb_renderer, mock_bb_entities):
        """複数BB同時描画性能確認"""
        test_cases = [10, 25, 50, 100]
        
        for bb_count in test_cases:
            bbs = mock_bb_entities[:bb_count]
            
            start_time = time.perf_counter()
            render_time = bb_renderer.render_bbs(bbs, update_mode="full")
            end_time = time.perf_counter()
            
            total_time = (end_time - start_time) * 1000
            
            # BB数に関係なく16ms以下維持
            assert total_time <= 16.0, f"{bb_count}BB描画時間{total_time:.2f}msが16ms超過"
    
    def test_differential_rendering_performance(self, bb_renderer, mock_bb_entities):
        """差分描画性能確認"""
        # 初回全描画
        full_start = time.perf_counter()
        bb_renderer.render_bbs(mock_bb_entities, update_mode="full")
        full_end = time.perf_counter()
        full_time = (full_end - full_start) * 1000
        
        # 差分描画（変更なし）
        diff_start = time.perf_counter()
        bb_renderer.render_bbs(mock_bb_entities, update_mode="differential")
        diff_end = time.perf_counter()
        diff_time = (diff_end - diff_start) * 1000
        
        # 差分描画は全描画より高速
        assert diff_time < full_time, f"差分描画({diff_time:.2f}ms)が全描画({full_time:.2f}ms)より遅い"
        assert diff_time <= 8.0, f"差分描画時間{diff_time:.2f}msが8ms超過"
    
    def test_60fps_rendering_capability(self, bb_renderer, mock_bb_entities):
        """60fps描画能力確認"""
        frame_budget = 16.67  # 60fps = 16.67ms/frame
        frame_count = 60
        
        total_start = time.perf_counter()
        
        for _ in range(frame_count):
            frame_start = time.perf_counter()
            bb_renderer.render_bbs(mock_bb_entities, update_mode="differential")
            frame_end = time.perf_counter()
            
            frame_time = (frame_end - frame_start) * 1000
            assert frame_time <= frame_budget, f"フレーム描画{frame_time:.2f}msが60fps予算{frame_budget}ms超過"
        
        total_end = time.perf_counter()
        total_time = (total_end - total_start) * 1000
        average_frame_time = total_time / frame_count
        
        assert average_frame_time <= frame_budget, f"平均フレーム時間{average_frame_time:.2f}msが60fps予算超過"
    
    def test_canvas_update_performance(self, bb_canvas, mock_bb_entities):
        """キャンバス更新性能確認"""
        start_time = time.perf_counter()
        bb_canvas.update_bounding_boxes(mock_bb_entities)
        end_time = time.perf_counter()
        
        update_time = (end_time - start_time) * 1000
        assert update_time <= 16.0, f"キャンバス更新時間{update_time:.2f}msが16ms超過"
    
    def test_clear_canvas_performance(self, bb_renderer):
        """キャンバスクリア性能確認"""
        start_time = time.perf_counter()
        bb_renderer.clear_canvas()
        end_time = time.perf_counter()
        
        clear_time = (end_time - start_time) * 1000
        assert clear_time <= 5.0, f"キャンバスクリア時間{clear_time:.2f}msが5ms超過"
    
    def test_color_mapping_performance(self, bb_renderer):
        """色マッピング性能確認"""
        # 16個体分の色マッピングテスト
        start_time = time.perf_counter()
        
        for individual_id in range(16):
            for action_id in range(5):
                color = bb_renderer.get_bb_color(individual_id, action_id)
                assert color is not None
        
        end_time = time.perf_counter()
        mapping_time = (end_time - start_time) * 1000
        
        # 3ms以下確認
        assert mapping_time <= 3.0, f"色マッピング時間{mapping_time:.2f}msが3ms超過"
    
    def test_memory_efficient_rendering(self, bb_renderer, mock_bb_entities):
        """メモリ効率的描画確認"""
        import tracemalloc
        
        tracemalloc.start()
        
        # 100回連続描画
        for _ in range(100):
            bb_renderer.render_bbs(mock_bb_entities, update_mode="differential")
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # メモリ使用量が妥当な範囲内
        assert peak < 100 * 1024 * 1024, f"ピークメモリ使用量{peak/1024/1024:.2f}MBが100MB超過"