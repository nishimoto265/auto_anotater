"""
AnnotationService Unit Tests
Agent2 Application Layer - BB作成・削除・更新統合処理テスト

性能目標:
- BB作成処理: 10ms以下
- BB削除処理: 5ms以下
- BB更新処理: 8ms以下
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.application.services.annotation_service import AnnotationService
from src.application.services.annotation_service import (
    BBCreationRequest,
    BBUpdateRequest,
    BBDeletionRequest,
    AnnotationError,
    ValidationError
)


@pytest.fixture
def mock_domain_service():
    """Domain層サービスモック"""
    mock = Mock()
    mock.create_bb_entity.return_value = Mock(id="bb_001", x=0.5, y=0.3, w=0.1, h=0.1)
    mock.validate_bb.return_value = True
    mock.check_bb_overlap.return_value = False
    mock.delete_bb_entity.return_value = True
    mock.update_bb_entity.return_value = Mock(id="bb_001")
    return mock


@pytest.fixture
def mock_data_bus():
    """Data Busモック"""
    mock = Mock()
    mock.publish.return_value = True
    return mock


@pytest.fixture
def annotation_service(mock_domain_service, mock_data_bus):
    """AnnotationService テストフィクスチャ"""
    return AnnotationService(mock_domain_service, mock_data_bus)


class TestAnnotationServicePerformance:
    """AnnotationService 性能テスト"""
    
    def measure_execution_time(self, func, *args, **kwargs):
        """実行時間測定"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        execution_time = (end - start) * 1000  # ms
        return result, execution_time
    
    def test_create_bb_10ms_performance(self, annotation_service):
        """BB作成処理10ms以下確認"""
        request = BBCreationRequest(
            x=0.5, y=0.3, w=0.1, h=0.1,
            individual_id=0, action_id=2, confidence=0.95
        )
        
        # 1000回実行で全て10ms以下確認
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                annotation_service.create_bounding_box, request
            )
            assert exec_time <= 10.0, f"Iteration {i}: {exec_time}ms > 10ms"
            assert result is not None
    
    def test_delete_bb_5ms_performance(self, annotation_service):
        """BB削除処理5ms以下確認"""
        request = BBDeletionRequest(bb_id="bb_001", frame_id="000001")
        
        # 1000回実行で全て5ms以下確認
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                annotation_service.delete_bounding_box, request
            )
            assert exec_time <= 5.0, f"Iteration {i}: {exec_time}ms > 5ms"
            assert result is True
    
    def test_update_bb_8ms_performance(self, annotation_service):
        """BB更新処理8ms以下確認"""
        request = BBUpdateRequest(
            bb_id="bb_001", 
            properties={"x": 0.6, "confidence": 0.9}
        )
        
        # 1000回実行で全て8ms以下確認
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                annotation_service.update_bounding_box, request
            )
            assert exec_time <= 8.0, f"Iteration {i}: {exec_time}ms > 8ms"
            assert result is not None
    
    def test_batch_create_efficiency(self, annotation_service):
        """一括BB作成効率性確認"""
        requests = [
            BBCreationRequest(x=0.1*i, y=0.1*i, w=0.1, h=0.1, 
                            individual_id=i%16, action_id=i%5)
            for i in range(100)
        ]
        
        # バッチ処理が個別処理より効率的であることを確認
        result, exec_time = self.measure_execution_time(
            annotation_service.batch_create_bounding_boxes, requests
        )
        
        # 100個で100ms以下（平均1ms/個）
        assert exec_time <= 100.0, f"Batch creation too slow: {exec_time}ms"
        assert len(result) == 100


