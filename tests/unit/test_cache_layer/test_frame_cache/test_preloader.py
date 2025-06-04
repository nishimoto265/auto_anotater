"""
Agent6 Cache Layer: 先読み機能テスト

バックグラウンド先読み・90%以上ヒット率確認
"""
import time
import pytest
import asyncio
import threading
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Optional, Callable

# テスト対象（実装予定）
from src.cache_layer.frame_cache.preloader import AsyncPreloader
from src.cache_layer.frame_cache.lru_cache import LRUFrameCache
from src.cache_layer.strategies.prefetch_strategy import PrefetchStrategy


class TestAsyncPreloader:
    """非同期先読み機能テスト"""
    
    @pytest.fixture
    def cache(self):
        """テスト用キャッシュ"""
        return LRUFrameCache(max_size=200, memory_limit=10 * 1024**3)
    
    @pytest.fixture
    def preloader(self, cache):
        """先読みエンジン"""
        return AsyncPreloader(
            cache_instance=cache,
            preload_range=50,  # 前後50フレーム
            max_concurrent=5   # 最大5並行
        )
    
    @pytest.fixture
    def mock_frame_loader(self):
        """フレーム読み込みモック"""
        async def load_frame(frame_id: str):
            await asyncio.sleep(0.01)  # 10ms読み込み時間シミュレーション
            return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        return load_frame
    
    def test_preload_queue_operation(self, preloader):
        """先読みキューイング操作確認"""
        current_frame = "frame_000100"
        
        # 先読み開始（1ms以下でキューイング）
        start_time = time.perf_counter()
        result = preloader.start_preload(current_frame, direction="both")
        end_time = time.perf_counter()
        
        queue_time = (end_time - start_time) * 1000
        
        assert result is True, "Preload queuing failed"
        assert queue_time <= 1.0, f"Preload queuing too slow: {queue_time:.3f}ms"
        
        # キューに正しく追加されたか確認
        assert preloader.get_queue_size() > 0, "Preload queue is empty"
    
    @pytest.mark.asyncio
    async def test_background_preloading_non_blocking(self, preloader, mock_frame_loader):
        """バックグラウンド先読みのノンブロッキング確認"""
        with patch.object(preloader, '_load_frame_async', mock_frame_loader):
            current_frame = "frame_000100"
            
            # 先読み開始
            preloader.start_preload(current_frame, direction="forward")
            
            # メインスレッドの処理（UIシミュレーション）
            main_thread_times = []
            for _ in range(10):
                start_time = time.perf_counter()
                
                # メインスレッド処理（フレーム表示等）
                await asyncio.sleep(0.001)  # 1ms処理時間
                
                end_time = time.perf_counter()
                main_thread_times.append((end_time - start_time) * 1000)
            
            # メインスレッドがブロックされていないことを確認
            avg_main_time = np.mean(main_thread_times)
            assert avg_main_time <= 2.0, f"Main thread blocked: {avg_main_time:.3f}ms"
            
            # 先読み完了待機
            await preloader.wait_completion()
    
    @pytest.mark.asyncio
    async def test_preload_range_accuracy(self, preloader, cache, mock_frame_loader):
        """先読み範囲精度確認"""
        with patch.object(preloader, '_load_frame_async', mock_frame_loader):
            current_frame_id = 100
            preload_range = 25  # 前後25フレーム
            
            preloader.preload_range = preload_range
            
            # 先読み実行
            await preloader.execute_preload(f"frame_{current_frame_id:06d}", "both")
            
            # 先読み結果確認
            loaded_frames = 0
            for i in range(current_frame_id - preload_range, current_frame_id + preload_range + 1):
                frame_id = f"frame_{i:06d}"
                if cache.get(frame_id) is not None:
                    loaded_frames += 1
            
            expected_frames = preload_range * 2 + 1  # 前25 + 現在1 + 後25
            hit_rate = loaded_frames / expected_frames
            
            assert hit_rate >= 0.9, f"Preload range accuracy too low: {hit_rate:.1%}"
    
    def test_concurrent_preload_limit(self, preloader, mock_frame_loader):
        """並行先読み制限確認"""
        max_concurrent = 3
        preloader.max_concurrent = max_concurrent
        
        # 複数先読み要求
        active_tasks = []
        for i in range(10):
            frame_id = f"frame_{i * 100:06d}"
            task = preloader.start_preload(frame_id, direction="forward")
            if task:
                active_tasks.append(task)
        
        # 同時実行数確認
        concurrent_count = preloader.get_active_task_count()
        assert concurrent_count <= max_concurrent, (
            f"Too many concurrent tasks: {concurrent_count} > {max_concurrent}"
        )
    
    def test_preload_priority_handling(self, preloader):
        """先読み優先度処理確認"""
        # 低優先度先読み
        preloader.start_preload("frame_000100", direction="forward", priority="low")
        
        # 高優先度先読み（直近フレーム）
        preloader.start_preload("frame_000101", direction="forward", priority="high")
        
        # 高優先度が先に処理されることを確認
        queue_items = preloader.get_queue_items()
        assert len(queue_items) >= 2, "Queue items not added"
        
        # 最初の項目が高優先度であることを確認
        first_item = queue_items[0]
        assert first_item['priority'] == 'high', "High priority item not first"


