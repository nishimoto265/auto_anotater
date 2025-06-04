"""
Agent6 Cache Layer: LRUキャッシュ単体テスト

O(1)アクセス時間・5ms以下操作の確認
"""
import time
import pytest
import numpy as np
from typing import Optional, Dict, Any
from unittest.mock import Mock, patch

# テスト対象（実装予定）
from src.cache_layer.frame_cache.lru_cache import LRUFrameCache, CacheNode
from src.cache_layer.frame_cache.memory_monitor import MemoryMonitor


class TestLRUCacheBasics:
    """LRUキャッシュ基本機能テスト"""
    
    @pytest.fixture
    def small_cache(self):
        """小規模テスト用キャッシュ"""
        return LRUFrameCache(max_size=3, memory_limit=1024**3)  # 1GB
    
    @pytest.fixture
    def production_cache(self):
        """本番相当キャッシュ"""
        return LRUFrameCache(max_size=100, memory_limit=20 * 1024**3)  # 20GB
    
    @pytest.fixture
    def sample_frame_data(self):
        """サンプルフレームデータ"""
        return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    def test_basic_put_get_operations(self, small_cache, sample_frame_data):
        """基本的なput/get操作確認"""
        frame_id = "frame_000001"
        
        # put操作
        result = small_cache.put(frame_id, sample_frame_data)
        assert result is True, "Put operation failed"
        
        # get操作
        retrieved_data = small_cache.get(frame_id)
        assert retrieved_data is not None, "Get operation returned None"
        assert np.array_equal(retrieved_data, sample_frame_data), "Data mismatch"
    
    def test_lru_eviction_policy(self, small_cache, sample_frame_data):
        """LRU削除ポリシー確認"""
        # 3個まで追加（制限内）
        small_cache.put("frame_001", sample_frame_data)
        small_cache.put("frame_002", sample_frame_data)
        small_cache.put("frame_003", sample_frame_data)
        
        # 全て存在確認
        assert small_cache.get("frame_001") is not None
        assert small_cache.get("frame_002") is not None
        assert small_cache.get("frame_003") is not None
        
        # frame_001をアクセス（最近使用にする）
        small_cache.get("frame_001")
        
        # 4個目追加（frame_002が最古なので削除されるはず）
        small_cache.put("frame_004", sample_frame_data)
        
        # 削除確認
        assert small_cache.get("frame_002") is None, "LRU item not evicted"
        assert small_cache.get("frame_001") is not None, "Recently used item evicted"
        assert small_cache.get("frame_003") is not None
        assert small_cache.get("frame_004") is not None
    
    def test_update_existing_key(self, small_cache, sample_frame_data):
        """既存キー更新時の動作確認"""
        frame_id = "frame_001"
        new_data = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        
        # 初回追加
        small_cache.put(frame_id, sample_frame_data)
        assert small_cache.size() == 1
        
        # 同じキーで更新
        small_cache.put(frame_id, new_data)
        assert small_cache.size() == 1, "Size increased on update"
        
        # 更新されたデータ確認
        retrieved_data = small_cache.get(frame_id)
        assert np.array_equal(retrieved_data, new_data), "Data not updated"
    
    def test_nonexistent_key_get(self, small_cache):
        """存在しないキーのget操作確認"""
        result = small_cache.get("nonexistent_frame")
        assert result is None, "Nonexistent key returned data"


