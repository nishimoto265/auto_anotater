# アーキテクチャ設計

## システム全体アーキテクチャ

### アーキテクチャ概要
```
┌─────────────────────────────────────────────────────────────┐
│                    オートアノテーションアプリ                  │
├─────────────────────────────────────────────────────────────┤
│  フロントエンド層（PyQt6/PySide6）                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ MainWindow  │ FrameViewer │ ControlPanel│ Navigation  │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ビジネスロジック層                                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ UI制御      │ 動画処理    │ アノテーション│ 追跡機能    │  │
│  │ モジュール   │ モジュール   │ モジュール   │ モジュール   │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  データアクセス層                                            │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ ファイルI/O │ フレーム     │ アノテーション│ 設定管理    │  │
│  │            │ キャッシュ    │ ストレージ   │            │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  データ層                                                   │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ 動画ファイル │ フレーム画像 │ アノテーション│ 設定ファイル │  │
│  │ (.mp4/.avi) │ (.jpg)      │ (.txt)      │ (.json)     │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 設計原則
- **レイヤード アーキテクチャ**: 関心の分離による保守性向上
- **イベント駆動**: 非同期処理による応答性向上
- **依存性注入**: テスタビリティと拡張性の確保
- **プラグイン アーキテクチャ**: 将来の機能拡張への対応

## モジュールアーキテクチャ

### 1. UIモジュール（フロントエンド）
```
ui-module/
├── components/               # UIコンポーネント
│   ├── main_window.py       # メインウィンドウ（MVCのController）
│   ├── frame_viewer.py      # フレーム表示（View + 一部Controller）
│   ├── bbox_overlay.py      # BB描画オーバーレイ（View）
│   ├── control_panel.py     # 制御パネル（View + Controller）
│   └── navigation.py        # ナビゲーション（View + Controller）
├── services/                # UIサービス
│   ├── ui_state.py         # UI状態管理（Model）
│   ├── event_bus.py        # イベント管理（Observer Pattern）
│   ├── theme_manager.py    # テーマ管理
│   └── shortcut_manager.py # ショートカット管理
└── styles/                 # スタイルシート
    ├── main.qss
    ├── dark_theme.qss
    └── light_theme.qss
```

**設計パターン**:
- **MVC Pattern**: View（UI）、Model（状態）、Controller（制御）の分離
- **Observer Pattern**: UIイベントの非同期通知
- **Strategy Pattern**: テーマ切り替え

### 2. 動画処理モジュール（バックエンド）
```
video-processing-module/
├── core/                   # コア機能
│   ├── video_loader.py    # 動画読み込み（Factory Pattern）
│   ├── frame_extractor.py # フレーム抽出
│   └── format_converter.py# 形式変換
├── cache/                 # キャッシュ機能
│   ├── frame_cache.py     # フレームキャッシュ（LRU）
│   ├── cache_manager.py   # キャッシュ管理
│   └── memory_monitor.py  # メモリ監視
├── batch/                 # バッチ処理
│   ├── batch_processor.py # バッチ処理エンジン
│   └── progress_tracker.py# 進捗追跡
└── utils/
    ├── video_info.py      # 動画情報
    └── validators.py      # バリデーション
```

**設計パターン**:
- **Factory Pattern**: 動画ローダーの形式別実装
- **Strategy Pattern**: キャッシュアルゴリズムの切り替え
- **Command Pattern**: バッチ処理の実行管理

### 3. アノテーションモジュール（バックエンド）
```
annotation-module/
├── models/                # データモデル
│   ├── bounding_box.py    # BBデータクラス
│   ├── annotation.py      # アノテーションデータ
│   └── project.py         # プロジェクト情報
├── managers/              # 管理クラス
│   ├── bbox_manager.py    # BB管理
│   ├── annotation_manager.py # アノテーション管理
│   └── project_manager.py # プロジェクト管理
├── io/                    # 入出力
│   ├── annotation_io.py   # ファイル読み書き
│   ├── yolo_format.py     # YOLO形式変換
│   └── backup_manager.py  # バックアップ管理
├── validation/            # データ検証
│   ├── data_validator.py  # データ検証
│   └── consistency_checker.py # 整合性チェック
└── auto_save/
    ├── auto_saver.py      # 自動保存
    └── recovery.py        # 復旧機能
```

**設計パターン**:
- **Repository Pattern**: データアクセスの抽象化
- **Observer Pattern**: 自動保存の変更通知
- **Template Method Pattern**: ファイル形式別I/O処理

### 4. 追跡モジュール（バックエンド）
```
tracking-module/
├── algorithms/            # 追跡アルゴリズム
│   ├── feature_tracker.py # 特徴点追跡
│   ├── template_tracker.py# テンプレートマッチング
│   └── optical_flow.py    # オプティカルフロー
├── features/              # 特徴抽出
│   ├── feature_extractor.py # 特徴抽出器
│   ├── descriptors.py     # 特徴記述子
│   └── matchers.py        # マッチング
├── similarity/            # 類似度計算
│   ├── similarity_calculator.py # 類似度計算
│   ├── distance_metrics.py # 距離メトリクス
│   └── threshold_manager.py # 閾値管理
└── trajectory/            # 軌跡管理
    ├── trajectory.py      # 軌跡データ
    ├── path_smoother.py   # パス平滑化
    └── gap_filler.py      # 欠損補間