class TestPrefetchStrategy:
    """先読み戦略テスト"""
    
    @pytest.fixture
    def strategy(self):
        """先読み戦略"""
        return PrefetchStrategy(
            history_size=100,
            prediction_window=50
        )
    
    def test_access_pattern_learning(self, strategy):
        """アクセスパターン学習確認"""
        # 順次アクセスパターン
        sequential_pattern = [f"frame_{i:06d}" for i in range(100, 200)]
        for frame_id in sequential_pattern:
            strategy.record_access(frame_id)
        
        # パターン予測
        current_frame = "frame_000150"
        predicted_frames = strategy.predict_next_frames(current_frame, count=10)
        
        # 順次パターンが予測されているか確認
        expected_next = [f"frame_{i:06d}" for i in range(151, 161)]
        
        # 50%以上の予測精度を期待
        correct_predictions = sum(1 for pred in predicted_frames if pred in expected_next)
        accuracy = correct_predictions / len(predicted_frames)
        
        assert accuracy >= 0.5, f"Pattern prediction accuracy too low: {accuracy:.1%}"
    
    def test_random_access_pattern_handling(self, strategy):
        """ランダムアクセスパターン処理確認"""
        # ランダムアクセスパターン
        np.random.seed(42)
        random_indices = np.random.randint(0, 1000, 50)
        random_pattern = [f"frame_{i:06d}" for i in random_indices]
        
        for frame_id in random_pattern:
            strategy.record_access(frame_id)
        
        # ランダムパターンでの予測
        current_frame = random_pattern[-1]
        predicted_frames = strategy.predict_next_frames(current_frame, count=10)
        
        # ランダムでも何らかの予測が返されることを確認
        assert len(predicted_frames) == 10, "Prediction count mismatch"
        assert all(isinstance(frame, str) for frame in predicted_frames), "Invalid frame IDs"
    
    def test_hot_spot_detection(self, strategy):
        """ホットスポット検出確認"""
        # 特定フレームに集中アクセス
        hot_frames = ["frame_000100", "frame_000150", "frame_000200"]
        
        for _ in range(10):
            for frame_id in hot_frames:
                strategy.record_access(frame_id)
        
        # 他のフレームにも少しアクセス
        for i in range(300, 320):
            strategy.record_access(f"frame_{i:06d}")
        
        # ホットスポット検出
        hot_spots = strategy.get_hot_spots(threshold=5)
        
        assert len(hot_spots) >= 3, "Hot spots not detected"
        for hot_frame in hot_frames:
            assert hot_frame in hot_spots, f"Hot frame {hot_frame} not detected"
    
    def test_adaptive_range_adjustment(self, strategy):
        """適応的範囲調整確認"""
        # 短距離移動パターン
        for i in range(100, 110):
            strategy.record_access(f"frame_{i:06d}")
        
        short_range = strategy.calculate_optimal_range()
        
        # 長距離移動パターン
        long_pattern = [100, 150, 200, 250, 300]
        for i in long_pattern:
            strategy.record_access(f"frame_{i:06d}")
        
        long_range = strategy.calculate_optimal_range()
        
        # 長距離パターンの方が範囲が広いことを確認
        assert long_range > short_range, "Range not adapted to access pattern"


