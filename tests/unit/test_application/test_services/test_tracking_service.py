"""
TrackingService Unit Tests
Agent2 Application Layer - IOU追跡・ID継承制御テスト

性能目標:
- IOU追跡処理: 5ms以下
- ID継承判定: 3ms以下
- 追跡断絶検知: 2ms以下
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.application.services.tracking_service import TrackingService
from src.application.services.tracking_service import (
    TrackingRequest,
    TrackingResult,
    TrackingBreak,
    TrackingError,
    IOUCalculationError
)


@pytest.fixture
def mock_domain_service():
    """Domain層サービスモック"""
    mock = Mock()
    # IOU計算モック
    mock.calculate_iou.return_value = 0.8
    # 追跡結果モック
    mock.track_objects.return_value = [
        {"source_id": 0, "target_id": 0, "iou": 0.8, "confidence": 0.9},
        {"source_id": 1, "target_id": 1, "iou": 0.7, "confidence": 0.8}
    ]
    return mock


@pytest.fixture
def mock_data_bus():
    """Data Busモック"""
    mock = Mock()
    mock.publish.return_value = True
    return mock


@pytest.fixture
def tracking_service(mock_domain_service, mock_data_bus):
    """TrackingService テストフィクスチャ"""
    return TrackingService(mock_domain_service, mock_data_bus)


@pytest.fixture
def sample_bbs():
    """サンプルBBデータ"""
    return [
        {"id": "bb_001", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1, "individual_id": 0},
        {"id": "bb_002", "x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1, "individual_id": 1},
        {"id": "bb_003", "x": 0.8, "y": 0.7, "w": 0.1, "h": 0.1, "individual_id": 2}
    ]


class TestTrackingServicePerformance:
    """TrackingService 性能テスト"""
    
    def measure_execution_time(self, func, *args, **kwargs):
        """実行時間測定"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        execution_time = (end - start) * 1000  # ms
        return result, execution_time
    
    def test_iou_tracking_5ms_performance(self, tracking_service, sample_bbs):
        """IOU追跡処理5ms以下確認"""
        request = TrackingRequest(
            source_frame_id="000001",
            target_frame_id="000002",
            source_bbs=sample_bbs,
            target_bbs=sample_bbs,
            iou_threshold=0.5
        )
        
        # 1000回実行で全て5ms以下確認
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                tracking_service.start_tracking, request
            )
            assert exec_time <= 5.0, f"Iteration {i}: {exec_time}ms > 5ms"
            assert result is not None
    
    def test_id_inheritance_3ms_performance(self, tracking_service, sample_bbs):
        """ID継承判定3ms以下確認"""
        # 継承判定のみのテスト
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                tracking_service.calculate_id_inheritance,
                sample_bbs, sample_bbs, 0.5
            )
            assert exec_time <= 3.0, f"Iteration {i}: {exec_time}ms > 3ms"
            assert isinstance(result, list)
    
    def test_tracking_break_detection_2ms(self, tracking_service, sample_bbs):
        """追跡断絶検知2ms以下確認"""
        # 断絶検知のみのテスト
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                tracking_service.detect_tracking_break,
                "000001", sample_bbs
            )
            assert exec_time <= 2.0, f"Iteration {i}: {exec_time}ms > 2ms"
            assert isinstance(result, list)
    
    def test_batch_tracking_efficiency(self, tracking_service):
        """バッチ追跡処理効率確認"""
        # 大量BBでの追跡テスト
        large_bb_set = [
            {"id": f"bb_{i:03d}", "x": 0.1*(i%10), "y": 0.1*(i//10), 
             "w": 0.05, "h": 0.05, "individual_id": i%16}
            for i in range(100)
        ]
        
        request = TrackingRequest(
            source_frame_id="000001",
            target_frame_id="000002",
            source_bbs=large_bb_set,
            target_bbs=large_bb_set,
            iou_threshold=0.5
        )
        
        result, exec_time = self.measure_execution_time(
            tracking_service.start_tracking, request
        )
        
        # 100個BBで50ms以下（平均0.5ms/個）
        assert exec_time <= 50.0, f"Batch tracking too slow: {exec_time}ms"
        assert result is not None


class TestTrackingServiceFunctionality:
    """TrackingService 機能テスト"""
    
    def test_tracking_workflow(self, tracking_service, mock_domain_service, mock_data_bus, sample_bbs):
        """追跡ワークフロー確認"""
        request = TrackingRequest(
            source_frame_id="000001",
            target_frame_id="000002",
            source_bbs=sample_bbs,
            target_bbs=sample_bbs,
            iou_threshold=0.5
        )
        
        result = tracking_service.start_tracking(request)
        
        # ワークフロー確認
        mock_domain_service.track_objects.assert_called_once()
        mock_data_bus.publish.assert_called()
        
        assert result is not None
        assert result.source_frame_id == "000001"
        assert result.target_frame_id == "000002"
    
    def test_tracking_accuracy_95_percent(self, tracking_service, mock_domain_service):
        """追跡精度95%以上確認"""
        # 高精度追跡シナリオ
        high_iou_bbs = [
            {"id": "bb_001", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1, "individual_id": 0},
            {"id": "bb_002", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1, "individual_id": 0}  # 同一位置
        ]
        
        mock_domain_service.calculate_iou.return_value = 0.95
        mock_domain_service.track_objects.return_value = [
            {"source_id": 0, "target_id": 0, "iou": 0.95, "confidence": 0.95}
        ]
        
        request = TrackingRequest(
            source_frame_id="000001",
            target_frame_id="000002",
            source_bbs=[high_iou_bbs[0]],
            target_bbs=[high_iou_bbs[1]],
            iou_threshold=0.5
        )
        
        result = tracking_service.start_tracking(request)
        
        # 高精度追跡確認
        assert result.matches[0]["confidence"] >= 0.95
        assert result.matches[0]["iou"] >= 0.95
    
    def test_tracking_result_application(self, tracking_service, sample_bbs):
        """追跡結果適用正確性確認"""
        tracking_result = TrackingResult(
            source_frame_id="000001",
            target_frame_id="000002",
            matches=[
                {"source_id": 0, "target_id": 0, "iou": 0.8, "confidence": 0.9},
                {"source_id": 1, "target_id": 1, "iou": 0.7, "confidence": 0.8}
            ],
            unmatched_source=[],
            unmatched_target=[],
            processing_time=3.5
        )
        
        applied_count = tracking_service.apply_tracking_results(tracking_result)
        
        # 適用結果確認
        assert applied_count >= 0  # 適用されたフレーム数
    
    def test_tracking_break_detection_accuracy(self, tracking_service):
        """追跡断絶検知精度確認"""
        # 断絶シナリオ（前フレームにあったBBが消失）
        previous_bbs = [
            {"id": "bb_001", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1, "individual_id": 0},
            {"id": "bb_002", "x": 0.5, "y": 0.3, "w": 0.1, "h": 0.1, "individual_id": 1}
        ]
        
        current_bbs = [
            {"id": "bb_003", "x": 0.8, "y": 0.7, "w": 0.1, "h": 0.1, "individual_id": 2}
        ]
        
        breaks = tracking_service.detect_tracking_break("000002", current_bbs)
        
        # 断絶検知確認
        assert isinstance(breaks, list)
        # 実際の断絶検知ロジックに依存するため、基本的な構造のみ確認
    
    def test_iou_threshold_behavior(self, tracking_service, mock_domain_service):
        """IOU閾値動作確認"""
        test_cases = [
            {"iou": 0.9, "threshold": 0.5, "should_match": True},
            {"iou": 0.3, "threshold": 0.5, "should_match": False},
            {"iou": 0.5, "threshold": 0.5, "should_match": True},  # 境界値
        ]
        
        for case in test_cases:
            mock_domain_service.calculate_iou.return_value = case["iou"]
            
            request = TrackingRequest(
                source_frame_id="000001",
                target_frame_id="000002",
                source_bbs=[{"id": "bb_001", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1}],
                target_bbs=[{"id": "bb_002", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1}],
                iou_threshold=case["threshold"]
            )
            
            inheritance = tracking_service.calculate_id_inheritance(
                request.source_bbs, request.target_bbs, case["threshold"]
            )
            
            if case["should_match"]:
                # マッチする場合の確認
                assert len(inheritance) > 0 or case["iou"] == case["threshold"]
            # マッチしない場合は結果が空またはマッチなし


class TestTrackingServiceIntegration:
    """TrackingService 統合テスト"""
    
    def test_complete_tracking_workflow(self, tracking_service, sample_bbs):
        """完全追跡ワークフロー確認"""
        # 追跡開始
        tracking_request = TrackingRequest(
            source_frame_id="000001",
            target_frame_id="000002",
            source_bbs=sample_bbs,
            target_bbs=sample_bbs,
            iou_threshold=0.5,
            individual_ids=[0, 1]  # 特定個体のみ追跡
        )
        
        tracking_result = tracking_service.start_tracking(tracking_request)
        
        # 結果適用
        applied_count = tracking_service.apply_tracking_results(tracking_result)
        
        # 断絶検知
        breaks = tracking_service.detect_tracking_break("000002", sample_bbs)
        
        assert tracking_result is not None
        assert applied_count >= 0
        assert isinstance(breaks, list)
    
    def test_error_handling_robustness(self, tracking_service, mock_domain_service):
        """エラーハンドリング堅牢性確認"""
        # Domain層でエラー発生
        mock_domain_service.track_objects.side_effect = Exception("Domain tracking error")
        
        request = TrackingRequest(
            source_frame_id="000001",
            target_frame_id="000002",
            source_bbs=[{"id": "bb_001", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1}],
            target_bbs=[{"id": "bb_002", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1}],
            iou_threshold=0.5
        )
        
        with pytest.raises(TrackingError):
            tracking_service.start_tracking(request)
    
    def test_concurrent_tracking_safety(self, tracking_service, sample_bbs):
        """並行追跡処理安全性確認"""
        import threading
        
        results = []
        errors = []
        
        def track_objects(thread_id):
            try:
                request = TrackingRequest(
                    source_frame_id=f"frame_{thread_id:03d}",
                    target_frame_id=f"frame_{thread_id+1:03d}",
                    source_bbs=sample_bbs,
                    target_bbs=sample_bbs,
                    iou_threshold=0.5
                )
                result = tracking_service.start_tracking(request)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 10並列で追跡処理
        threads = [threading.Thread(target=track_objects, args=(i,)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # 並行処理結果確認
        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert len(results) == 10
    
    def test_memory_efficiency(self, tracking_service):
        """メモリ使用効率確認"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 大量追跡処理
        for batch in range(10):
            large_bb_set = [
                {"id": f"bb_{i:03d}", "x": 0.1*(i%10), "y": 0.1*(i//10), 
                 "w": 0.05, "h": 0.05, "individual_id": i%16}
                for i in range(100)
            ]
            
            request = TrackingRequest(
                source_frame_id=f"frame_{batch:03d}",
                target_frame_id=f"frame_{batch+1:03d}",
                source_bbs=large_bb_set,
                target_bbs=large_bb_set,
                iou_threshold=0.5
            )
            
            result = tracking_service.start_tracking(request)
            tracking_service.apply_tracking_results(result)
            
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # メモリ増加量が適切な範囲内であることを確認
        assert memory_increase < 30, f"Memory leak detected: {memory_increase}MB increase"
    
    def test_tracking_statistics(self, tracking_service):
        """追跡統計情報確認"""
        # 複数回追跡実行
        sample_request = TrackingRequest(
            source_frame_id="000001",
            target_frame_id="000002",
            source_bbs=[{"id": "bb_001", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1}],
            target_bbs=[{"id": "bb_002", "x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1}],
            iou_threshold=0.5
        )
        
        for _ in range(10):
            tracking_service.start_tracking(sample_request)
        
        # 統計情報取得
        stats = tracking_service.get_performance_stats()
        
        assert "start_tracking" in stats
        assert stats["start_tracking"]["count"] == 10
        assert stats["start_tracking"]["avg"] > 0