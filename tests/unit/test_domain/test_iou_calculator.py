"""
IOU計算アルゴリズム単体テスト - Agent3専用
IOU計算1ms以下・バッチ処理パフォーマンステスト
"""

import time
import pytest
import numpy as np

from src.domain.algorithms.iou_calculator import IOUCalculator
from src.domain.entities.bb_entity import BBEntity
from src.domain.entities.id_entity import IndividualID
from src.domain.entities.action_entity import ActionType
from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.confidence import Confidence
from src.domain.exceptions import PerformanceError


class TestIOUCalculator:
    """IOU計算アルゴリズムテスト"""
    
    def test_single_iou_calculation_performance_1ms(self):
        """単体IOU計算1ms以下パフォーマンステスト（最重要）"""
        bb1 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
            confidence=Confidence(0.8)
        )
        
        bb2 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(1),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.6, 0.6, 0.2, 0.2),
            confidence=Confidence(0.7)
        )
        
        # 1000回テストして全て1ms以下であることを確認
        times = []
        for _ in range(1000):
            start_time = time.perf_counter()
            iou = IOUCalculator.calculate_iou(bb1, bb2)
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)
            
            # 個別確認
            assert elapsed <= 1.0, f"IOU calculation took {elapsed}ms (target: 1.0ms)"
            assert 0.0 <= iou <= 1.0
        
        # 統計確認
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time <= 0.5, f"Average IOU time {avg_time}ms exceeds 0.5ms"
        assert max_time <= 1.0, f"Max IOU time {max_time}ms exceeds 1.0ms"
        
        print(f"単体IOU計算パフォーマンス: 平均{avg_time:.3f}ms, 最大{max_time:.3f}ms")
    
    def test_iou_calculation_accuracy(self):
        """IOU計算精度テスト"""
        # テストケース1: 完全一致 (IOU = 1.0)
        bb1 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(0),
            action_type=ActionType.SIT,
            coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
            confidence=Confidence(0.8)
        )
        
        bb2 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(1),
            action_type=ActionType.STAND,
            coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
            confidence=Confidence(0.7)
        )
        
        iou = IOUCalculator.calculate_iou(bb1, bb2)
        assert abs(iou - 1.0) < 1e-6
        
        # テストケース2: 重複なし (IOU = 0.0)
        bb3 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(2),
            action_type=ActionType.MILK,
            coordinates=Coordinates(0.2, 0.2, 0.1, 0.1),
            confidence=Confidence(0.9)
        )
        
        iou = IOUCalculator.calculate_iou(bb1, bb3)
        assert abs(iou - 0.0) < 1e-6
        
        # テストケース3: 部分重複（手計算確認）
        bb4 = BBEntity(
            frame_id="000001",
            individual_id=IndividualID(3),
            action_type=ActionType.WATER,
            coordinates=Coordinates(0.6, 0.5, 0.2, 0.2),  # X方向にずらす
            confidence=Confidence(0.6)
        )
        
        iou = IOUCalculator.calculate_iou(bb1, bb4)
        # 手計算: 重複幅=0.1, 重複高さ=0.2, 重複面積=0.02
        # Union面積 = 0.04 + 0.04 - 0.02 = 0.06
        # IOU = 0.02 / 0.06 = 1/3 ≈ 0.333
        expected_iou = 1.0 / 3.0
        assert abs(iou - expected_iou) < 1e-2
    
    def test_batch_iou_calculation_performance(self):
        """バッチIOU計算パフォーマンステスト（0.1ms per pair）"""
        # 50 x 50 = 2500ペアのテスト
        bb_list1 = [
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(i % 16),
                action_type=ActionType(i % 5),
                coordinates=Coordinates(0.1 + i * 0.01, 0.1 + i * 0.01, 0.05, 0.05),
                confidence=Confidence(0.8)
            )
            for i in range(50)
        ]
        
        bb_list2 = [
            BBEntity(
                frame_id="000002",
                individual_id=IndividualID(i % 16),
                action_type=ActionType(i % 5),
                coordinates=Coordinates(0.15 + i * 0.01, 0.15 + i * 0.01, 0.05, 0.05),
                confidence=Confidence(0.7)
            )
            for i in range(50)
        ]
        
        start_time = time.perf_counter()
        iou_matrix = IOUCalculator.calculate_iou_matrix(bb_list1, bb_list2)
        elapsed = (time.perf_counter() - start_time) * 1000
        
        # 2500ペア * 0.1ms = 250ms以下
        assert elapsed <= 250.0, f"Batch IOU calculation took {elapsed}ms (target: 250.0ms)"
        
        # 結果検証
        assert iou_matrix.shape == (50, 50)
        assert np.all(iou_matrix >= 0.0)
        assert np.all(iou_matrix <= 1.0)
        
        print(f"バッチIOU計算パフォーマンス: {elapsed:.1f}ms for 2500 pairs")
    
    def test_vectorized_iou_calculation_accuracy(self):
        """ベクトル化IOU計算精度テスト"""
        bb_list1 = [
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(0),
                action_type=ActionType.SIT,
                coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
                confidence=Confidence(0.8)
            ),
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(1),
                action_type=ActionType.STAND,
                coordinates=Coordinates(0.3, 0.3, 0.15, 0.15),
                confidence=Confidence(0.9)
            )
        ]
        
        bb_list2 = [
            BBEntity(
                frame_id="000002",
                individual_id=IndividualID(0),
                action_type=ActionType.SIT,
                coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),  # 完全一致
                confidence=Confidence(0.7)
            ),
            BBEntity(
                frame_id="000002",
                individual_id=IndividualID(1),
                action_type=ActionType.MILK,
                coordinates=Coordinates(0.8, 0.8, 0.1, 0.1),  # 重複なし
                confidence=Confidence(0.6)
            )
        ]
        
        # バッチ計算
        iou_matrix = IOUCalculator.calculate_iou_matrix(bb_list1, bb_list2)
        
        # 個別計算と比較
        for i in range(len(bb_list1)):
            for j in range(len(bb_list2)):
                expected_iou = IOUCalculator.calculate_iou(bb_list1[i], bb_list2[j])
                actual_iou = iou_matrix[i, j]
                assert abs(actual_iou - expected_iou) < 1e-6
        
        # 特定値確認
        assert abs(iou_matrix[0, 0] - 1.0) < 1e-6  # 完全一致
        assert abs(iou_matrix[1, 1] - 0.0) < 1e-6  # 重複なし
    
    def test_best_matches_finding(self):
        """最適マッチング検索テスト"""
        source_bbs = [
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(0),
                action_type=ActionType.SIT,
                coordinates=Coordinates(0.3, 0.3, 0.2, 0.2),
                confidence=Confidence(0.8)
            ),
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(1),
                action_type=ActionType.STAND,
                coordinates=Coordinates(0.7, 0.7, 0.15, 0.15),
                confidence=Confidence(0.9)
            )
        ]
        
        target_bbs = [
            BBEntity(
                frame_id="000002",
                individual_id=IndividualID(0),
                action_type=ActionType.SIT,
                coordinates=Coordinates(0.32, 0.32, 0.2, 0.2),  # source[0]と高IOU
                confidence=Confidence(0.7)
            ),
            BBEntity(
                frame_id="000002",
                individual_id=IndividualID(1),
                action_type=ActionType.MILK,
                coordinates=Coordinates(0.72, 0.72, 0.15, 0.15),  # source[1]と高IOU
                confidence=Confidence(0.6)
            ),
            BBEntity(
                frame_id="000002",
                individual_id=IndividualID(2),
                action_type=ActionType.WATER,
                coordinates=Coordinates(0.1, 0.1, 0.1, 0.1),  # マッチなし
                confidence=Confidence(0.5)
            )
        ]
        
        matches = IOUCalculator.find_best_matches(source_bbs, target_bbs, 0.3)
        
        # 2つのマッチが見つかるはず
        assert len(matches) == 2
        
        # マッチング内容確認
        source_ids = [match[0] for match in matches]
        target_ids = [match[1] for match in matches]
        iou_scores = [match[2] for match in matches]
        
        assert source_bbs[0].id in source_ids
        assert source_bbs[1].id in source_ids
        assert target_bbs[0].id in target_ids
        assert target_bbs[1].id in target_ids
        assert all(iou >= 0.3 for iou in iou_scores)
    
    def test_overlap_statistics(self):
        """重複統計計算テスト"""
        bb_list = [
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(0),
                action_type=ActionType.SIT,
                coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
                confidence=Confidence(0.8)
            ),
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(1),
                action_type=ActionType.STAND,
                coordinates=Coordinates(0.55, 0.55, 0.2, 0.2),  # 重複あり
                confidence=Confidence(0.7)
            ),
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(2),
                action_type=ActionType.MILK,
                coordinates=Coordinates(0.2, 0.2, 0.1, 0.1),  # 重複なし
                confidence=Confidence(0.9)
            )
        ]
        
        stats = IOUCalculator.calculate_overlap_statistics(bb_list, 0.1)
        
        # 統計確認
        assert stats["total_pairs"] == 3  # C(3,2) = 3ペア
        assert stats["overlapping_pairs"] >= 0
        assert 0.0 <= stats["overlap_ratio"] <= 1.0
        assert stats["max_iou"] >= 0.0
        assert stats["avg_iou"] >= 0.0
    
    def test_cached_iou_calculation(self):
        """キャッシュ付きIOU計算テスト"""
        coords1 = (0.5, 0.5, 0.2, 0.2)
        coords2 = (0.6, 0.6, 0.2, 0.2)
        
        # 初回計算
        start_time = time.perf_counter()
        iou1 = IOUCalculator.calculate_cached_iou(coords1, coords2)
        first_time = (time.perf_counter() - start_time) * 1000
        
        # キャッシュヒット
        start_time = time.perf_counter()
        iou2 = IOUCalculator.calculate_cached_iou(coords1, coords2)
        cached_time = (time.perf_counter() - start_time) * 1000
        
        # 結果一致確認
        assert abs(iou1 - iou2) < 1e-6
        
        # キャッシュ効果確認（通常はキャッシュが高速）
        print(f"初回計算: {first_time:.3f}ms, キャッシュヒット: {cached_time:.3f}ms")
        
        # キャッシュ情報確認
        cache_info = IOUCalculator.get_cache_info()
        assert cache_info.hits >= 1  # 少なくとも1回ヒット
    
    def test_empty_list_handling(self):
        """空リスト処理テスト"""
        empty_list = []
        bb_list = [
            BBEntity(
                frame_id="000001",
                individual_id=IndividualID(0),
                action_type=ActionType.SIT,
                coordinates=Coordinates(0.5, 0.5, 0.2, 0.2),
                confidence=Confidence(0.8)
            )
        ]
        
        # 空リスト vs 通常リスト
        iou_matrix1 = IOUCalculator.calculate_iou_matrix(empty_list, bb_list)
        assert iou_matrix1.shape == (0, 1)
        
        # 通常リスト vs 空リスト
        iou_matrix2 = IOUCalculator.calculate_iou_matrix(bb_list, empty_list)
        assert iou_matrix2.shape == (1, 0)
        
        # 空リスト vs 空リスト
        iou_matrix3 = IOUCalculator.calculate_iou_matrix(empty_list, empty_list)
        assert iou_matrix3.shape == (0, 0)
        
        # 空リストでのマッチング
        matches = IOUCalculator.find_best_matches(empty_list, bb_list)
        assert matches == []
        
        # 空リストでの統計
        stats = IOUCalculator.calculate_overlap_statistics(empty_list)
        assert stats["total_pairs"] == 0
        assert stats["overlapping_pairs"] == 0
        assert stats["overlap_ratio"] == 0.0
    
    def test_cache_management(self):
        """キャッシュ管理テスト"""
        # キャッシュクリア前の状態確認
        info_before = IOUCalculator.get_cache_info()
        
        # キャッシュクリア
        IOUCalculator.clear_cache()
        
        # キャッシュクリア後の状態確認
        info_after = IOUCalculator.get_cache_info()
        assert info_after.currsize == 0  # キャッシュが空になっている