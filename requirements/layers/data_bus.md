# Agent5: Data Bus Layer 詳細仕様書（通信基盤Agent）

## 🎯 Agent5 Data Bus の使命
**Agent間通信統一基盤** - 8Agent協調動作の要

## 📋 Agent5開始時の必須確認項目

### 開発開始前チェックリスト
- [ ] CLAUDE.md読了（Agent5責任範囲確認）
- [ ] requirement.yaml確認（通信要件理解）
- [ ] config/layer_interfaces.yaml確認（通信プロトコル詳細）
- [ ] config/performance_targets.yaml確認（通信性能目標）
- [ ] tests/requirements/unit/data-bus-unit-tests.md確認（テスト要件）

### Agent5専門領域
```
責任範囲: Agent間通信・イベント配信・メッセージング統合
技術領域: Event Bus、Message Queue、API Gateway、通信プロトコル
実装場所: src/data_bus/
テスト場所: tests/unit/test_data_bus/
```

## 🏗️ 実装すべきコンポーネント詳細

### 1. event_bus/ - イベントバス（非同期通信）
```
src/data_bus/event_bus/
├── __init__.py
├── event_dispatcher.py    # イベント配信エンジン
├── event_subscriber.py    # イベント購読管理
└── event_types.py         # イベント型定義
```

#### event_dispatcher.py 仕様
```python
class EventDispatcher:
    """
    非同期イベント配信エンジン
    
    性能要件:
    - イベント配信: 1ms以下
    - 同時購読者: 8Agent対応
    - 配信保証: best effort
    """
    
    def publish(self, event_type: str, data: dict) -> bool:
        """
        イベント発行（1ms以下必達）
        
        Args:
            event_type: frame_changed, bb_created等
            data: イベントデータ
            
        Returns:
            bool: 発行成功フラグ
        """
        
    def subscribe(self, event_type: str, callback: Callable) -> str:
        """
        イベント購読登録
        
        Returns:
            str: 購読ID
        """
        
    def unsubscribe(self, subscription_id: str) -> bool:
        """購読解除"""
```

#### event_types.py 仕様
```python
# 必須イベント型定義
EVENT_FRAME_CHANGED = "frame_changed"
EVENT_BB_CREATED = "bb_created" 
EVENT_BB_UPDATED = "bb_updated"
EVENT_BB_DELETED = "bb_deleted"
EVENT_TRACKING_STARTED = "tracking_started"
EVENT_TRACKING_COMPLETED = "tracking_completed"
EVENT_PERFORMANCE_WARNING = "performance_warning"
EVENT_CACHE_HIT = "cache_hit"
EVENT_CACHE_MISS = "cache_miss"
EVENT_MEMORY_USAGE = "memory_usage"
EVENT_ERROR_OCCURRED = "error_occurred"

class EventData:
    """イベントデータ基底クラス"""
    timestamp: float
    source_agent: str
    event_id: str
```

### 2. message_queue/ - メッセージキュー（同期通信）
```
src/data_bus/message_queue/
├── __init__.py
├── queue_manager.py       # キュー管理
├── message_serializer.py  # メッセージシリアライズ
└── priority_queue.py      # 優先度付きキュー
```

#### queue_manager.py 仕様
```python
class QueueManager:
    """
    Agent間メッセージキュー管理
    
    性能要件:
    - メッセージ転送: 1ms以下
    - 優先度制御: 高/通常/低
    - 容量制限: メモリ効率運用
    """
    
    def send_message(self, target_agent: str, message: dict, 
                    priority: str = "normal", timeout: int = 1000) -> Any:
        """
        同期メッセージ送信（1ms以下必達）
        
        Args:
            target_agent: 送信先Agent名
            message: メッセージデータ
            priority: high/normal/low
            timeout: タイムアウト（ms）
            
        Returns:
            Any: レスポンスデータ
        """
        
    def register_handler(self, message_type: str, handler: Callable):
        """メッセージハンドラー登録"""
```

### 3. interfaces/ - インターフェース管理
```
src/data_bus/interfaces/
├── __init__.py
├── layer_interface.py     # レイヤー間API管理
├── communication_protocol.py  # 通信プロトコル
└── api_registry.py        # API登録・発見
```

#### layer_interface.py 仕様
```python
class LayerInterface:
    """
    Agent間統一API呼び出しインターフェース
    
    使用例:
    result = layer_interface.call_service(
        "cache_layer", "get_frame", frame_id="000001"
    )
    """
    
    def call_service(self, layer_name: str, service_name: str, 
                    timeout: int = None, **kwargs) -> Any:
        """
        レイヤー間API呼び出し
        
        Args:
            layer_name: presentation, application, domain等
            service_name: get_frame, create_bb等
            timeout: タイムアウト（ms）
            **kwargs: サービス引数
        """
        
    def register_service(self, layer_name: str, service_name: str, 
                        handler: Callable, timeout: int = 1000):
        """サービス登録"""
```

## ⚡ パフォーマンス要件詳細

### 通信性能目標
```yaml
event_dispatch:
  target: "1ms以下"
  measurement: "publish()実行時間"
  max_subscribers: 8
  
message_transfer:
  target: "1ms以下" 
  measurement: "send_message()実行時間"
  max_message_size: "100KB"
  
communication_overhead:
  target: "全体の5%以下"
  measurement: "通信時間/総処理時間"
  monitoring: "リアルタイム"
  
queue_performance:
  latency: "遅延ゼロ"
  throughput: "1000 msg/sec"
  priority_levels: 3
```