class TestAnnotationServiceFunctionality:
    """AnnotationService 機能テスト"""
    
    def test_bb_creation_workflow(self, annotation_service, mock_domain_service, mock_data_bus):
        """BB作成ワークフロー完全性確認"""
        request = BBCreationRequest(
            x=0.5, y=0.3, w=0.1, h=0.1,
            individual_id=1, action_id=2, confidence=0.95
        )
        
        result = annotation_service.create_bounding_box(request)
        
        # ワークフロー確認
        mock_domain_service.validate_bb.assert_called_once()
        mock_domain_service.create_bb_entity.assert_called_once()
        mock_domain_service.check_bb_overlap.assert_called_once()
        mock_data_bus.publish.assert_called_once()
        
        assert result is not None
        assert result.id == "bb_001"
    
    def test_bb_validation_integration(self, annotation_service, mock_domain_service):
        """BB検証統合確認"""
        # 無効なBBリクエスト
        invalid_request = BBCreationRequest(
            x=1.5, y=0.3, w=0.1, h=0.1,  # x座標が範囲外
            individual_id=20, action_id=2  # IDが範囲外
        )
        
        mock_domain_service.validate_bb.return_value = False
        
        with pytest.raises(ValidationError):
            annotation_service.create_bounding_box(invalid_request)
    
    def test_domain_service_integration(self, annotation_service, mock_domain_service):
        """Domain層サービス連携確認"""
        request = BBCreationRequest(x=0.5, y=0.3, w=0.1, h=0.1, individual_id=1, action_id=2)
        
        annotation_service.create_bounding_box(request)
        
        # Domain層連携確認
        assert mock_domain_service.validate_bb.called
        assert mock_domain_service.create_bb_entity.called
        assert mock_domain_service.check_bb_overlap.called
    
    def test_data_bus_event_publishing(self, annotation_service, mock_data_bus):
        """Data Busイベント発行確認"""
        request = BBCreationRequest(x=0.5, y=0.3, w=0.1, h=0.1, individual_id=1, action_id=2)
        
        annotation_service.create_bounding_box(request)
        
        # イベント発行確認
        mock_data_bus.publish.assert_called_once()
        call_args = mock_data_bus.publish.call_args
        assert call_args[0][0] == "bb_created"  # イベント名
        assert "bb" in call_args[1]  # BB データ
        assert "frame_id" in call_args[1]  # フレームID
    
    def test_bb_deletion_workflow(self, annotation_service, mock_domain_service, mock_data_bus):
        """BB削除ワークフロー確認"""
        request = BBDeletionRequest(bb_id="bb_001", frame_id="000001")
        
        result = annotation_service.delete_bounding_box(request)
        
        # 削除ワークフロー確認
        mock_domain_service.delete_bb_entity.assert_called_once_with("bb_001")
        mock_data_bus.publish.assert_called_once()
        
        assert result is True
    
    def test_bb_update_workflow(self, annotation_service, mock_domain_service, mock_data_bus):
        """BB更新ワークフロー確認"""
        request = BBUpdateRequest(
            bb_id="bb_001",
            properties={"confidence": 0.9, "action_id": 3}
        )
        
        result = annotation_service.update_bounding_box(request)
        
        # 更新ワークフロー確認
        mock_domain_service.update_bb_entity.assert_called_once()
        mock_data_bus.publish.assert_called_once()
        
        assert result is not None
    
    def test_error_handling_robustness(self, annotation_service, mock_domain_service):
        """エラーハンドリング堅牢性確認"""
        # Domain層でエラー発生
        mock_domain_service.create_bb_entity.side_effect = Exception("Domain error")
        
        request = BBCreationRequest(x=0.5, y=0.3, w=0.1, h=0.1, individual_id=1, action_id=2)
        
        with pytest.raises(AnnotationError):
            annotation_service.create_bounding_box(request)
    
    def test_concurrent_operations_safety(self, annotation_service):
        """並行操作安全性確認"""
        import threading
        
        results = []
        errors = []
        
        def create_bb(thread_id):
            try:
                request = BBCreationRequest(
                    x=0.1*thread_id, y=0.1*thread_id, w=0.1, h=0.1,
                    individual_id=thread_id%16, action_id=thread_id%5
                )
                result = annotation_service.create_bounding_box(request)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 10並列でBB作成
        threads = [threading.Thread(target=create_bb, args=(i,)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # 並行処理結果確認
        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert len(results) == 10


class TestAnnotationServiceIntegration:
    """AnnotationService 統合テスト"""
    
    def test_complete_annotation_workflow(self, annotation_service):
        """完全アノテーションワークフロー確認"""
        # 作成
        create_request = BBCreationRequest(
            x=0.5, y=0.3, w=0.1, h=0.1, individual_id=1, action_id=2
        )
        bb = annotation_service.create_bounding_box(create_request)
        
        # 更新
        update_request = BBUpdateRequest(
            bb_id=bb.id, properties={"confidence": 0.8}
        )
        updated_bb = annotation_service.update_bounding_box(update_request)
        
        # 削除
        delete_request = BBDeletionRequest(bb_id=bb.id, frame_id="000001")
        deleted = annotation_service.delete_bounding_box(delete_request)
        
        assert bb is not None
        assert updated_bb is not None
        assert deleted is True
    
    def test_memory_efficiency(self, annotation_service):
        """メモリ使用効率確認"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 大量BB作成・削除
        for batch in range(10):
            requests = [
                BBCreationRequest(x=0.1*i, y=0.1*i, w=0.05, h=0.05, 
                                individual_id=i%16, action_id=i%5)
                for i in range(100)
            ]
            bbs = annotation_service.batch_create_bounding_boxes(requests)
            
            # 削除
            for bb in bbs:
                delete_request = BBDeletionRequest(bb_id=bb.id, frame_id="000001")
                annotation_service.delete_bounding_box(delete_request)
            
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # メモリ増加量が適切な範囲内であることを確認
        assert memory_increase < 50, f"Memory leak detected: {memory_increase}MB increase"