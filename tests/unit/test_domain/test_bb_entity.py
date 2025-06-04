"""
BBエンティティ単体テスト - Agent3専用
エンティティ検証・ビジネスルール・操作性能テスト
"""

import time
import pytest
from datetime import datetime

from src.domain.entities.bb_entity import BBEntity
from src.domain.entities.id_entity import IndividualID
from src.domain.entities.action_entity import ActionType
from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.confidence import Confidence
from src.domain.exceptions import ValidationError, BusinessRuleViolationError, PerformanceError


class TestBBEntity:
    """BBエンティティテスト"""
    
    def test_bb_entity_creation_success(self):
        """BBエンティティ作成成功ケース"""
        bb = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(5),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
            confidence=Confidence(0.8)
        )
        
        assert bb.frame_id == "000001"
        assert bb.individual_id.value == 5
        assert bb.action_type == ActionType.STAND
        assert bb.coordinates.x == 0.5
        assert bb.confidence.value == 0.8
        assert bb.id is not None  # UUID自動生成
        assert isinstance(bb.created_at, datetime)
        assert isinstance(bb.updated_at, datetime)
    
    def test_bb_entity_validation_performance_1ms(self):
        """BBエンティティ検証1ms以下パフォーマンステスト（最重要）"""
        # 1000回作成テストして全て1ms以下であることを確認
        times = []
        for i in range(1000):
            start_time = time.perf_counter()
            
            bb = BBEntity(
                frame_id=f"{i:06d}",
                individual_id=IndividualID(i % 16),
                action_type=ActionType(i % 5),
                coordinates=Coordinates(0.5, 0.5, 0.1, 0.1),
                confidence=Confidence(0.7)
            )
            
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)
            
            # 個別確認
            assert elapsed <= 1.0, f"BB entity validation took {elapsed}ms (target: 1.0ms)"
            assert bb.frame_id == f"{i:06d}"
        
        # 統計確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time <= 0.5, f"Average validation time {avg_time}ms exceeds 0.5ms"
        assert max_time <= 1.0, f"Max validation time {max_time}ms exceeds 1.0ms"
        
        print(f"BBエンティティ検証パフォーマンス: 平均{avg_time:.3f}ms, 最大{max_time:.3f}ms")
    
    def test_bb_entity_required_field_validation(self):
        """必須フィールド検証テスト"""
        # フレームIDなし
        with pytest.raises(ValidationError):
            BBEntity(
                frame_id="",
                individual_id=IndividualID(0),
                action_type=ActionType.SIT,
                coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
                confidence=Confidence(0.8)
            )
        
        # 不正な個体ID型
        with pytest.raises(ValidationError):
            BBEntity(
                frame_id="000001",
                individual_id="invalid",  # IndividualIDではない
                action_type=ActionType.SIT,
                coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
                confidence=Confidence(0.8)
            )
    
    def test_bb_minimum_size_business_rule(self):
        """BB最小サイズビジネスルールテスト"""
        # 最小サイズ以下（0.01% x 0.01% = 0.0001未満）
        with pytest.raises(BusinessRuleViolationError):
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(0),
                action_type=ActionType.SIT,
                coordinates=Coordinates(0.5, 0.5, 0.005, 0.005),  # 0.000025 < 0.0001
                confidence=Confidence(0.8)
            )
        
        # 最小サイズギリギリOK
        bb = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.5, 0.5, 0.01, 0.01),  # 0.0001
            confidence=Confidence(0.8)
        )
        assert bb.get_area() == 0.0001
    
    def test_bb_entity_operations(self):
        """BBエンティティ操作テスト"""
        bb = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(3),
            action_type=ActionType.MILK,
            coordinates=Coordinates(0.6, 0.4, 0.3, 0.2),
            confidence=Confidence(0.9)
        )
        
        # 面積取得
        area = bb.get_area()
        assert abs(area - 0.06) < 1e-6  # 0.3 * 0.2 = 0.06
        
        # 中心座標取得
        center = bb.get_center()
        assert center == (0.6, 0.4)
        
        # 色取得
        color = bb.get_color()
        assert color.individual_id == 3
        
        # 信頼度判定
        assert bb.is_high_confidence()  # 0.9 > 0.8
        assert not bb.is_low_confidence()  # 0.9 > 0.3
    
    def test_bb_entity_overlap_detection(self):
        """BB重複検知テスト"""
        bb1 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
            confidence=Confidence(0.8)
        )
        
        # 重複あり
        bb2 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(1),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.55, 0.55, 0.2, 0.2),  # 重複
            confidence=Confidence(0.7)
        )
        
        # 重複なし
        bb3 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(2),
            action_type=ActionType.FOOD,
            coordinates=Coordinates(0.2, 0.2, 0.1, 0.1),  # 重複なし
            confidence=Confidence(0.6)
        )
        
        assert bb1.overlaps_with(bb2, 0.1)  # 重複検知
        assert not bb1.overlaps_with(bb3, 0.1)  # 重複なし
    
    def test_bb_entity_iou_calculation(self):
        """BBエンティティIOU計算テスト"""
        bb1 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
            confidence=Confidence(0.8)
        )
        
        # 同じBB（IOU = 1.0）
        bb2 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(1),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
            confidence=Confidence(0.7)
        )
        
        iou = bb1.calculate_iou_with(bb2)
        assert abs(iou - 1.0) < 1e-6
    
    def test_bb_entity_update_operations(self):
        """BBエンティティ更新操作テスト（不変性確認）"""
        original_bb = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(5),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
            confidence=Confidence(0.8)
        )
        
        # 座標更新（新インスタンス生成）
        new_coords = Coordinates(0.6, 0.6, 0.3, 0.3)
        updated_bb = original_bb.update_coordinates(new_coords)
        
        # 元のBBは変更されない
        assert original_bb.coordinates.x == 0.5
        assert updated_bb.coordinates.x == 0.6
        assert original_bb.id == updated_bb.id  # IDは同じ
        assert updated_bb.updated_at > original_bb.updated_at
        
        # 個体ID更新
        new_individual_id = IndividualID(10)
        id_updated_bb = original_bb.update_individual_id(new_individual_id)
        
        assert original_bb.individual_id.value == 5
        assert id_updated_bb.individual_id.value == 10
        
        # 行動タイプ更新
        action_updated_bb = original_bb.update_action_type(ActionType.WATER)
        
        assert original_bb.action_type == ActionType.SIT
        assert action_updated_bb.action_type == ActionType.WATER
        
        # 信頼度更新
        confidence_updated_bb = original_bb.update_confidence(Confidence(0.9))
        
        assert original_bb.confidence.value == 0.8
        assert confidence_updated_bb.confidence.value == 0.9
    
    def test_bb_entity_yolo_format_conversion(self):
        """BBエンティティYOLO形式変換テスト"""
        bb = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(7),
            action_type=ActionType.WATER,
            coordinates=Coordinates(0.5123, 0.3456, 0.1234, 0.0987),
            confidence=Confidence(0.9512)
        )
        
        # YOLO形式文字列生成
        yolo_str = bb.to_yolo_format()
        expected = "7 0.5123 0.3456 0.1234 0.0987 3 0.9512"
        assert yolo_str == expected
        
        # YOLO形式からBBエンティティ生成
        restored_bb = BBEntity.from_yolo_format(yolo_str, "000001", "test_id")
        
        assert restored_bb.frame_id == "000001"
        assert restored_bb.individual_id.value == 7
        assert restored_bb.action_type == ActionType.WATER
        assert abs(restored_bb.coordinates.x - 0.5123) < 1e-6
        assert abs(restored_bb.coordinates.y - 0.3456) < 1e-6
        assert abs(restored_bb.coordinates.w - 0.1234) < 1e-6
        assert abs(restored_bb.coordinates.h - 0.0987) < 1e-6
        assert abs(restored_bb.confidence.value - 0.9512) < 1e-6
    
    def test_bb_entity_yolo_format_validation(self):
        """YOLO形式検証テスト"""
        # 不正な形式（要素数不足）
        with pytest.raises(ValidationError):
            BBEntity.from_yolo_format("7 0.5 0.3 0.1", "000001")
        
        # 不正な個体ID
        with pytest.raises(ValidationError):
            BBEntity.from_yolo_format("20 0.5 0.3 0.1 0.1 2 0.8", "000001")
        
        # 不正な行動ID
        with pytest.raises(ValidationError):
            BBEntity.from_yolo_format("7 0.5 0.3 0.1 0.1 7 0.8", "000001")
    
    def test_bb_entity_clone_operation(self):
        """BBエンティティ複製操作テスト"""
        original_bb = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(2),
            action_type=ActionType.FOOD,
            coordinates=Coordinates(0.3, 0.7, 0.15, 0.25),
            confidence=Confidence(0.85)
        )
        
        # 部分更新で複製
        cloned_bb = original_bb.clone(
            frame_id="000002",
            individual_id=IndividualID(8)
        )
        
        # 更新されたフィールド
        assert cloned_bb.frame_id == "000002"
        assert cloned_bb.individual_id.value == 8
        
        # 更新されていないフィールド
        assert cloned_bb.action_type == ActionType.FOOD
        assert cloned_bb.coordinates.x == 0.3
        assert cloned_bb.confidence.value == 0.85
        
        # IDは同じ（同一BBの複製）
        assert cloned_bb.id == original_bb.id
    
    def test_bb_entity_same_individual_detection(self):
        """同一個体判定テスト"""
        bb1 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(3),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
            confidence=Confidence(0.8)
        )
        
        bb2 = BBEntity(
            frame_id="000002",
            individual_id=IndividualID(3),  # 同じ個体ID
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.6, 0.6, 0.25, 0.25),
            confidence=Confidence(0.9)
        )
        
        bb3 = BBEntity(
            frame_id="000002",
            individual_id=IndividualID(5),  # 異なる個体ID
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.6, 0.6, 0.25, 0.25),
            confidence=Confidence(0.9)
        )
        
        assert bb1.is_same_individual(bb2)
        assert not bb1.is_same_individual(bb3)