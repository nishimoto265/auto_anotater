"""
FrameController Unit Tests
Agent2 Application Layer - フレーム制御テスト

性能要件:
- フレーム切り替え制御: 5ms以下（Cache連携部分除く）
- フレーム検証: 1ms以下
- 自動保存制御: 非同期実行
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from src.application.controllers.frame_controller import FrameController
from src.application.controllers.frame_controller import (
    FrameSwitchRequest,
    FrameSwitchResult,
    FrameValidationError,
    FrameControllerError
)


@pytest.fixture
def mock_cache_service():
    """Cache層サービスモック"""
    mock = Mock()
    mock.get_frame.return_value = {"frame_id": "000001", "data": b"fake_frame_data"}
    mock.preload_frames.return_value = True
    return mock


@pytest.fixture
def mock_persistence_service():
    """Persistence層サービスモック"""
    mock = Mock()
    mock.auto_save_async.return_value = True
    return mock


@pytest.fixture
def mock_data_bus():
    """Data Busモック"""
    mock = Mock()
    mock.publish.return_value = True
    return mock


@pytest.fixture
def frame_controller(mock_cache_service, mock_persistence_service, mock_data_bus):
    """FrameController テストフィクスチャ"""
    return FrameController(mock_cache_service, mock_persistence_service, mock_data_bus)


class TestFrameControllerPerformance:
    """FrameController 性能テスト"""
    
    def measure_execution_time(self, func, *args, **kwargs):
        """実行時間測定"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        execution_time = (end - start) * 1000  # ms
        return result, execution_time
    
    def test_frame_switch_control_5ms(self, frame_controller):
        """フレーム切り替え制御5ms以下確認"""
        request = FrameSwitchRequest(
            current_frame_id="000001",
            target_frame_id="000002",
            auto_save=True
        )
        
        # 1000回実行で全て5ms以下確認
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                frame_controller.switch_to_frame, request
            )
            assert exec_time <= 5.0, f"Iteration {i}: {exec_time}ms > 5ms"
            assert result.success is True
    
    def test_frame_validation_1ms(self, frame_controller):
        """フレーム検証1ms以下確認"""
        # 各種フレームIDでの検証テスト
        test_frame_ids = [
            "000001", "000123", "999999", "000000",
            "invalid", "", "123456", "abc123"
        ]
        
        for frame_id in test_frame_ids:
            for i in range(100):  # 各パターン100回
                result, exec_time = self.measure_execution_time(
                    frame_controller.validate_frame_id, frame_id
                )
                assert exec_time <= 1.0, f"Frame {frame_id}, iteration {i}: {exec_time}ms > 1ms"
    
    def test_navigation_operations_1ms(self, frame_controller):
        """ナビゲーション操作1ms以下確認"""
        current_frame = "000123"
        
        # 次フレーム取得
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                frame_controller.get_next_frame_id, current_frame
            )
            assert exec_time <= 1.0, f"Next frame iteration {i}: {exec_time}ms > 1ms"
            assert result == "000124"
        
        # 前フレーム取得
        for i in range(1000):
            result, exec_time = self.measure_execution_time(
                frame_controller.get_previous_frame_id, current_frame
            )
            assert exec_time <= 1.0, f"Previous frame iteration {i}: {exec_time}ms > 1ms"
            assert result == "000122"
    
    def test_auto_save_non_blocking(self, frame_controller, mock_persistence_service):
        """自動保存非同期実行確認"""
        request = FrameSwitchRequest(
            current_frame_id="000001",
            target_frame_id="000002",
            auto_save=True
        )
        
        # 自動保存が同期的に5ms以内に完了することを確認
        result, exec_time = self.measure_execution_time(
            frame_controller.switch_to_frame, request
        )
        
        assert exec_time <= 5.0, f"Auto-save blocking: {exec_time}ms > 5ms"
        assert result.success is True
        
        # 自動保存が呼び出されていることを確認
        mock_persistence_service.auto_save_async.assert_called()