class TestLRUCachePerformance:
    """LRUキャッシュ性能テスト"""
    
    @pytest.fixture
    def production_cache(self):
        """本番相当キャッシュ"""
        return LRUFrameCache(max_size=100, memory_limit=20 * 1024**3)  # 20GB
    
    @pytest.fixture
    def large_frame_data(self):
        """大容量フレームデータ（4K相当）"""
        return np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
    
    def test_get_operation_5ms_performance(self, production_cache, large_frame_data):
        """get操作5ms以下確認"""
        frame_id = "performance_test_frame"
        production_cache.put(frame_id, large_frame_data)
        
        # 100回連続get操作測定
        get_times = []
        for _ in range(100):
            start_time = time.perf_counter()
            result = production_cache.get(frame_id)
            end_time = time.perf_counter()
            
            get_time = (end_time - start_time) * 1000  # ms変換
            get_times.append(get_time)
            
            assert result is not None, "Get operation failed"
            assert get_time <= 5.0, f"Get operation too slow: {get_time:.2f}ms"
        
        avg_get_time = np.mean(get_times)
        max_get_time = np.max(get_times)
        
        print(f"Get operation stats: avg={avg_get_time:.3f}ms, max={max_get_time:.3f}ms")
        assert avg_get_time <= 2.0, f"Average get time too high: {avg_get_time:.3f}ms"
    
    def test_put_operation_5ms_performance(self, production_cache, large_frame_data):
        """put操作5ms以下確認"""
        put_times = []
        
        # 100回連続put操作測定
        for i in range(100):
            frame_id = f"perf_frame_{i:06d}"
            
            start_time = time.perf_counter()
            result = production_cache.put(frame_id, large_frame_data)
            end_time = time.perf_counter()
            
            put_time = (end_time - start_time) * 1000  # ms変換
            put_times.append(put_time)
            
            assert result is True, f"Put operation failed for {frame_id}"
            assert put_time <= 5.0, f"Put operation too slow: {put_time:.2f}ms"
        
        avg_put_time = np.mean(put_times)
        max_put_time = np.max(put_times)
        
        print(f"Put operation stats: avg={avg_put_time:.3f}ms, max={max_put_time:.3f}ms")
        assert avg_put_time <= 2.0, f"Average put time too high: {avg_put_time:.3f}ms"
    
    def test_mixed_operations_performance(self, production_cache, large_frame_data):
        """混合操作での性能確認"""
        # 初期データ投入
        for i in range(50):
            production_cache.put(f"init_frame_{i:03d}", large_frame_data)
        
        operation_times = []
        
        # 混合操作パターン
        for i in range(200):
            if i % 3 == 0:  # get操作
                frame_id = f"init_frame_{i % 50:03d}"
                start_time = time.perf_counter()
                result = production_cache.get(frame_id)
                end_time = time.perf_counter()
                assert result is not None
            else:  # put操作
                frame_id = f"mixed_frame_{i:06d}"
                start_time = time.perf_counter()
                result = production_cache.put(frame_id, large_frame_data)
                end_time = time.perf_counter()
                assert result is True
            
            operation_time = (end_time - start_time) * 1000
            operation_times.append(operation_time)
            assert operation_time <= 5.0, f"Mixed operation too slow: {operation_time:.2f}ms"
        
        avg_operation_time = np.mean(operation_times)
        assert avg_operation_time <= 3.0, f"Average mixed operation time too high: {avg_operation_time:.3f}ms"