### Agent間通信マトリクス
```yaml
# 頻繁な通信ペア（最適化重点）
high_frequency:
  - cache_layer ↔ infrastructure
  - presentation ↔ application  
  - application ↔ domain
  
# イベント配信（多対多）
event_broadcast:
  - frame_changed: [cache, persistence, monitoring]
  - bb_created: [presentation, persistence]
  - performance_warning: [monitoring, cache]
```

## 🔗 Agent別通信インターフェース実装

### Cache Layer連携（最重要）
```python
# Cache Agentサービス登録
def register_cache_services(self):
    self.register_service("cache_layer", "get_frame", 
                         self.cache_agent.get_frame, timeout=50)
    self.register_service("cache_layer", "preload_frames",
                         self.cache_agent.preload_frames, timeout=1)

# フレーム切り替え専用高速チャネル
class FastFrameChannel:
    """フレーム切り替え専用の最適化チャネル（50ms以下保証）"""
    
    def switch_frame(self, frame_id: str) -> FrameData:
        """直接通信による高速フレーム切り替え"""
```

### Presentation Layer連携
```python
# UI操作イベント処理
@event_handler("user_input")
def handle_ui_events(self, event_data):
    """
    UIイベント→Applicationレイヤー転送
    キーボード1ms、マウス5ms以下保証
    """
    
# UI更新イベント配信
def notify_ui_update(self, update_type: str, data: dict):
    """UI更新通知（描画更新用）"""
```

## 🧪 テスト要件（TDD必須）

### 単体テスト必須項目
```python
# tests/unit/test_data_bus/test_event_dispatcher.py
class TestEventDispatcher:
    def test_publish_1ms_performance(self):
        """publish()が1ms以下で完了確認"""
        
    def test_multi_subscriber_delivery(self):
        """複数購読者への配信確認"""
        
    def test_event_ordering(self):
        """イベント順序保証確認"""

# tests/unit/test_data_bus/test_queue_manager.py  
class TestQueueManager:
    def test_message_transfer_1ms(self):
        """メッセージ転送1ms以下確認"""
        
    def test_priority_queue_ordering(self):
        """優先度キュー動作確認"""
        
    def test_timeout_handling(self):
        """タイムアウト処理確認"""
```

### 統合テスト必須項目
```python
# tests/integration/test_data_bus_integration.py
class TestDataBusIntegration:
    def test_all_agent_communication(self):
        """全Agent間通信確認"""
        
    def test_concurrent_messaging(self):
        """並行メッセージング確認"""
        
    def test_frame_switching_flow(self):
        """フレーム切り替え通信フロー確認"""
```

## 🛠️ 実装ガイドライン

### 必須技術スタック
```python
import asyncio           # 非同期処理
import threading        # マルチスレッド
import queue           # スレッドセーフキュー
import time           # 高精度時間測定
import uuid           # 一意ID生成
import json           # メッセージシリアライズ
from typing import Callable, Any, Dict, List
from dataclasses import dataclass
```

### 通信プロトコル実装
```python
@dataclass
class Message:
    """標準メッセージ形式"""
    id: str
    source: str
    target: str
    type: str
    data: dict
    timestamp: float
    priority: str = "normal"

class CommunicationProtocol:
    """通信プロトコル統一実装"""
    
    def serialize_message(self, message: Message) -> bytes:
        """メッセージシリアライズ"""
        
    def deserialize_message(self, data: bytes) -> Message:
        """メッセージデシリアライズ"""
```

### エラーハンドリング
```python
class CommunicationError(Exception):
    """通信エラー基底クラス"""
    
class TimeoutError(CommunicationError):
    """タイムアウトエラー"""
    
class AgentNotFoundError(CommunicationError):
    """Agent未発見エラー"""

def with_timeout(timeout_ms: int):
    """タイムアウト付きデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # タイムアウト処理実装
            pass
        return wrapper
    return decorator
```

## 📊 監視・デバッグ機能

### 通信統計収集
```python
class CommunicationStats:
    """通信統計収集"""
    
    def record_message_time(self, source: str, target: str, duration: float):
        """メッセージ送信時間記録"""
        
    def record_event_delivery(self, event_type: str, subscriber_count: int):
        """イベント配信統計記録"""
        
    def get_performance_report(self) -> dict:
        """性能レポート生成"""
```

### リアルタイムモニタリング
```python
class CommuncationMonitor:
    """リアルタイム通信監視"""
    
    def monitor_message_flow(self):
        """メッセージフロー監視"""
        
    def detect_communication_bottleneck(self):
        """通信ボトルネック検知"""
        
    def generate_alert(self, condition: str, data: dict):
        """通信アラート生成"""
```

## ✅ Agent5完了条件

### 機能完了チェック
- [ ] EventBus動作確認（非同期）
- [ ] MessageQueue動作確認（同期）
- [ ] LayerInterface動作確認（API呼び出し）
- [ ] 全Agent間通信確認

### 性能完了チェック
- [ ] イベント配信1ms以下
- [ ] メッセージ転送1ms以下
- [ ] 通信オーバーヘッド5%以下
- [ ] 並行処理安定性確認

### テスト完了チェック
- [ ] 単体テスト100%通過
- [ ] 統合テスト100%通過
- [ ] 通信性能テスト通過
- [ ] エラーハンドリングテスト通過

---

**Agent5 Data Busは、8Agent協調動作の基盤です。高速で安定した通信により、特にCache Agent（フレーム切り替え50ms）の性能発揮を支えます。**