class TestPreloadHitRateOptimization:
    """先読みヒット率最適化テスト"""
    
    @pytest.fixture
    def optimized_system(self):
        """最適化された先読みシステム"""
        cache = LRUFrameCache(max_size=200, memory_limit=10 * 1024**3)
        strategy = PrefetchStrategy()
        preloader = AsyncPreloader(cache_instance=cache, preload_range=50, max_concurrent=3)
        return cache, preloader, strategy
    
    @pytest.mark.asyncio
    async def test_90_percent_hit_rate_sequential(self, optimized_system):
        """順次アクセスでの90%以上ヒット率確認"""
        cache, preloader, strategy = optimized_system
        
        with patch.object(preloader, '_load_frame_async') as mock_loader:
            mock_loader.return_value = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            
            # 初期フレーム読み込み
            for i in range(50, 60):
                frame_id = f"frame_{i:06d}"
                frame_data = await mock_loader(frame_id)
                cache.put(frame_id, frame_data)
            
            # 順次アクセステスト
            hits = 0
            misses = 0
            
            for i in range(60, 160):  # 100フレーム順次アクセス
                frame_id = f"frame_{i:06d}"
                
                # 先読み実行
                await preloader.execute_preload(frame_id, "forward")
                
                # フレームアクセス
                frame_data = cache.get(frame_id)
                if frame_data is not None:
                    hits += 1
                else:
                    # キャッシュミス時の読み込み
                    frame_data = await mock_loader(frame_id)
                    cache.put(frame_id, frame_data)
                    misses += 1
            
            hit_rate = hits / (hits + misses)
            assert hit_rate >= 0.9, f"Sequential hit rate too low: {hit_rate:.1%}"
    
    @pytest.mark.asyncio
    async def test_adaptive_preload_adjustment(self, optimized_system):
        """適応的先読み調整確認"""
        cache, preloader, strategy = optimized_system
        
        # 初期設定
        initial_range = preloader.preload_range
        
        # 低ヒット率シミュレーション
        strategy.record_hit_rate(0.7)  # 70%
        strategy.record_hit_rate(0.75)  # 75%
        
        # 範囲調整実行
        preloader.adjust_preload_range()
        adjusted_range = preloader.preload_range
        
        # 範囲が拡大されることを確認
        assert adjusted_range > initial_range, "Preload range not increased for low hit rate"
        
        # 高ヒット率シミュレーション
        for _ in range(10):
            strategy.record_hit_rate(0.98)  # 98%
        
        # 範囲再調整
        preloader.adjust_preload_range()
        optimized_range = preloader.preload_range
        
        # 効率的な範囲に調整されることを確認
        assert optimized_range <= adjusted_range, "Range not optimized for high hit rate"
    
    def test_preload_cancellation(self, optimized_system):
        """不要先読みキャンセル確認"""
        cache, preloader, strategy = optimized_system
        
        # 先読み開始
        task1 = preloader.start_preload("frame_000100", "forward")
        task2 = preloader.start_preload("frame_000200", "forward")  # 離れた位置
        
        # 方向転換（task2が不要になる）
        preloader.start_preload("frame_000101", "forward")
        
        # 不要タスクがキャンセルされることを確認
        time.sleep(0.1)  # 少し待機
        
        active_tasks = preloader.get_active_tasks()
        frame_200_active = any("frame_000200" in str(task) for task in active_tasks)
        
        assert not frame_200_active, "Unnecessary preload task not cancelled"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])