class TestLRUCacheDataStructure:
    """LRUキャッシュデータ構造テスト"""
    
    @pytest.fixture
    def production_cache(self):
        """本番相当キャッシュ"""
        return LRUFrameCache(max_size=100, memory_limit=20 * 1024**3)
    
    @pytest.fixture
    def small_cache(self):
        """小規模テスト用キャッシュ"""
        return LRUFrameCache(max_size=3, memory_limit=1024**3)
    
    @pytest.fixture
    def sample_frame_data(self):
        """サンプルフレームデータ"""
        return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    @pytest.fixture
    def large_frame_data(self):
        """大容量フレームデータ（4K相当）"""
        return np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
    
    def test_o1_access_complexity(self, production_cache, large_frame_data):
        """O(1)アクセス時間複雑度確認"""
        # 異なるサイズでの性能測定
        sizes = [10, 50, 100]
        access_times = {}
        
        for size in sizes:
            # データ投入
            cache = LRUFrameCache(max_size=size, memory_limit=20 * 1024**3)
            for i in range(size):
                cache.put(f"frame_{i:06d}", large_frame_data)
            
            # アクセス時間測定
            times = []
            for _ in range(100):
                frame_id = f"frame_{np.random.randint(0, size):06d}"
                start_time = time.perf_counter()
                cache.get(frame_id)
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
            
            access_times[size] = np.mean(times)
        
        # O(1)確認：サイズが10倍になっても時間は一定
        time_10 = access_times[10]
        time_100 = access_times[100]
        
        print(f"Access times: 10={time_10:.3f}ms, 100={time_100:.3f}ms")
        assert time_100 <= time_10 * 2, "Access time not O(1) - too much increase with size"
    
    def test_hash_map_efficiency(self, production_cache):
        """ハッシュマップ効率確認"""
        # キー分散確認
        keys = [f"frame_{i:06d}" for i in range(1000)]
        
        for key in keys:
            # ハッシュ値分散確認（内部実装確認）
            hash_val = hash(key)
            assert isinstance(hash_val, int), "Hash function not working"
        
        # 衝突率確認（理論上は低いはず）
        hash_values = [hash(key) for key in keys]
        unique_hashes = len(set(hash_values))
        collision_rate = 1 - (unique_hashes / len(keys))
        
        assert collision_rate <= 0.01, f"Hash collision rate too high: {collision_rate:.3f}"
    
    def test_doubly_linked_list_operations(self, small_cache, sample_frame_data):
        """双方向リンクリスト操作確認"""
        # 順序確認のためのテスト
        keys = ["frame_A", "frame_B", "frame_C"]
        
        for key in keys:
            small_cache.put(key, sample_frame_data)
        
        # アクセス順序変更
        small_cache.get("frame_A")  # A を最新にする
        
        # 新しい要素追加（B が削除されるはず）
        small_cache.put("frame_D", sample_frame_data)
        
        # 順序確認
        assert small_cache.get("frame_B") is None, "Middle element not evicted"
        assert small_cache.get("frame_A") is not None, "Recently accessed element evicted"
        assert small_cache.get("frame_C") is not None
        assert small_cache.get("frame_D") is not None


class TestLRUCacheMemoryManagement:
    """LRUキャッシュメモリ管理テスト"""
    
    @pytest.fixture
    def production_cache(self):
        """本番相当キャッシュ"""
        return LRUFrameCache(max_size=100, memory_limit=20 * 1024**3)
    
    @pytest.fixture
    def small_cache(self):
        """小規模テスト用キャッシュ"""
        return LRUFrameCache(max_size=3, memory_limit=1024**3)
    
    @pytest.fixture
    def sample_frame_data(self):
        """サンプルフレームデータ"""
        return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    @pytest.fixture
    def large_frame_data(self):
        """大容量フレームデータ（4K相当）"""
        return np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
    
    def test_memory_usage_tracking(self, production_cache, large_frame_data):
        """メモリ使用量追跡確認"""
        initial_memory = production_cache.get_memory_usage()
        assert initial_memory == 0, "Initial memory usage not zero"
        
        # データ追加とメモリ増加確認
        frame_size = large_frame_data.nbytes
        production_cache.put("test_frame", large_frame_data)
        
        after_memory = production_cache.get_memory_usage()
        assert after_memory >= frame_size, "Memory usage not tracked properly"
        assert after_memory <= frame_size * 1.2, "Memory overhead too high"
    
    def test_memory_cleanup_on_eviction(self, small_cache, sample_frame_data):
        """削除時のメモリクリーンアップ確認"""
        frame_size = sample_frame_data.nbytes
        
        # 制限まで追加
        for i in range(3):
            small_cache.put(f"frame_{i}", sample_frame_data)
        
        memory_before = small_cache.get_memory_usage()
        assert memory_before >= frame_size * 3
        
        # 追加で削除発生
        small_cache.put("frame_new", sample_frame_data)
        
        memory_after = small_cache.get_memory_usage()
        assert memory_after <= memory_before, "Memory not cleaned up on eviction"
        assert memory_after >= frame_size * 3, "Too much memory cleaned up"
    
    def test_explicit_clear_operation(self, production_cache, large_frame_data):
        """明示的クリア操作確認"""
        # データ追加
        for i in range(10):
            production_cache.put(f"frame_{i}", large_frame_data)
        
        memory_before = production_cache.get_memory_usage()
        size_before = production_cache.size()
        
        assert memory_before > 0
        assert size_before == 10
        
        # クリア実行
        production_cache.clear()
        
        memory_after = production_cache.get_memory_usage()
        size_after = production_cache.size()
        
        assert memory_after == 0, "Memory not cleared"
        assert size_after == 0, "Size not cleared"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])