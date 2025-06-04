"""
BBValidator Unit Tests
Agent2 Application Layer - BB検証テスト

性能要件:
- 基本検証: 1ms以下
- 複合検証: 3ms以下
- バッチ検証: 効率的処理
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.application.validators.bb_validator import BBValidator
from src.application.validators.bb_validator import (
    ValidationResult,
    ValidationError,
    CoordinateValidationError,
    IDValidationError
)


@pytest.fixture
def bb_validator():
    """BBValidator テストフィクスチャ"""
    return BBValidator()


@pytest.fixture
def sample_bb_data():
    """サンプルBBデータ"""
    return {
        "x": 0.5,
        "y": 0.3,
        "w": 0.1,
        "h": 0.1,
        "individual_id": 5,
        "action_id": 2,
        "confidence": 0.9
    }


@pytest.fixture
def sample_bb_list():
    """サンプルBBリスト"""
    return [
        {"x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1, "individual_id": 0, "action_id": 0},
        {"x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1, "individual_id": 1, "action_id": 1},
        {"x": 0.8, "y": 0.7, "w": 0.1, "h": 0.1, "individual_id": 2, "action_id": 2}
    ]


class TestBBValidatorPerformance:
    """BBValidator 性能テスト"""
    
    def measure_execution_time(self, func, *args, **kwargs):
        """実行時間測定"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        execution_time = (end - start) * 1000  # ms
        return result, execution_time
    
    def test_basic_validation_1ms(self, bb_validator, sample_bb_data):
        """基本検証1ms以下確認"""
        # 1000回実行で全て1ms以下確認
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                bb_validator.validate_bb_creation, sample_bb_data
            )
            assert exec_time <= 1.0, f"Iteration {i}: {exec_time}ms > 1ms"
            assert result.is_valid is True
    
    def test_composite_validation_3ms(self, bb_validator, sample_bb_data, sample_bb_list):
        """複合検証3ms以下確認"""
        # 重複チェック込みの複合検証
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                bb_validator.validate_bb_overlap, sample_bb_data, sample_bb_list
            )
            assert exec_time <= 3.0, f"Iteration {i}: {exec_time}ms > 3ms"
            assert isinstance(result, ValidationResult)
    
    def test_batch_validation_efficiency(self, bb_validator):
        """バッチ検証効率性確認"""
        # 100個BBのバッチ検証
        large_bb_list = [
            {
                "x": 0.1*(i%10), "y": 0.1*(i//10), "w": 0.05, "h": 0.05,
                "individual_id": i%16, "action_id": i%5, "confidence": 0.8
            }
            for i in range(100)
        ]
        
        result, exec_time = self.measure_execution_time(
            bb_validator.validate_batch_bbs, large_bb_list
        )
        
        # 100個で100ms以下（平均1ms/個）
        assert exec_time <= 100.0, f"Batch validation too slow: {exec_time}ms"
        assert len(result) == 100
        assert all(isinstance(r, ValidationResult) for r in result)
    
    def test_coordinate_validation_speed(self, bb_validator):
        """座標検証速度確認"""
        test_coordinates = [
            (0.0, 0.0, 0.1, 0.1),  # 有効
            (0.9, 0.9, 0.1, 0.1),  # 境界有効
            (1.0, 1.0, 0.1, 0.1),  # 境界無効
            (-0.1, 0.5, 0.1, 0.1),  # 無効（負の値）
            (0.5, 0.5, 1.5, 0.1),  # 無効（範囲外）
        ]
        
        for coords in test_coordinates:
            for i in range(200):  # 各パターン200回
                result, exec_time = self.measure_execution_time(
                    bb_validator.validate_coordinate_range, *coords
                )
                assert exec_time <= 1.0, f"Coordinate validation {coords}, iteration {i}: {exec_time}ms > 1ms"
    
    def test_id_validation_speed(self, bb_validator):
        """ID検証速度確認"""
        test_ids = [
            (0, 0), (15, 4), (16, 0), (-1, 2), (5, 5), (10, -1)
        ]
        
        for individual_id, action_id in test_ids:
            for i in range(200):  # 各パターン200回
                result, exec_time = self.measure_execution_time(
                    bb_validator.validate_id_range, individual_id, action_id
                )
                assert exec_time <= 1.0, f"ID validation ({individual_id}, {action_id}), iteration {i}: {exec_time}ms > 1ms"


class TestBBValidatorFunctionality:
    """BBValidator 機能テスト"""
    
    def test_coordinate_range_validation(self, bb_validator):
        """座標範囲検証正確性確認"""
        # 有効な座標
        valid_coords = [
            (0.0, 0.0, 0.1, 0.1),
            (0.5, 0.3, 0.2, 0.4),
            (0.9, 0.9, 0.1, 0.1),
            (0.0, 0.0, 1.0, 1.0),  # 全体
        ]
        
        for x, y, w, h in valid_coords:
            assert bb_validator.validate_coordinate_range(x, y, w, h) is True
        
        # 無効な座標
        invalid_coords = [
            (-0.1, 0.0, 0.1, 0.1),  # 負のx
            (0.0, -0.1, 0.1, 0.1),  # 負のy
            (0.0, 0.0, 0.0, 0.1),   # wが0
            (0.0, 0.0, 0.1, 0.0),   # hが0
            (0.0, 0.0, -0.1, 0.1),  # 負のw
            (0.0, 0.0, 0.1, -0.1),  # 負のh
            (1.1, 0.0, 0.1, 0.1),   # xが範囲外
            (0.0, 1.1, 0.1, 0.1),   # yが範囲外
            (0.0, 0.0, 1.1, 0.1),   # wが範囲外
            (0.0, 0.0, 0.1, 1.1),   # hが範囲外
            (0.9, 0.0, 0.2, 0.1),   # x+wが1.0超過
            (0.0, 0.9, 0.1, 0.2),   # y+hが1.0超過
        ]
        
        for x, y, w, h in invalid_coords:
            assert bb_validator.validate_coordinate_range(x, y, w, h) is False
    
    def test_id_range_validation(self, bb_validator):
        """ID範囲検証正確性確認"""
        # 有効なID
        valid_ids = [
            (0, 0), (15, 4), (5, 2), (0, 4), (15, 0)
        ]
        
        for individual_id, action_id in valid_ids:
            assert bb_validator.validate_id_range(individual_id, action_id) is True
        
        # 無効なID
        invalid_ids = [
            (-1, 0), (16, 0), (0, -1), (0, 5), 
            (-1, -1), (16, 5), (20, 10), (100, 100)
        ]
        
        for individual_id, action_id in invalid_ids:
            assert bb_validator.validate_id_range(individual_id, action_id) is False
    
    def test_bb_creation_validation(self, bb_validator):
        """BB作成検証確認"""
        # 有効なBBデータ
        valid_bb = {
            "x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1,
            "individual_id": 5, "action_id": 2, "confidence": 0.9
        }
        
        result = bb_validator.validate_bb_creation(valid_bb)
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # 無効なBBデータ
        invalid_bb = {
            "x": 1.5, "y": 0.3, "w": 0.1, "h": 0.1,  # x座標無効
            "individual_id": 20, "action_id": 2, "confidence": 0.9  # individual_id無効
        }
        
        result = bb_validator.validate_bb_creation(invalid_bb)
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_overlap_detection_accuracy(self, bb_validator):
        """重複検知精度確認"""
        # 重複するBB
        overlapping_bb = {"x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1}
        existing_bbs = [
            {"x": 0.15, "y": 0.15, "w": 0.1, "h": 0.1},  # 重複
            {"x": 0.5, "y": 0.5, "w": 0.1, "h": 0.1}     # 重複なし
        ]
        
        result = bb_validator.validate_bb_overlap(overlapping_bb, existing_bbs)
        assert result.is_valid is False  # 重複検知
        
        # 重複しないBB
        non_overlapping_bb = {"x": 0.8, "y": 0.8, "w": 0.1, "h": 0.1}
        
        result = bb_validator.validate_bb_overlap(non_overlapping_bb, existing_bbs)
        assert result.is_valid is True  # 重複なし
    
    def test_confidence_validation(self, bb_validator):
        """信頼度検証確認"""
        # 有効な信頼度
        valid_confidences = [0.0, 0.5, 1.0, 0.123, 0.999]
        for confidence in valid_confidences:
            bb_data = {"x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1, 
                      "individual_id": 0, "action_id": 0, "confidence": confidence}
            result = bb_validator.validate_bb_creation(bb_data)
            assert result.is_valid is True
        
        # 無効な信頼度
        invalid_confidences = [-0.1, 1.1, -1.0, 2.0]
        for confidence in invalid_confidences:
            bb_data = {"x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1, 
                      "individual_id": 0, "action_id": 0, "confidence": confidence}
            result = bb_validator.validate_bb_creation(bb_data)
            assert result.is_valid is False
    
    def test_required_fields_validation(self, bb_validator):
        """必須フィールド検証確認"""
        # 完全なBBデータ
        complete_bb = {
            "x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1,
            "individual_id": 0, "action_id": 0
        }
        result = bb_validator.validate_bb_creation(complete_bb)
        assert result.is_valid is True
        
        # 必須フィールド不足
        incomplete_bbs = [
            {"y": 0.3, "w": 0.1, "h": 0.1, "individual_id": 0, "action_id": 0},  # x不足
            {"x": 0.5, "w": 0.1, "h": 0.1, "individual_id": 0, "action_id": 0},  # y不足
            {"x": 0.5, "y": 0.3, "h": 0.1, "individual_id": 0, "action_id": 0},  # w不足
            {"x": 0.5, "y": 0.3, "w": 0.1, "individual_id": 0, "action_id": 0},  # h不足
            {"x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1, "action_id": 0},           # individual_id不足
            {"x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1, "individual_id": 0},       # action_id不足
        ]
        
        for incomplete_bb in incomplete_bbs:
            result = bb_validator.validate_bb_creation(incomplete_bb)
            assert result.is_valid is False


class TestBBValidatorIntegration:
    """BBValidator 統合テスト"""
    
    def test_complete_validation_workflow(self, bb_validator, sample_bb_list):
        """完全検証ワークフロー確認"""
        new_bb = {"x": 0.2, "y": 0.2, "w": 0.1, "h": 0.1, "individual_id": 3, "action_id": 1}
        
        # 基本検証
        basic_result = bb_validator.validate_bb_creation(new_bb)
        assert basic_result.is_valid is True
        
        # 重複検証
        overlap_result = bb_validator.validate_bb_overlap(new_bb, sample_bb_list)
        assert overlap_result.is_valid is True  # 重複なし
        
        # 複合検証結果
        assert basic_result.is_valid and overlap_result.is_valid
    
    def test_error_accumulation(self, bb_validator):
        """エラー蓄積確認"""
        # 複数エラーを持つBB
        multi_error_bb = {
            "x": 1.5,        # 座標エラー
            "y": -0.1,       # 座標エラー
            "w": 0.1, 
            "h": 0.1,
            "individual_id": 20,  # IDエラー
            "action_id": -1,      # IDエラー
            "confidence": 1.5     # 信頼度エラー
        }
        
        result = bb_validator.validate_bb_creation(multi_error_bb)
        assert result.is_valid is False
        assert len(result.errors) >= 4  # 複数エラー蓄積
    
    def test_edge_case_handling(self, bb_validator):
        """エッジケース処理確認"""
        # 境界値テスト
        edge_cases = [
            # 境界有効値
            {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0, "individual_id": 0, "action_id": 0},
            {"x": 0.9, "y": 0.9, "w": 0.1, "h": 0.1, "individual_id": 15, "action_id": 4},
            
            # 境界無効値
            {"x": 1.0, "y": 0.0, "w": 0.1, "h": 0.1, "individual_id": 0, "action_id": 0},
            {"x": 0.0, "y": 1.0, "w": 0.1, "h": 0.1, "individual_id": 0, "action_id": 0},
        ]
        
        results = []
        for bb in edge_cases:
            result = bb_validator.validate_bb_creation(bb)
            results.append(result.is_valid)
        
        # 最初の2つは有効、後の2つは無効
        assert results == [True, True, False, False]
    
    def test_memory_efficiency(self, bb_validator):
        """メモリ使用効率確認"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 大量検証処理
        for batch in range(10):
            large_bb_list = [
                {
                    "x": 0.1*(i%10), "y": 0.1*(i//10), "w": 0.05, "h": 0.05,
                    "individual_id": i%16, "action_id": i%5, "confidence": 0.8
                }
                for i in range(100)
            ]
            
            # バッチ検証
            results = bb_validator.validate_batch_bbs(large_bb_list)
            
            # 重複検証
            for bb in large_bb_list[:10]:  # 部分的に重複検証
                bb_validator.validate_bb_overlap(bb, large_bb_list)
            
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # メモリ増加量が適切な範囲内であることを確認
        assert memory_increase < 10, f"Memory leak detected: {memory_increase}MB increase"
    
    def test_concurrent_validation_safety(self, bb_validator, sample_bb_list):
        """並行検証安全性確認"""
        import threading
        
        results = []
        errors = []
        
        def validate_bb(thread_id):
            try:
                bb_data = {
                    "x": 0.1*thread_id, "y": 0.1*thread_id, "w": 0.05, "h": 0.05,
                    "individual_id": thread_id%16, "action_id": thread_id%5
                }
                result = bb_validator.validate_bb_creation(bb_data)
                overlap_result = bb_validator.validate_bb_overlap(bb_data, sample_bb_list)
                results.append((result, overlap_result))
            except Exception as e:
                errors.append(e)
        
        # 10並列で検証
        threads = [threading.Thread(target=validate_bb, args=(i,)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # 並行処理結果確認
        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert len(results) == 10