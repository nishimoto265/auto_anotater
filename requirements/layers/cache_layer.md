# Agent6: Cache Layer 詳細仕様書（最重要Agent）

## 🎯 Agent6 Cache の使命
**フレーム切り替え50ms以下絶対達成** - プロジェクト成功の要

## 📋 Agent6開始時の必須確認項目

### 開発開始前チェックリスト
- [ ] CLAUDE.md読了（Agent6責任範囲確認）
- [ ] requirement.yaml確認（システム要件理解）
- [ ] config/performance_targets.yaml確認（性能目標50ms理解）
- [ ] config/layer_interfaces.yaml確認（他Agent通信方法）
- [ ] tests/requirements/unit/cache-layer-unit-tests.md確認（テスト要件）

### Agent6専門領域
```
責任範囲: 高速キャッシュ・パフォーマンス最適化・メモリ管理
最重要目標: フレーム切り替え50ms以下絶対達成
技術領域: LRU Cache、先読み、非同期I/O、メモリ最適化
実装場所: src/cache_layer/
テスト場所: tests/unit/test_cache_layer/
```

## 🏗️ 実装すべきコンポーネント詳細

### 1. frame_cache/ - フレームキャッシュ（最重要）
```
src/cache_layer/frame_cache/
├── __init__.py
├── lru_cache.py           # LRUアルゴリズム実装
├── preloader.py           # バックグラウンド先読み
├── cache_optimizer.py     # キャッシュ最適化エンジン
└── memory_monitor.py      # メモリ使用量監視
```

#### lru_cache.py 仕様
```python
class LRUFrameCache:
    """
    フレーム切り替え50ms以下達成のためのLRUキャッシュ
    
    性能要件:
    - get(): 5ms以下
    - put(): 5ms以下
    - キャッシュヒット率: 95%以上
    - メモリ上限: 20GB
    """
    
    def __init__(self, max_size: int = 100, memory_limit: int = 20*1024**3):
        """
        Args:
            max_size: 最大フレーム数（前後100フレーム）
            memory_limit: メモリ上限（20GB）
        """
        
    def get(self, frame_id: str) -> Optional[FrameData]:
        """
        フレーム取得（5ms以下必達）
        
        Returns:
            FrameData: フレーム画像データ、None if miss
        """
        
    def put(self, frame_id: str, frame_data: FrameData) -> bool:
        """
        フレーム格納（5ms以下必達）
        
        Returns:
            bool: 格納成功フラグ
        """
```

#### preloader.py 仕様
```python
class AsyncPreloader:
    """
    バックグラウンド先読みエンジン
    
    性能要件:
    - 先読み範囲: 前後50フレーム
    - バックグラウンド実行（UIブロックなし）
    - 先読みヒット率: 90%以上
    """
    
    def start_preload(self, current_frame: str, direction: str = "both"):
        """先読み開始（1ms以下でキューイング）"""
        
    def predict_next_frames(self, access_pattern: List[str]) -> List[str]:
        """アクセスパターン学習による予測先読み"""
```

### 2. image_cache/ - 画像キャッシュ
```
src/cache_layer/image_cache/
├── __init__.py
├── display_cache.py       # 表示用リサイズ画像キャッシュ
├── full_size_cache.py     # フルサイズ画像キャッシュ
└── compressed_cache.py    # 圧縮画像キャッシュ
```

### 3. strategies/ - キャッシュ戦略
```
src/cache_layer/strategies/
├── __init__.py
├── caching_strategy.py    # キャッシュ戦略選択
├── eviction_policy.py     # 削除ポリシー
└── prefetch_strategy.py   # 先読み戦略
```

## ⚡ パフォーマンス要件詳細

### 絶対達成目標
```yaml
frame_switching:
  target: "50ms以下"
  breakdown:
    cache_lookup: "5ms以下"     # HashMap O(1)アクセス
    memory_access: "30ms以下"   # メモリ→CPU転送
    data_transfer: "10ms以下"   # Agent間転送
    finalization: "5ms以下"     # 最終処理
  
cache_hit_rate:
  target: "95%以上"
  measurement: "ヒット数/(ヒット数+ミス数)"
  
memory_management:
  limit: "20GB"
  monitoring: "RSS（実使用メモリ）"
  strategy: "LRU削除による上限制御"
```

### 測定・監視要件
```python
@performance_monitor
def get_frame(self, frame_id: str) -> FrameData:
    """
    フレーム取得時間を自動測定
    50ms超過時は即座にアラート
    """
    
@memory_monitor  
def cleanup_cache(self):
    """
    メモリ使用量を監視
    18GB超過時は事前削除実行
    """
```