```

**設計パターン**:
- **Strategy Pattern**: 追跡アルゴリズムの切り替え
- **Chain of Responsibility**: 特徴抽出パイプライン
- **State Pattern**: 追跡状態の管理

## データフローアーキテクチャ

### 1. 動画読み込みフロー
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   動画ファイル   │ -> │ VideoLoader │ -> │ VideoInfo   │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          v
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ FrameCache  │ <- │FrameExtractor│ <- │ バッチ処理    │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          v
┌─────────────┐    ┌─────────────┐
│ フレーム画像  │ <- │ FileOutput  │
└─────────────┘    └─────────────┘
```

### 2. アノテーションフロー
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ UI操作      │ -> │ EventBus    │ -> │ BBoxManager │
└─────────────┘    └─────────────┘    └─────────────┘
                                            │
                                            v
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ AutoSaver   │ <- │AnnotationMgr│ <- │ Validation  │
└─────────────┘    └─────────────┘    └─────────────┘
       │
       v
┌─────────────┐    ┌─────────────┐
│ txtファイル   │ <- │ AnnotationIO│
└─────────────┘    └─────────────┘
```

### 3. 追跡フロー
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 初期BB設定   │ -> │FeatureExtract│ -> │ Tracker     │
└─────────────┘    └─────────────┘    └─────────────┘
                                            │
                                            v
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 予測BB      │ <- │ Trajectory  │ <- │ Similarity  │
└─────────────┘    └─────────────┘    └─────────────┘
       │
       v
┌─────────────┐    ┌─────────────┐
│ UI更新      │ <- │ EventBus    │
└─────────────┘    └─────────────┘
```

## パフォーマンスアーキテクチャ

### 1. マルチスレッド設計
```
┌─────────────────────────────────────────────────────────────┐
│                     Main Thread (UI)                       │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ MainWindow  │ EventLoop   │ Rendering   │ User Input  │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               v (Queue)
┌─────────────────────────────────────────────────────────────┐
│                  Background Threads                        │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ FrameLoader │ AutoSaver   │ Tracker     │ FileWatcher │  │
│  │ Thread      │ Thread      │ Thread      │ Thread      │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**スレッド分離**:
- **Main Thread**: UI表示・ユーザー操作（16ms以下）
- **FrameLoader Thread**: フレーム読み込み・キャッシュ管理
- **AutoSaver Thread**: アノテーション自動保存
- **Tracker Thread**: 追跡アルゴリズム実行

### 2. メモリ管理アーキテクチャ
```
┌─────────────────────────────────────────────────────────────┐
│                   Memory Management                        │
├─────────────────────────────────────────────────────────────┤
│  L1 Cache (Display)     │ 現在表示フレーム + 前後5フレーム    │
│  ├─ Resolution: 1/2     │ Size: ~50MB                    │
│  └─ Access: <1ms        │ Hit Rate: >95%                 │
├─────────────────────────────────────────────────────────────┤
│  L2 Cache (Preload)     │ 前後100フレーム                   │
│  ├─ Resolution: 1/2     │ Size: ~1GB                     │
│  └─ Access: <10ms       │ Hit Rate: >80%                 │
├─────────────────────────────────────────────────────────────┤
│  L3 Cache (Background)  │ フルサイズキャッシュ               │
│  ├─ Resolution: Full    │ Size: ~20GB                    │
│  └─ Access: <50ms       │ Hit Rate: >60%                 │
├─────────────────────────────────────────────────────────────┤
│  Storage (Disk)         │ 全フレーム                        │
│  ├─ Format: JPEG        │ Size: ~100GB                   │
│  └─ Access: <200ms      │ Hit Rate: <40%                 │
└─────────────────────────────────────────────────────────────┘
```

### 3. 描画最適化アーキテクチャ
```
┌─────────────────────────────────────────────────────────────┐
│                   Rendering Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│  Frame Input            │ Image Data (NumPy Array)         │
│  └─ Format: RGB/BGR     │ Size: H×W×C                      │
├─────────────────────────────────────────────────────────────┤
│  Display Scaling        │ 1/2 Scale for Performance        │
│  ├─ Method: cv2.resize  │ Time: <5ms                       │
│  └─ Quality: INTER_AREA │ Memory: 1/4 reduction            │
├─────────────────────────────────────────────────────────────┤
│  Qt Conversion          │ NumPy -> QImage -> QPixmap        │
│  ├─ Format: RGB888      │ Time: <5ms                       │
│  └─ Optimization: Zero-copy when possible                  │
├─────────────────────────────────────────────────────────────┤
│  BBox Overlay           │ Vector Graphics on QGraphicsScene │
│  ├─ Method: Incremental │ Time: <6ms for 50 boxes         │
│  └─ Culling: Viewport-based clipping                       │
├─────────────────────────────────────────────────────────────┤
│  Display Output         │ Final Rendering                   │
│  └─ Target: 60fps (16ms) │ Actual: <16ms total             │
└─────────────────────────────────────────────────────────────┘
```

## イベント駆動アーキテクチャ

### 1. イベントバス設計
```python
class EventBus:
    """中央集権的イベント管理"""
    
    def __init__(self):
        self.handlers = defaultdict(list)
        self.event_queue = queue.Queue()
        self.is_running = False
    
    def subscribe(self, event_type: str, handler: Callable):
        """イベントハンドラーの登録"""
        self.handlers[event_type].append(handler)
    
    def publish(self, event_type: str, data: Any):
        """イベントの発行"""
        self.event_queue.put((event_type, data))
    
    def process_events(self):
        """イベント処理ループ"""
        while self.is_running:
            try:
                event_type, data = self.event_queue.get(timeout=0.1)
                for handler in self.handlers[event_type]:
                    handler(data)
            except queue.Empty:
                continue
