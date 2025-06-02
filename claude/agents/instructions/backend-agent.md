# Backend Agent 指示書

## 役割・責務
バックエンド実装を担当する専門Agent。PyQt6/PySide6アプリケーションのコア機能とビジネスロジックを実装。

## 主要タスク

### 1. モジュール実装
- **UIモジュール**: PyQt6/PySide6によるメインアプリケーション
- **動画処理モジュール**: OpenCVによる動画読み込み・フレーム抽出
- **アノテーションモジュール**: BB管理・保存機能
- **追跡モジュール**: 自動追跡アルゴリズム実装

### 2. アーキテクチャ実装
- **MVCパターン**: Model-View-Controller設計
- **依存性注入**: モジュール間の疎結合
- **イベント駆動**: 非同期処理・UI連携
- **プラグイン対応**: 拡張可能な設計

### 3. パフォーマンス最適化
- **メモリ管理**: 効率的なキャッシュ・リソース管理
- **マルチスレッド**: バックグラウンド処理の並列化
- **I/O最適化**: ファイル読み書きの高速化

## 実装方針

### アーキテクチャ設計
```python
# メインアプリケーション構成
claude/implementation/src/backend/
├── ui-module/              # UIコントローラ
│   ├── main_window.py     # メインウィンドウ制御
│   ├── frame_viewer.py    # フレーム表示制御
│   ├── bbox_editor.py     # BB編集制御
│   └── navigation.py      # ナビゲーション制御
├── video-processing-module/  # 動画処理
│   ├── video_loader.py    # 動画読み込み
│   ├── frame_extractor.py # フレーム抽出
│   ├── frame_cache.py     # フレームキャッシュ
│   └── batch_processor.py # バッチ処理
├── annotation-module/       # アノテーション管理
│   ├── bbox_manager.py    # BB管理
│   ├── annotation_io.py   # 読み書き処理
│   ├── data_validator.py  # データ検証
│   └── auto_save.py       # 自動保存
└── tracking-module/         # 追跡機能
    ├── tracker.py         # 追跡アルゴリズム
    ├── feature_extractor.py # 特徴抽出
    ├── similarity.py      # 類似度計算
    └── trajectory.py      # 軌跡管理
```

### 開発フロー
```bash
# 1. ワークツリーでの並列開発
cd workspace/worktrees/ui-feature
# implementation/src/backend/ui-module/ で実装

cd workspace/worktrees/video-feature  
# implementation/src/backend/video-processing-module/ で実装

# 2. 単体テスト実行
pytest implementation/src/backend/ui-module/tests/
pytest implementation/src/backend/video-processing-module/tests/

# 3. テスト通過後、統合キューへ
# testing-agentが自動的にマージキューに移動
```

## 技術仕様

### 1. UIモジュール実装
```python
class MainApplication:
    """メインアプリケーション制御"""
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.annotation_manager = AnnotationManager()
        self.tracker = Tracker()
        self.setup_ui()
    
    def setup_ui(self):
        """UI初期化"""
        self.main_window = MainWindow()
        self.frame_viewer = FrameViewer()
        self.bbox_editor = BBoxEditor()
        self.navigation = Navigation()
    
class FrameViewer:
    """フレーム表示制御（50ms以下での切り替え）"""
    def __init__(self):
        self.cache = FrameCache(size_mb=20480)  # 20GB
        self.zoom_factor = 1.0
        
    def display_frame(self, frame_index: int):
        """高速フレーム表示"""
        frame = self.cache.get_frame(frame_index)
        if frame is None:
            frame = self.load_frame_async(frame_index)
        self.render_frame(frame)
        
class BBoxEditor:
    """BB編集制御（16ms以下での描画）"""
    def create_bbox(self, start_point, end_point):
        """BB作成"""
        bbox = BoundingBox(start_point, end_point)
        self.annotation_manager.add_bbox(bbox)
        self.update_display()
```

### 2. 動画処理モジュール実装
```python
class VideoProcessor:
    """動画処理の中心クラス"""
    def __init__(self):
        self.video_path = None
        self.cap = None
        self.frame_count = 0
        self.fps = 0
        
    def load_video(self, video_path: str):
        """動画読み込み（メタデータ取得）"""
        self.cap = cv2.VideoCapture(video_path)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
    def extract_frames(self, output_dir: str, target_fps: float = 5.0):
        """フレーム抽出（30fps → 5fps）"""
        interval = int(self.fps / target_fps)
        frame_index = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            if frame_index % interval == 0:
                filename = f"{frame_index//interval:06d}.jpg"
                cv2.imwrite(os.path.join(output_dir, filename), frame)
                
            frame_index += 1

class FrameCache:
    """高速フレームキャッシュ（LRU + 先読み）"""
    def __init__(self, size_mb: int = 20480):
        self.cache = {}
        self.max_size = size_mb * 1024 * 1024
        self.current_size = 0
        self.access_order = []
        
    def get_frame(self, frame_index: int) -> Optional[np.ndarray]:
        """フレーム取得（キャッシュ優先）"""
        if frame_index in self.cache:
            self.access_order.remove(frame_index)
            self.access_order.append(frame_index)
            return self.cache[frame_index]
        return None
        
    def preload_frames(self, center_index: int, radius: int = 100):
        """先読みキャッシュ（前後100フレーム）"""
        start = max(0, center_index - radius)
        end = min(self.frame_count, center_index + radius)
        
        for i in range(start, end):
            if i not in self.cache:
                self.load_frame_to_cache(i)
```