## 🔗 他Agent連携インターフェース

### Infrastructure層との連携
```yaml
cache_to_infrastructure:
  load_frame:
    description: "キャッシュミス時のフレーム読み込み"
    timeout: "45ms以下"
    fallback: "エラー時は前フレーム維持"
    
  preload_frames:
    description: "バックグラウンド先読み要求"
    async: true
    priority: "低優先度"
```

### Data Bus層との連携
```python
# フレーム切り替えイベント受信
@event_handler("frame_changed")
def on_frame_changed(self, event_data):
    """
    フレーム切り替え通知受信
    → 次フレーム先読み開始（1ms以内）
    """
    
# パフォーマンス警告発信
def emit_performance_warning(self, metric, value, threshold):
    """
    性能劣化検知時の警告発信
    → Monitoring Agentに通知
    """
```

## 🧪 テスト要件（TDD必須）

### 単体テスト必須項目
```python
# tests/unit/test_cache_layer/test_lru_cache.py
class TestLRUCache:
    def test_get_performance_5ms(self):
        """get()が5ms以下で完了することを確認"""
        
    def test_hit_rate_95_percent(self):
        """ヒット率95%以上を確認"""
        
    def test_memory_limit_20gb(self):
        """メモリ使用量20GB以下を確認"""
        
    def test_frame_switching_50ms(self):
        """フレーム切り替え50ms以下を確認（最重要）"""
```

### 統合テスト必須項目
```python
# tests/integration/test_cache_integration.py
class TestCacheIntegration:
    def test_infrastructure_communication(self):
        """Infrastructure層との通信確認"""
        
    def test_data_bus_events(self):
        """Data Bus経由イベント処理確認"""
        
    def test_concurrent_access(self):
        """並行アクセス時の性能確認"""
```

### パフォーマンステスト必須項目
```python
# tests/e2e/test_frame_switching_performance.py
def test_1000_frame_switches():
    """
    1000回連続フレーム切り替えテスト
    全て50ms以下達成を確認
    """
    
def test_4_hour_endurance():
    """
    4時間連続動作テスト
    メモリリーク・性能劣化なし確認
    """
```

## 🛠️ 実装ガイドライン

### 必須技術スタック
```python
# 必須ライブラリ
import numpy as np          # 高速数値計算
import threading           # マルチスレッド
import asyncio            # 非同期処理  
import psutil             # メモリ監視
import time              # 高精度時間測定

# パフォーマンス最適化
from functools import lru_cache    # Python標準LRU
from concurrent.futures import ThreadPoolExecutor
import mmap              # メモリマップファイル
```

### 実装優先順序
1. **基本LRUキャッシュ実装**（Day 1）
2. **フレーム切り替え50ms確認**（Day 1-2）
3. **先読み機能実装**（Day 2）
4. **メモリ管理最適化**（Day 2-3）
5. **統合テスト・最終調整**（Day 3-4）

### デバッグ・監視機能
```python
class CacheDebugger:
    """Cache Agent専用デバッグ機能"""
    
    def log_performance_metrics(self):
        """性能メトリクス詳細ログ"""
        
    def analyze_cache_patterns(self):
        """キャッシュアクセスパターン分析"""
        
    def memory_usage_report(self):
        """メモリ使用量詳細レポート"""
```

## 🚨 緊急時対応

### 50ms未達成時の対処
1. **キャッシュアルゴリズム見直し**
2. **メモリアクセス最適化**
3. **並行処理改善**
4. **Infrastructure層との通信最適化**

### メモリ不足時の対処
1. **LRU削除の積極実行**
2. **キャッシュサイズ動的調整**
3. **メモリマップファイル活用**
4. **ガベージコレクション強制実行**

## ✅ Agent6完了条件

### 機能完了チェック
- [ ] LRUキャッシュ動作確認
- [ ] 先読み機能動作確認
- [ ] メモリ管理動作確認
- [ ] Agent間通信確認

### 性能完了チェック
- [ ] **フレーム切り替え50ms以下100%達成**
- [ ] キャッシュヒット率95%以上
- [ ] メモリ使用量20GB以下
- [ ] 4時間連続動作安定性

### テスト完了チェック
- [ ] 単体テスト100%通過
- [ ] 統合テスト100%通過
- [ ] パフォーマンステスト100%通過
- [ ] エンドツーエンドテスト通過

---

**Agent6 Cacheは、プロジェクト成功の最重要要因です。フレーム切り替え50ms以下の絶対達成により、個人用動物行動解析ツールの実用性を決定づけます。**