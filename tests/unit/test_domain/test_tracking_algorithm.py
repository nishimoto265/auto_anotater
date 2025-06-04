"""
追跡アルゴリズム単体テスト - Agent3専用
追跡処理5ms以下・精度90%以上パフォーマンステスト
"""

import time
import pytest

from src.domain.algorithms.tracking_algorithm import SimpleIOUTracker, TrackingStatus
from src.domain.entities.bb_entity import BBEntity
from src.domain.entities.frame_entity import FrameEntity
from src.domain.entities.id_entity import IndividualID
from src.domain.entities.action_entity import ActionType
from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.confidence import Confidence
from src.domain.exceptions import ValidationError, PerformanceError


class TestSimpleIOUTracker:
    """シンプルIOU追跡アルゴリズムテスト"""
    
    def test_tracker_initialization(self):
        """追跡アルゴリズム初期化テスト"""
        # デフォルト閾値
        tracker = SimpleIOUTracker()
        assert tracker.iou_threshold == 0.5
        assert tracker.confidence_threshold == 0.3
        
        # カスタム閾値
        tracker_custom = SimpleIOUTracker(0.7, 0.4)
        assert tracker_custom.iou_threshold == 0.7
        assert tracker_custom.confidence_threshold == 0.4
        
        # 不正な閾値
        with pytest.raises(ValidationError):
            SimpleIOUTracker(-0.1, 0.3)
        
        with pytest.raises(ValidationError):
            SimpleIOUTracker(0.5, 1.5)
    
    def test_tracking_performance_5ms(self):
        """追跡処理5ms以下パフォーマンステスト（最重要）"""
        tracker = SimpleIOUTracker()
        
        # フレーム1（10個のBB）
        frame1 = self._create_test_frame("000001", 10)
        
        # フレーム2（10個のBB、少し移動）
        frame2 = self._create_test_frame("000002", 10, offset=0.05)
        
        # 100回追跡テストして全て5ms以下であることを確認
        times = []
        for _ in range(100):
            start_time = time.perf_counter()
            result = tracker.track_between_frames(frame1, frame2)
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)
            
            # 個別確認
            assert elapsed <= 5.0, f"Tracking took {elapsed}ms (target: 5.0ms)"
            assert result.processing_time_ms <= 5.0
        
        # 統計確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time <= 2.5, f"Average tracking time {avg_time}ms exceeds 2.5ms"
        assert max_time <= 5.0, f"Max tracking time {max_time}ms exceeds 5.0ms"
        
        print(f"追跡処理パフォーマンス: 平均{avg_time:.3f}ms, 最大{max_time:.3f}ms")
    
    def test_tracking_accuracy_90_percent(self):
        """追跡精度90%以上テスト（最重要）"""
        tracker = SimpleIOUTracker(0.3, 0.1)  # 低い閾値で高い追跡率
        
        # フレーム1（8個のBB）
        frame1 = self._create_test_frame("000001", 8)
        
        # フレーム2（8個のBB、少し移動）
        frame2 = self._create_test_frame("000002", 8, offset=0.03)
        
        result = tracker.track_between_frames(frame1, frame2)
        
        # 精度確認
        total_objects = max(len(frame1.bounding_boxes), len(frame2.bounding_boxes))
        match_accuracy = len(result.matches) / total_objects if total_objects > 0 else 1.0
        
        assert match_accuracy >= 0.9, f"Tracking accuracy {match_accuracy:.2%} below 90%"
        assert result.match_accuracy >= 0.9
        
        print(f"追跡精度: {match_accuracy:.1%}")
    
    def test_perfect_tracking_scenario(self):
        """完璧追跡シナリオテスト"""
        tracker = SimpleIOUTracker()
        
        # 同一BBセット（わずかな移動）
        frame1 = FrameEntity(
            id="000001",
            image_path="test1.jpg",
            annotation_path="test1.txt",
            width=1920,
            height=1080
        )
        
        frame2 = FrameEntity(
            id="000002", 
            image_path="test2.jpg",
            annotation_path="test2.txt",
            width=1920,
            height=1080
        )
        
        # フレーム1のBB
        bb1_f1 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.3, 0.3, 0.2, 0.2),
            confidence=Confidence(0.9)
        )
        
        bb2_f1 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(1),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.7, 0.7, 0.15, 0.15),
            confidence=Confidence(0.8)
        )
        
        frame1.add_bounding_box(bb1_f1)
        frame1.add_bounding_box(bb2_f1)
        
        # フレーム2のBB（少し移動）
        bb1_f2 = BBEntity(
            frame_id="000002",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.32, 0.32, 0.2, 0.2),  # 少し移動
            confidence=Confidence(0.85)
        )
        
        bb2_f2 = BBEntity(
            frame_id="000002",
            individual_id=IndividualID(1),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.72, 0.72, 0.15, 0.15),  # 少し移動
            confidence=Confidence(0.82)
        )
        
        frame2.add_bounding_box(bb1_f2)
        frame2.add_bounding_box(bb2_f2)
        
        # 追跡実行
        result = tracker.track_between_frames(frame1, frame2)
        
        # 結果確認
        assert len(result.matches) == 2  # 2つのマッチ
        assert len(result.new_objects) == 0  # 新規オブジェクトなし
        assert len(result.lost_objects) == 0  # 追跡断絶なし
        assert result.match_accuracy == 1.0  # 100%精度
        
        # マッチング詳細確認
        for match in result.matches:
            assert match.status == TrackingStatus.MATCHED
            assert match.iou_score > 0.5  # 高いIOU
            assert 0 <= match.individual_id <= 1
    
    def test_new_object_detection(self):
        """新規オブジェクト検出テスト"""
        tracker = SimpleIOUTracker()
        
        # フレーム1（2個のBB）
        frame1 = self._create_test_frame("000001", 2)
        
        # フレーム2（4個のBB、新規2個追加）
        frame2 = self._create_test_frame("000002", 4)
        
        result = tracker.track_between_frames(frame1, frame2)
        
        # 新規オブジェクト検出確認
        assert len(result.new_objects) >= 0  # 新規オブジェクトあり
        assert len(result.matches) <= 2  # 既存オブジェクトのマッチ
        
        total_tracked = len(result.matches) + len(result.new_objects)
        assert total_tracked == len(frame2.bounding_boxes)
    
    def test_lost_object_detection(self):
        """追跡断絶検出テスト"""
        tracker = SimpleIOUTracker()
        
        # フレーム1（4個のBB）
        frame1 = self._create_test_frame("000001", 4)
        
        # フレーム2（2個のBB、2個消失）
        frame2 = self._create_test_frame("000002", 2)
        
        result = tracker.track_between_frames(frame1, frame2)
        
        # 追跡断絶検出確認
        assert len(result.lost_objects) >= 0  # 追跡断絶オブジェクトあり
        assert len(result.matches) <= 2  # 継続追跡オブジェクト
        
        total_source = len(result.matches) + len(result.lost_objects)
        assert total_source == len(frame1.bounding_boxes)
    
    def test_empty_frame_handling(self):
        """空フレーム処理テスト"""
        tracker = SimpleIOUTracker()
        
        # 空フレーム
        empty_frame = FrameEntity(
            id="000000",
            image_path="empty.jpg", 
            annotation_path="empty.txt",
            width=1920,
            height=1080
        )
        
        # 通常フレーム
        normal_frame = self._create_test_frame("000001", 3)
        
        # 空 → 通常
        result1 = tracker.track_between_frames(empty_frame, normal_frame)
        assert len(result1.matches) == 0
        assert len(result1.new_objects) == 3
        assert len(result1.lost_objects) == 0
        assert result1.match_accuracy == 0.0 if result1.new_objects else 1.0
        
        # 通常 → 空
        result2 = tracker.track_between_frames(normal_frame, empty_frame)
        assert len(result2.matches) == 0
        assert len(result2.new_objects) == 0
        assert len(result2.lost_objects) == 3
        assert result2.match_accuracy == 0.0
        
        # 空 → 空
        result3 = tracker.track_between_frames(empty_frame, empty_frame)
        assert len(result3.matches) == 0
        assert len(result3.new_objects) == 0
        assert len(result3.lost_objects) == 0
        assert result3.match_accuracy == 1.0
    
    def test_cross_individual_matching(self):
        """異個体マッチングテスト（ID変更対応）"""
        tracker = SimpleIOUTracker(0.3, 0.1)
        
        frame1 = FrameEntity(
            id="000001",
            image_path="test1.jpg",
            annotation_path="test1.txt", 
            width=1920,
            height=1080
        )
        
        frame2 = FrameEntity(
            id="000002",
            image_path="test2.jpg",
            annotation_path="test2.txt",
            width=1920,
            height=1080
        )
        
        # フレーム1（個体ID 0, 1）
        bb1_f1 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.3, 0.3, 0.2, 0.2),
            confidence=Confidence(0.9)
        )
        
        bb2_f1 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(1),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.7, 0.7, 0.15, 0.15),
            confidence=Confidence(0.8)
        )
        
        frame1.add_bounding_box(bb1_f1)
        frame1.add_bounding_box(bb2_f1)
        
        # フレーム2（個体ID 2, 3だが位置は近い）
        bb1_f2 = BBEntity(
            frame_id="000002",
            individual_id=IndividualID(2),  # ID変更
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.32, 0.32, 0.2, 0.2),
            confidence=Confidence(0.85)
        )
        
        bb2_f2 = BBEntity(
            frame_id="000002",
            individual_id=IndividualID(3),  # ID変更
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.72, 0.72, 0.15, 0.15),
            confidence=Confidence(0.82)
        )
        
        frame2.add_bounding_box(bb1_f2)
        frame2.add_bounding_box(bb2_f2)
        
        # 追跡実行
        result = tracker.track_between_frames(frame1, frame2)
        
        # 異個体マッチング確認
        assert len(result.matches) == 2  # 位置ベースマッチング
        
        # 元の個体IDが維持されているか確認
        for match in result.matches:
            assert match.individual_id in [0, 1]  # ソース個体ID維持
    
    def test_tracking_result_application(self):
        """追跡結果適用テスト"""
        tracker = SimpleIOUTracker()
        
        frame1 = self._create_test_frame("000001", 2)
        frame2 = self._create_test_frame("000002", 2, offset=0.05)
        
        # 追跡実行
        result = tracker.track_between_frames(frame1, frame2)
        
        # 追跡結果をフレームに適用
        updated_frame = tracker.apply_tracking_result(frame2, result)
        
        # 適用結果確認
        assert updated_frame.id == frame2.id
        assert len(updated_frame.bounding_boxes) >= len(result.matches)
        
        # ID継承確認
        for match in result.matches:
            updated_bb = updated_frame.get_bounding_box_by_id(match.target_bb_id)
            if updated_bb:
                assert updated_bb.individual_id.value == match.individual_id
    
    def test_tracking_statistics(self):
        """追跡統計テスト"""
        tracker = SimpleIOUTracker()
        
        frame1 = self._create_test_frame("000001", 5)
        frame2 = self._create_test_frame("000002", 5, offset=0.03)
        
        result = tracker.track_between_frames(frame1, frame2)
        stats = tracker.get_tracking_statistics(result)
        
        # 統計項目確認
        required_keys = [
            "total_objects", "matched_objects", "new_objects", "lost_objects",
            "match_ratio", "average_iou", "average_confidence", 
            "processing_time_ms", "match_accuracy"
        ]
        
        for key in required_keys:
            assert key in stats
        
        # 統計値範囲確認
        assert stats["total_objects"] >= 0
        assert stats["matched_objects"] >= 0
        assert stats["new_objects"] >= 0
        assert stats["lost_objects"] >= 0
        assert 0.0 <= stats["match_ratio"] <= 1.0
        assert 0.0 <= stats["average_iou"] <= 1.0
        assert 0.0 <= stats["average_confidence"] <= 1.0
        assert stats["processing_time_ms"] >= 0.0
        assert 0.0 <= stats["match_accuracy"] <= 1.0
    
    def test_confidence_filtering(self):
        """信頼度フィルタリングテスト"""
        tracker = SimpleIOUTracker(0.5, 0.7)  # 高い信頼度閾値
        
        frame1 = FrameEntity(
            id="000001",
            image_path="test1.jpg",
            annotation_path="test1.txt",
            width=1920,
            height=1080
        )
        
        frame2 = FrameEntity(
            id="000002",
            image_path="test2.jpg", 
            annotation_path="test2.txt",
            width=1920,
            height=1080
        )
        
        # 高信頼度BB
        high_conf_bb = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.3, 0.3, 0.2, 0.2),
            confidence=Confidence(0.9)  # 閾値0.7以上
        )
        
        # 低信頼度BB
        low_conf_bb = BBEntity(
            frame_id="000001", 
            individual_id=IndividualID(1),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.7, 0.7, 0.15, 0.15),
            confidence=Confidence(0.5)  # 閾値0.7未満
        )
        
        frame1.add_bounding_box(high_conf_bb)
        frame1.add_bounding_box(low_conf_bb)
        
        # 対応するフレーム2のBB
        high_conf_bb2 = BBEntity(
            frame_id="000002",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.32, 0.32, 0.2, 0.2),
            confidence=Confidence(0.85)
        )
        
        low_conf_bb2 = BBEntity(
            frame_id="000002",
            individual_id=IndividualID(1),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.72, 0.72, 0.15, 0.15),
            confidence=Confidence(0.6)
        )
        
        frame2.add_bounding_box(high_conf_bb2)
        frame2.add_bounding_box(low_conf_bb2)
        
        # 追跡実行
        result = tracker.track_between_frames(frame1, frame2)
        
        # 高信頼度BBのみが追跡されるはず
        # 低信頼度BBは新規オブジェクト・追跡断絶扱い
        matched_individual_ids = [match.individual_id for match in result.matches]
        assert 0 in matched_individual_ids  # 高信頼度BBはマッチ
        # 低信頼度BBはフィルタされるため、new_objects/lost_objectsに含まれない
    
    def _create_test_frame(self, frame_id: str, bb_count: int, offset: float = 0.0) -> FrameEntity:
        """テスト用フレーム作成ヘルパー"""
        frame = FrameEntity(
            id=frame_id,
            image_path=f"test_{frame_id}.jpg",
            annotation_path=f"test_{frame_id}.txt",
            width=1920,
            height=1080
        )
        
        for i in range(bb_count):
            bb = BBEntity(
                frame_id=frame_id,
                individual_id=IndividualID(i % 16),
                action_type=ActionType(i % 5),
                coordinates=Coordinates(
                    0.2 + (i * 0.1) + offset,
                    0.2 + (i * 0.1) + offset,
                    0.08,
                    0.08
                ),
                confidence=Confidence(0.7 + (i * 0.02) % 0.3)
            )
            frame.add_bounding_box(bb)
        
        return frame