### 3. アノテーションモジュール実装
```python
class AnnotationManager:
    """アノテーション管理"""
    def __init__(self):
        self.bboxes = {}  # frame_index: [BoundingBox]
        self.auto_saver = AutoSaver()
        
    def add_bbox(self, frame_index: int, bbox: BoundingBox):
        """BB追加"""
        if frame_index not in self.bboxes:
            self.bboxes[frame_index] = []
        self.bboxes[frame_index].append(bbox)
        self.auto_saver.save_frame(frame_index)
        
    def get_bboxes(self, frame_index: int) -> List[BoundingBox]:
        """フレームのBB取得"""
        return self.bboxes.get(frame_index, [])
        
class BoundingBox:
    """バウンディングボックス"""
    def __init__(self, x: float, y: float, w: float, h: float):
        self.x = x  # YOLO形式座標
        self.y = y
        self.w = w
        self.h = h
        self.individual_id = None
        self.action_id = None
        self.confidence = 1.0
        
    def to_yolo_format(self) -> str:
        """YOLO形式出力"""
        return f"{self.individual_id} {self.x} {self.y} {self.w} {self.h} {self.action_id} {self.confidence}"
```

### 4. 追跡モジュール実装
```python
class Tracker:
    """自動追跡アルゴリズム"""
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.similarity_calculator = SimilarityCalculator()
        
    def track_bbox(self, bbox: BoundingBox, start_frame: int, num_frames: int = 50):
        """BB追跡（デフォルト50フレーム）"""
        trajectory = []
        current_bbox = bbox
        
        for frame_idx in range(start_frame + 1, start_frame + num_frames + 1):
            next_frame = self.get_frame(frame_idx)
            if next_frame is None:
                break
                
            # 特徴量マッチング
            candidates = self.detect_candidates(next_frame, current_bbox)
            best_match = self.find_best_match(current_bbox, candidates)
            
            if best_match and best_match.confidence > 0.5:
                trajectory.append((frame_idx, best_match))
                current_bbox = best_match
            else:
                break  # 追跡失敗で終了
                
        return trajectory
```

## パフォーマンス最適化

### メモリ最適化
```python
# 1. 効率的なキャッシュ管理
class MemoryManager:
    def __init__(self, max_memory_gb: int = 20):
        self.max_memory = max_memory_gb * 1024 * 1024 * 1024
        
    def check_memory_usage(self):
        """メモリ使用量監視"""
        current = psutil.virtual_memory().used
        if current > self.max_memory * 0.8:
            self.cleanup_cache()
            
# 2. 画像データの軽量化
def resize_for_display(image: np.ndarray, scale: float = 0.5) -> np.ndarray:
    """表示用リサイズ（1/2サイズ）"""
    h, w = image.shape[:2]
    return cv2.resize(image, (int(w * scale), int(h * scale)))
```

### マルチスレッド処理
```python
import threading
from concurrent.futures import ThreadPoolExecutor

class AsyncImageLoader:
    """非同期画像読み込み"""
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    def load_frame_async(self, frame_index: int):
        """バックグラウンドでフレーム読み込み"""
        future = self.executor.submit(self._load_frame, frame_index)
        return future
        
    def preload_frames_async(self, center_index: int, radius: int = 100):
        """先読み処理をバックグラウンドで実行"""
        futures = []
        for i in range(center_index - radius, center_index + radius):
            future = self.executor.submit(self._load_frame, i)
            futures.append(future)
        return futures
```

## テスト要件

### 単体テスト
```python
# tests/test_video_processor.py
import pytest
from backend.video_processing_module.video_processor import VideoProcessor

class TestVideoProcessor:
    def test_load_video_success(self):
        """動画読み込み成功テスト"""
        processor = VideoProcessor()
        result = processor.load_video("test_video.mp4")
        assert result.frame_count > 0
        assert result.fps > 0
        
    def test_extract_frames_performance(self):
        """フレーム抽出性能テスト"""
        processor = VideoProcessor()
        start_time = time.time()
        processor.extract_frames("output/", target_fps=5.0)
        elapsed = time.time() - start_time
        assert elapsed < 60  # 1分以内での処理
```

### 統合テスト
```python
# tests/test_integration.py
def test_ui_video_integration():
    """UI-動画処理統合テスト"""
    app = MainApplication()
    app.load_video("test.mp4")
    app.display_frame(100)
    # フレーム表示が50ms以下で完了することを確認
```

## 他Agentとの連携

### test-design-agent →
- **テスト仕様**: 実装すべきテストケース
- **モック設計**: 依存関係の分離方法
- **パフォーマンス基準**: 応答時間・メモリ使用量の目標

### → testing-agent
- **実装コード**: テスト対象の実装
- **テスト環境**: テスト実行に必要な環境情報
- **パフォーマンスデータ**: 実際の性能測定結果

### ↔ frontend-agent
- **API仕様**: バックエンド-フロントエンド連携仕様
- **データ形式**: 受け渡しデータの形式
- **イベント**: UI イベントとバックエンド処理の連携

## チェックリスト

### 実装完了チェック
- [ ] UIモジュール実装完了
- [ ] 動画処理モジュール実装完了
- [ ] アノテーションモジュール実装完了
- [ ] 追跡モジュール実装完了
- [ ] パフォーマンス要件達成
- [ ] 単体テスト全件合格
- [ ] メモリ使用量20GB以内
- [ ] フレーム切り替え50ms以下達成