class TestFrameControllerFunctionality:
    """FrameController 機能テスト"""
    
    def test_frame_switch_workflow(self, frame_controller, mock_cache_service, 
                                 mock_persistence_service, mock_data_bus):
        """フレーム切り替えワークフロー確認"""
        request = FrameSwitchRequest(
            current_frame_id="000001",
            target_frame_id="000002",
            auto_save=True
        )
        
        result = frame_controller.switch_to_frame(request)
        
        # ワークフロー確認
        assert result.success is True
        assert result.current_frame_id == "000001"
        assert result.target_frame_id == "000002"
        
        # Cache層連携確認
        mock_cache_service.get_frame.assert_called_with("000002")
        
        # 自動保存確認
        mock_persistence_service.auto_save_async.assert_called()
        
        # イベント発行確認
        mock_data_bus.publish.assert_called()
    
    def test_frame_validation_accuracy(self, frame_controller):
        """フレーム検証正確性確認"""
        # 有効なフレームID
        valid_frames = ["000000", "000001", "123456", "999999"]
        for frame_id in valid_frames:
            assert frame_controller.validate_frame_id(frame_id) is True
        
        # 無効なフレームID
        invalid_frames = ["", "abc123", "12345", "1234567", "-00001", "00000a"]
        for frame_id in invalid_frames:
            assert frame_controller.validate_frame_id(frame_id) is False
    
    def test_cache_integration(self, frame_controller, mock_cache_service):
        """Cache層連携確認"""
        request = FrameSwitchRequest(
            current_frame_id="000001",
            target_frame_id="000002"
        )
        
        # Cache層からフレーム取得
        result = frame_controller.switch_to_frame(request)
        
        # Cache層メソッド呼び出し確認
        mock_cache_service.get_frame.assert_called_with("000002")
        assert result.success is True
    
    def test_frame_navigation_accuracy(self, frame_controller):
        """フレームナビゲーション正確性確認"""
        test_cases = [
            ("000000", "000001", None),  # 最初のフレーム（前フレームなし）
            ("000001", "000002", "000000"),
            ("000123", "000124", "000122"),
            ("999999", None, "999998"),  # 最後のフレーム（次フレームなし）
        ]
        
        for current, expected_next, expected_prev in test_cases:
            # 次フレーム確認
            if expected_next:
                assert frame_controller.get_next_frame_id(current) == expected_next
            else:
                assert frame_controller.get_next_frame_id(current) is None
            
            # 前フレーム確認
            if expected_prev:
                assert frame_controller.get_previous_frame_id(current) == expected_prev
            else:
                assert frame_controller.get_previous_frame_id(current) is None
    
    def test_error_handling_robustness(self, frame_controller, mock_cache_service):
        """エラーハンドリング堅牢性確認"""
        # Cache層でエラー発生
        mock_cache_service.get_frame.side_effect = Exception("Cache error")
        
        request = FrameSwitchRequest(
            current_frame_id="000001",
            target_frame_id="000002"
        )
        
        result = frame_controller.switch_to_frame(request)
        
        # エラー時の適切な処理確認
        assert result.success is False
        assert "error" in result.error_message.lower()
    
    def test_concurrent_frame_operations(self, frame_controller):
        """並行フレーム操作安全性確認"""
        import threading
        
        results = []
        errors = []
        
        def switch_frames(thread_id):
            try:
                request = FrameSwitchRequest(
                    current_frame_id=f"{thread_id:06d}",
                    target_frame_id=f"{thread_id+1:06d}"
                )
                result = frame_controller.switch_to_frame(request)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 10並列でフレーム切り替え
        threads = [threading.Thread(target=switch_frames, args=(i,)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # 並行処理結果確認
        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert len(results) == 10


class TestFrameControllerIntegration:
    """FrameController 統合テスト"""
    
    def test_complete_frame_workflow(self, frame_controller):
        """完全フレームワークフロー確認"""
        # 現在フレーム: 000005
        current_frame = "000005"
        
        # 次フレームに移動
        next_frame = frame_controller.get_next_frame_id(current_frame)
        assert next_frame == "000006"
        
        # フレーム切り替え実行
        switch_request = FrameSwitchRequest(
            current_frame_id=current_frame,
            target_frame_id=next_frame,
            auto_save=True
        )
        switch_result = frame_controller.switch_to_frame(switch_request)
        assert switch_result.success is True
        
        # 前フレームに戻る
        prev_frame = frame_controller.get_previous_frame_id(next_frame)
        assert prev_frame == current_frame
        
        # 再度フレーム切り替え
        switch_back_request = FrameSwitchRequest(
            current_frame_id=next_frame,
            target_frame_id=prev_frame,
            auto_save=False
        )
        switch_back_result = frame_controller.switch_to_frame(switch_back_request)
        assert switch_back_result.success is True
    
    def test_frame_boundary_handling(self, frame_controller):
        """フレーム境界処理確認"""
        # 最初のフレーム
        first_frame = "000000"
        prev_of_first = frame_controller.get_previous_frame_id(first_frame)
        assert prev_of_first is None
        
        # 最後のフレーム（仮想的）
        last_frame = "999999"
        next_of_last = frame_controller.get_next_frame_id(last_frame)
        # 実装により異なるが、適切な境界処理があることを確認
        assert next_of_last is None or isinstance(next_of_last, str)
    
    def test_performance_under_load(self, frame_controller):
        """負荷時性能確認"""
        # 連続フレーム切り替え
        start_time = time.perf_counter()
        
        for i in range(100):
            request = FrameSwitchRequest(
                current_frame_id=f"{i:06d}",
                target_frame_id=f"{i+1:06d}",
                auto_save=i % 10 == 0  # 10回に1回自動保存
            )
            result = frame_controller.switch_to_frame(request)
            assert result.success is True
        
        total_time = (time.perf_counter() - start_time) * 1000
        avg_time = total_time / 100
        
        # 平均5ms以下確認
        assert avg_time <= 5.0, f"Average frame switch time {avg_time:.2f}ms > 5ms"
    
    def test_memory_efficiency(self, frame_controller):
        """メモリ使用効率確認"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 大量フレーム操作
        for batch in range(10):
            for i in range(100):
                frame_id = f"{batch*100+i:06d}"
                
                # 検証
                frame_controller.validate_frame_id(frame_id)
                
                # ナビゲーション
                frame_controller.get_next_frame_id(frame_id)
                frame_controller.get_previous_frame_id(frame_id)
                
                # フレーム切り替え
                request = FrameSwitchRequest(
                    current_frame_id=frame_id,
                    target_frame_id=f"{batch*100+i+1:06d}"
                )
                frame_controller.switch_to_frame(request)
            
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # メモリ増加量が適切な範囲内であることを確認
        assert memory_increase < 20, f"Memory leak detected: {memory_increase}MB increase"
    
    def test_error_recovery(self, frame_controller, mock_cache_service):
        """エラー回復機能確認"""
        # 一時的なCache層エラー
        mock_cache_service.get_frame.side_effect = [
            Exception("Temporary error"),  # 最初はエラー
            {"frame_id": "000002", "data": b"recovered_data"}  # 次は成功
        ]
        
        request = FrameSwitchRequest(
            current_frame_id="000001",
            target_frame_id="000002"
        )
        
        # 最初の試行（失敗）
        result1 = frame_controller.switch_to_frame(request)
        assert result1.success is False
        
        # 再試行（成功）
        result2 = frame_controller.switch_to_frame(request)
        assert result2.success is True