```

### 2. イベント定義
```python
# UIイベント
UI_FRAME_CHANGED = "ui.frame_changed"
UI_BBOX_CREATED = "ui.bbox_created"
UI_BBOX_MODIFIED = "ui.bbox_modified"
UI_BBOX_DELETED = "ui.bbox_deleted"

# 動画処理イベント
VIDEO_LOADED = "video.loaded"
FRAME_EXTRACTED = "frame.extracted"
CACHE_UPDATED = "cache.updated"

# アノテーションイベント
ANNOTATION_SAVED = "annotation.saved"
ANNOTATION_LOADED = "annotation.loaded"
PROJECT_CREATED = "project.created"

# 追跡イベント
TRACKING_STARTED = "tracking.started"
TRACKING_COMPLETED = "tracking.completed"
TRACKING_FAILED = "tracking.failed"
```

### 3. イベントフロー例
```
┌─────────────┐    UI_BBOX_CREATED    ┌─────────────┐
│ FrameViewer │ ───────────────────> │ EventBus    │
└─────────────┘                      └─────────────┘
                                           │
                                           ├─> BBoxManager.add_bbox()
                                           ├─> AutoSaver.save_annotation()
                                           ├─> Tracker.start_tracking()
                                           └─> ControlPanel.update_list()
```

## 拡張性アーキテクチャ

### 1. プラグインアーキテクチャ
```python
class PluginInterface(ABC):
    """プラグインインターフェース"""
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        pass
    
    @abstractmethod
    def initialize(self, context: PluginContext) -> bool:
        pass

class TrackingPlugin(PluginInterface):
    """追跡プラグインベースクラス"""
    
    @abstractmethod
    def track_bbox(self, bbox: BoundingBox, frames: List[np.ndarray]) -> List[BoundingBox]:
        pass

class YOLOTrackingPlugin(TrackingPlugin):
    """YOLOベース追跡プラグイン"""
    
    def track_bbox(self, bbox: BoundingBox, frames: List[np.ndarray]) -> List[BoundingBox]:
        # YOLO実装
        pass
```

### 2. 設定管理アーキテクチャ
```python
class ConfigManager:
    """階層的設定管理"""
    
    def __init__(self):
        self.configs = {
            'app': AppConfig(),
            'ui': UIConfig(),
            'video': VideoConfig(),
            'tracking': TrackingConfig(),
            'performance': PerformanceConfig()
        }
    
    def get(self, path: str, default=None):
        """ドット記法での設定取得"""
        keys = path.split('.')
        value = self.configs
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return default
        
        return value

# 使用例
config = ConfigManager()
frame_cache_size = config.get('performance.cache.frame_cache_size_mb', 1024)
ui_theme = config.get('ui.theme', 'dark')
```

## セキュリティアーキテクチャ

### 1. データ保護
```python
class SecureDataManager:
    """セキュアなデータ管理"""
    
    def __init__(self):
        self.encryption_key = self._generate_key()
    
    def save_sensitive_data(self, data: dict, file_path: str):
        """機密データの暗号化保存"""
        encrypted_data = self._encrypt(json.dumps(data))
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
    
    def load_sensitive_data(self, file_path: str) -> dict:
        """機密データの復号化読み込み"""
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self._decrypt(encrypted_data)
        return json.loads(decrypted_data)
```

### 2. 入力検証
```python
class InputValidator:
    """入力値検証"""
    
    @staticmethod
    def validate_file_path(path: str) -> bool:
        """ファイルパスの検証"""
        # パストラバーサル攻撃の防止
        normalized = os.path.normpath(path)
        if '..' in normalized:
            return False
        
        # 許可された拡張子のチェック
        allowed_extensions = {'.mp4', '.avi', '.jpg', '.txt', '.json'}
        ext = os.path.splitext(path)[1].lower()
        return ext in allowed_extensions
    
    @staticmethod
    def validate_bbox_coordinates(x: float, y: float, w: float, h: float) -> bool:
        """BB座標の検証"""
        # YOLO形式の範囲チェック
        return all(0.0 <= coord <= 1.0 for coord in [x, y, w, h])
```

このアーキテクチャ設計により、高性能で拡張可能、かつ保守しやすいオートアノテーションアプリを構築できます。各Agentはこの設計に従って実装を進めてください。