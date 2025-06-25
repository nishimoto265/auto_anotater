"""
フレーム別BB描画テスト - 各フレームに適切なBBのみが表示されることを確認

テスト目的:
- フレーム切り替え時に前のフレームのBBが残らない
- 各フレームに該当するBBのみが表示される
- BBが他のフレームに漏れて表示されない
- シーンアイテム数が正確に管理される
"""

import pytest
import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor
from typing import List, Dict, Any

# テスト対象モジュール
sys.path.append('/media/thithilab/volume/auto_anotatation/src')
from presentation.bb_canvas.canvas_widget import BBCanvas
from presentation.bb_canvas.bb_renderer import BBRenderer


@pytest.mark.bb_isolation
@pytest.mark.integration
@pytest.mark.gui
class TestFrameSpecificBBRendering:
    """フレーム別BB描画テスト"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """テスト前セットアップ"""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
            
        # テスト用キャンバス作成
        self.canvas = BBCanvas(use_opengl=False)
        
        # テスト用フレーム画像作成
        self.frame1_pixmap = QPixmap(800, 600)
        self.frame1_pixmap.fill(QColor(255, 0, 0))  # 赤
        
        self.frame2_pixmap = QPixmap(800, 600)
        self.frame2_pixmap.fill(QColor(0, 255, 0))  # 緑
        
        self.frame3_pixmap = QPixmap(800, 600)
        self.frame3_pixmap.fill(QColor(0, 0, 255))  # 青
        
        # テスト用BBデータ作成
        self.frame1_bbs = [
            {
                'id': 'frame1_bb1',
                'x': 0.3, 'y': 0.3, 'w': 0.2, 'h': 0.2,
                'individual_id': 0, 'action_id': 0,
                'confidence': 0.9
            },
            {
                'id': 'frame1_bb2',
                'x': 0.7, 'y': 0.7, 'w': 0.15, 'h': 0.15,
                'individual_id': 1, 'action_id': 1,
                'confidence': 0.85
            }
        ]
        
        self.frame2_bbs = [
            {
                'id': 'frame2_bb1',
                'x': 0.4, 'y': 0.4, 'w': 0.25, 'h': 0.25,
                'individual_id': 2, 'action_id': 2,
                'confidence': 0.92
            }
        ]
        
        self.frame3_bbs = [
            {
                'id': 'frame3_bb1',
                'x': 0.2, 'y': 0.2, 'w': 0.3, 'h': 0.3,
                'individual_id': 3, 'action_id': 3,
                'confidence': 0.88
            },
            {
                'id': 'frame3_bb2',
                'x': 0.6, 'y': 0.6, 'w': 0.2, 'h': 0.2,
                'individual_id': 4, 'action_id': 4,
                'confidence': 0.91
            },
            {
                'id': 'frame3_bb3',
                'x': 0.5, 'y': 0.3, 'w': 0.18, 'h': 0.18,
                'individual_id': 5, 'action_id': 0,
                'confidence': 0.87
            }
        ]
        
        yield
        
        # テスト後クリーンアップ
        if hasattr(self, 'canvas'):
            self.canvas.close()
            
    def wait_for_ui_update(self, timeout_ms: int = 100):
        """UI更新待機"""
        start_time = time.time()
        while time.time() - start_time < timeout_ms / 1000:
            QApplication.processEvents()
            time.sleep(0.01)
            
    def get_scene_bb_count(self) -> int:
        """シーン内のBBアイテム数を取得"""
        bb_count = 0
        for item in self.canvas.scene.items():
            # BBGraphicsItemかどうかを判定
            if hasattr(item, 'bb_entity'):
                bb_count += 1
        return bb_count
        
    def get_rendered_bb_ids(self) -> List[str]:
        """レンダリングされたBB IDリストを取得"""
        bb_ids = []
        if hasattr(self.canvas.bb_renderer, 'rendered_items'):
            for item in self.canvas.bb_renderer.rendered_items:
                if hasattr(item, 'bb_entity') and hasattr(item.bb_entity, 'id'):
                    bb_ids.append(item.bb_entity.id)
        return bb_ids
        
    def test_single_frame_bb_display(self):
        """単一フレームのBB表示テスト"""
        # フレーム1表示
        self.canvas.display_frame(self.frame1_pixmap)
        self.wait_for_ui_update()
        
        # フレーム1のBB表示
        self.canvas.update_bounding_boxes(self.frame1_bbs)
        self.wait_for_ui_update()
        
        # BB数確認
        scene_bb_count = self.get_scene_bb_count()
        rendered_bb_ids = self.get_rendered_bb_ids()
        
        assert scene_bb_count == len(self.frame1_bbs), f"シーン内BB数が不正: 期待値{len(self.frame1_bbs)}, 実際{scene_bb_count}"
        assert len(rendered_bb_ids) == len(self.frame1_bbs), f"レンダリングBB数が不正: 期待値{len(self.frame1_bbs)}, 実際{len(rendered_bb_ids)}"
        
        # BB ID確認
        expected_ids = {bb['id'] for bb in self.frame1_bbs}
        actual_ids = set(rendered_bb_ids)
        assert actual_ids == expected_ids, f"BB ID不一致: 期待値{expected_ids}, 実際{actual_ids}"
        
    def test_frame_switching_bb_isolation(self):
        """フレーム切り替え時のBB分離テスト"""
        # フレーム1表示とBB描画
        self.canvas.display_frame(self.frame1_pixmap)
        self.canvas.update_bounding_boxes(self.frame1_bbs)
        self.wait_for_ui_update()
        
        # フレーム1のBB確認
        frame1_bb_count = self.get_scene_bb_count()
        frame1_bb_ids = set(self.get_rendered_bb_ids())
        
        assert frame1_bb_count == len(self.frame1_bbs)
        assert frame1_bb_ids == {bb['id'] for bb in self.frame1_bbs}
        
        # フレーム2に切り替え
        self.canvas.display_frame(self.frame2_pixmap)
        self.canvas.update_bounding_boxes(self.frame2_bbs)
        self.wait_for_ui_update()
        
        # フレーム2のBB確認（フレーム1のBBが残っていないこと）
        frame2_bb_count = self.get_scene_bb_count()
        frame2_bb_ids = set(self.get_rendered_bb_ids())
        
        assert frame2_bb_count == len(self.frame2_bbs), f"フレーム2でBB数が不正: 期待値{len(self.frame2_bbs)}, 実際{frame2_bb_count}"
        assert frame2_bb_ids == {bb['id'] for bb in self.frame2_bbs}, f"フレーム2でBB ID不一致"
        
        # フレーム1のBBが残っていないことを確認
        frame1_ids_in_frame2 = frame1_bb_ids.intersection(frame2_bb_ids)
        assert len(frame1_ids_in_frame2) == 0, f"フレーム1のBBがフレーム2に残存: {frame1_ids_in_frame2}"
        
    def test_multiple_frame_transitions(self):
        """複数フレーム遷移テスト"""
        frames_and_bbs = [
            (self.frame1_pixmap, self.frame1_bbs),
            (self.frame2_pixmap, self.frame2_bbs),
            (self.frame3_pixmap, self.frame3_bbs),
            (self.frame1_pixmap, self.frame1_bbs),  # フレーム1に戻る
            (self.frame2_pixmap, self.frame2_bbs),  # フレーム2に戻る
        ]
        
        for i, (frame_pixmap, frame_bbs) in enumerate(frames_and_bbs):
            print(f"フレーム遷移テスト {i+1}/{len(frames_and_bbs)}")
            
            # フレーム表示とBB描画
            self.canvas.display_frame(frame_pixmap)
            self.canvas.update_bounding_boxes(frame_bbs)
            self.wait_for_ui_update()
            
            # BB数とID確認
            scene_bb_count = self.get_scene_bb_count()
            rendered_bb_ids = set(self.get_rendered_bb_ids())
            expected_bb_ids = {bb['id'] for bb in frame_bbs}
            
            assert scene_bb_count == len(frame_bbs), f"遷移{i+1}: シーン内BB数不正 期待値{len(frame_bbs)}, 実際{scene_bb_count}"
            assert rendered_bb_ids == expected_bb_ids, f"遷移{i+1}: BB ID不一致 期待値{expected_bb_ids}, 実際{rendered_bb_ids}"
            
            # 他のフレームのBBが混入していないことを確認
            all_other_bb_ids = set()
            for other_frame_pixmap, other_frame_bbs in frames_and_bbs:
                if other_frame_bbs != frame_bbs:
                    all_other_bb_ids.update(bb['id'] for bb in other_frame_bbs)
                    
            leaked_bb_ids = rendered_bb_ids.intersection(all_other_bb_ids)
            assert len(leaked_bb_ids) == 0, f"遷移{i+1}: 他フレームのBBが混入 {leaked_bb_ids}"
            
    def test_empty_frame_bb_handling(self):
        """空フレーム（BBなし）の処理テスト"""
        # フレーム1にBBを表示
        self.canvas.display_frame(self.frame1_pixmap)
        self.canvas.update_bounding_boxes(self.frame1_bbs)
        self.wait_for_ui_update()
        
        # BB表示確認
        assert self.get_scene_bb_count() == len(self.frame1_bbs)
        
        # 空のBBリストで更新（BBなしフレーム）
        self.canvas.update_bounding_boxes([])
        self.wait_for_ui_update()
        
        # BBが全てクリアされていることを確認
        scene_bb_count = self.get_scene_bb_count()
        rendered_bb_ids = self.get_rendered_bb_ids()
        
        assert scene_bb_count == 0, f"空フレーム後にBBが残存: シーン内{scene_bb_count}個"
        assert len(rendered_bb_ids) == 0, f"空フレーム後にレンダリング済みBBが残存: {rendered_bb_ids}"
        
    def test_bb_renderer_state_consistency(self):
        """BBレンダラー状態一貫性テスト"""
        # 初期状態確認
        assert len(self.canvas.bb_renderer.rendered_items) == 0
        
        # フレーム1表示
        self.canvas.display_frame(self.frame1_pixmap)
        self.canvas.update_bounding_boxes(self.frame1_bbs)
        self.wait_for_ui_update()
        
        # レンダラー状態確認
        assert len(self.canvas.bb_renderer.rendered_items) == len(self.frame1_bbs)
        
        # フレーム2切り替え
        self.canvas.display_frame(self.frame2_pixmap)
        self.canvas.update_bounding_boxes(self.frame2_bbs)
        self.wait_for_ui_update()
        
        # レンダラー状態更新確認
        assert len(self.canvas.bb_renderer.rendered_items) == len(self.frame2_bbs)
        
        # 前フレームのアイテムがrenderer内に残っていないことを確認
        current_bb_ids = {item.bb_entity.id for item in self.canvas.bb_renderer.rendered_items if hasattr(item, 'bb_entity')}
        frame1_bb_ids = {bb['id'] for bb in self.frame1_bbs}
        frame2_bb_ids = {bb['id'] for bb in self.frame2_bbs}
        
        assert current_bb_ids == frame2_bb_ids, f"レンダラー内BB ID不一致: 期待値{frame2_bb_ids}, 実際{current_bb_ids}"
        assert not current_bb_ids.intersection(frame1_bb_ids), f"前フレームのBBがレンダラー内に残存: {current_bb_ids.intersection(frame1_bb_ids)}"
        
    def test_performance_bb_clearing(self):
        """BB描画性能テスト（クリア処理含む）"""
        # 大量BBでのテスト
        large_bb_list = []
        for i in range(50):  # 50個のBB
            large_bb_list.append({
                'id': f'perf_bb_{i}',
                'x': 0.1 + (i % 10) * 0.08,
                'y': 0.1 + (i // 10) * 0.18,
                'w': 0.05, 'h': 0.05,
                'individual_id': i % 16,
                'action_id': i % 5,
                'confidence': 0.8 + (i % 20) * 0.01
            })
            
        # フレーム表示と大量BB描画
        start_time = time.perf_counter()
        self.canvas.display_frame(self.frame1_pixmap)
        self.canvas.update_bounding_boxes(large_bb_list)
        self.wait_for_ui_update()
        display_time = (time.perf_counter() - start_time) * 1000
        
        # 性能要件確認（100ms以下）
        assert display_time < 100, f"大量BB表示時間が性能要件超過: {display_time:.2f}ms > 100ms"
        
        # 切り替え性能確認
        start_time = time.perf_counter()
        self.canvas.display_frame(self.frame2_pixmap)
        self.canvas.update_bounding_boxes([])  # 空フレーム
        self.wait_for_ui_update()
        clear_time = (time.perf_counter() - start_time) * 1000
        
        # クリア性能要件確認（50ms以下）
        assert clear_time < 50, f"大量BBクリア時間が性能要件超過: {clear_time:.2f}ms > 50ms"
        
        # 完全クリア確認
        assert self.get_scene_bb_count() == 0, "大量BB後のクリアが不完全"


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])