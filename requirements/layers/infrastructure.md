# Agent4: Infrastructure Layer 詳細仕様書（技術基盤Agent）

## 🎯 Agent4 Infrastructure の使命
**外部リソース・技術基盤・OpenCV動画処理** - 高性能技術基盤提供

## 📋 Agent4開始時の必須確認項目

### 開発開始前チェックリスト
- [ ] CLAUDE.md読了（Agent4責任範囲確認）
- [ ] requirement.yaml確認（技術基盤要件理解）
- [ ] config/performance_targets.yaml確認（処理性能目標）
- [ ] config/layer_interfaces.yaml確認（Cache層連携重要）
- [ ] tests/requirements/unit/infrastructure-unit-tests.md確認（テスト要件）

### Agent4専門領域
```
責任範囲: 外部リソース・技術基盤・動画処理・システム最適化
技術領域: OpenCV、マルチスレッド、ファイルI/O、メモリ管理
実装場所: src/infrastructure/
テスト場所: tests/unit/test_infrastructure/
```

## 🏗️ 実装すべきコンポーネント詳細

### 1. video/ - 動画処理（OpenCV基盤）
```
src/infrastructure/video/
├── __init__.py
├── video_loader.py        # 動画読み込みエンジン
├── frame_extractor.py     # フレーム抽出エンジン
├── fps_converter.py       # FPS変換エンジン
└── format_handler.py      # 動画フォーマット処理
```

#### video_loader.py 仕様
```python
class VideoLoader:
    """
    動画読み込みエンジン
    
    性能要件:
    - 動画読み込み: 実速度（1秒動画/1秒処理）
    - 対応フォーマット: mp4, avi
    - 対応解像度: 4K (3840x2160)まで
    - メモリ効率: ストリーミング読み込み
    """
    
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi']
        
    def load_video(self, video_path: str) -> VideoMetadata:
        """
        動画読み込み（実速度必達）
        
        Args:
            video_path: 動画ファイルパス
            
        Returns:
            VideoMetadata: 動画メタデータ
        """
        if not self._is_supported_format(video_path):
            raise InfrastructureError(f"Unsupported format: {video_path}")
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise InfrastructureError(f"Cannot open video: {video_path}")
            
        metadata = VideoMetadata(
            path=video_path,
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=cap.get(cv2.CAP_PROP_FPS),
            frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            duration=cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
        )
        
        cap.release()
        return metadata
        
    def get_video_stream(self, video_path: str) -> cv2.VideoCapture:
        """動画ストリーム取得（メモリ効率重視）"""
        
    def _is_supported_format(self, video_path: str) -> bool:
        """対応フォーマット確認"""
        return any(video_path.lower().endswith(fmt) for fmt in self.supported_formats)
```

#### frame_extractor.py 仕様
```python
class FrameExtractor:
    """
    フレーム抽出エンジン
    
    性能要件:
    - フレーム変換: 30fps→5fps リアルタイム
    - 出力品質: jpg 90%品質
    - 並列処理: マルチスレッド活用
    - 進捗管理: リアルタイム進捗報告
    """
    
    def __init__(self, thread_count: int = 4):
        self.thread_count = thread_count
        self.thread_pool = ThreadPoolExecutor(max_workers=thread_count)
        
    def extract_frames(self, video_path: str, output_dir: str,
                      target_fps: int = 5, quality: int = 90,
                      progress_callback: Callable = None) -> FrameExtractionResult:
        """
        フレーム抽出（リアルタイム処理必達）
        
        Args:
            video_path: 入力動画パス
            output_dir: 出力ディレクトリ
            target_fps: 目標FPS（デフォルト5）
            quality: jpg品質（デフォルト90）
            progress_callback: 進捗コールバック
            
        Returns:
            FrameExtractionResult: 抽出結果
        """
        video_metadata = VideoLoader().load_video(video_path)
        fps_ratio = video_metadata.fps / target_fps
        
        cap = cv2.VideoCapture(video_path)
        frame_number = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # FPS変換（フレームスキップ）
            if frame_number % int(fps_ratio) == 0:
                output_path = os.path.join(output_dir, f"{extracted_count:06d}.jpg")
                self._save_frame_async(frame, output_path, quality)
                extracted_count += 1
                
                # 進捗報告
                if progress_callback:
                    progress = extracted_count / (video_metadata.frame_count / fps_ratio)
                    progress_callback(progress)
                    
            frame_number += 1
            
        cap.release()
        self.thread_pool.shutdown(wait=True)
        
        return FrameExtractionResult(
            total_frames=extracted_count,
            output_dir=output_dir,
            target_fps=target_fps,
            processing_time=time.time() - start_time
        )
        
    def _save_frame_async(self, frame: np.ndarray, output_path: str, quality: int):
        """非同期フレーム保存"""
        future = self.thread_pool.submit(self._save_frame, frame, output_path, quality)
        return future
        
    def _save_frame(self, frame: np.ndarray, output_path: str, quality: int):
        """フレーム保存（最適化済み）"""
        cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
```

### 2. image/ - 画像処理
```
src/infrastructure/image/
├── __init__.py
├── image_processor.py     # 画像処理エンジン
├── resize_engine.py       # リサイズエンジン
└── format_converter.py    # フォーマット変換
```

#### image_processor.py 仕様
```python
class ImageProcessor:
    """
    画像処理エンジン
    
    性能要件:
    - 4K→表示サイズ変換: 50ms以下
    - リサイズ処理: 高品質・高速
    - キャッシュ連携: Cache層との効率的連携
    - メモリ効率: 大容量画像対応
    """
    
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        
    def load_image(self, image_path: str) -> np.ndarray:
        """
        画像読み込み（50ms以下必達）
        
        Args:
            image_path: 画像ファイルパス
            
        Returns:
            np.ndarray: 画像データ
        """
        if not os.path.exists(image_path):
            raise InfrastructureError(f"Image not found: {image_path}")
            
        # OpenCV最適化フラグ使用
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            raise InfrastructureError(f"Cannot load image: {image_path}")
            
        return image
        
    def resize_for_display(self, image: np.ndarray, 
                          target_width: int, target_height: int,
                          maintain_aspect: bool = True) -> np.ndarray:
        """
        表示用リサイズ（50ms以下必達）
        
        Cache層連携用の高速リサイズ
        """
        if maintain_aspect:
            # アスペクト比維持リサイズ
            h, w = image.shape[:2]
            scale = min(target_width / w, target_height / h)
            new_w, new_h = int(w * scale), int(h * scale)
        else:
            new_w, new_h = target_width, target_height
            
        # OpenCV高速リサイズ（INTER_LINEAR使用）
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return resized
        
    def create_thumbnail(self, image: np.ndarray, size: int = 200) -> np.ndarray:
        """サムネイル生成（キャッシュ用）"""
        return self.resize_for_display(image, size, size, maintain_aspect=True)
        
    def optimize_for_cache(self, image: np.ndarray) -> np.ndarray:
        """Cache層最適化（メモリ効率・転送効率）"""
        # 必要に応じて圧縮・最適化
        return image
```

### 3. system/ - システム最適化
```
src/infrastructure/system/
├── __init__.py
├── file_system.py         # ファイルシステム最適化
├── memory_manager.py      # メモリ管理
└── thread_pool.py         # スレッドプール管理
```

#### memory_manager.py 仕様
```python
class MemoryManager:
    """
    メモリ管理（Cache層支援）
    
    機能:
    - メモリ使用量監視
    - ガベージコレクション最適化
    - メモリマップファイル管理
    - システムメモリ効率化
    """
    
    def __init__(self):
        self.memory_threshold = 20 * 1024 ** 3  # 20GB
        
    def get_memory_usage(self) -> MemoryUsage:
        """現在メモリ使用量取得"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return MemoryUsage(
            rss=memory_info.rss,  # 実使用メモリ
            vms=memory_info.vms,  # 仮想メモリ
            percent=process.memory_percent(),
            available=psutil.virtual_memory().available
        )
        
    def optimize_memory_usage(self):
        """メモリ使用量最適化"""
        # ガベージコレクション実行
        import gc
        gc.collect()
        
        # メモリ使用量確認
        current_usage = self.get_memory_usage()
        if current_usage.rss > self.memory_threshold:
            self._trigger_cache_cleanup()
            
    def _trigger_cache_cleanup(self):
        """Cache層にメモリクリーンアップ要求"""
        # Data Bus経由でCache層に通知
        pass
        
    def create_memory_mapped_file(self, file_path: str, size: int) -> mmap.mmap:
        """メモリマップファイル作成（大容量画像用）"""
        
    def monitor_memory_continuously(self, callback: Callable):
        """継続的メモリ監視"""
```

#### thread_pool.py 仕様
```python
class OptimizedThreadPool:
    """
    最適化スレッドプール
    
    最適化:
    - CPU集約処理用ThreadPoolExecutor
    - I/O集約処理用専用プール
    - 動的スレッド数調整
    - 優先度付きタスク処理
    """
    
    def __init__(self):
        self.cpu_pool = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())
        self.io_pool = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 2)
        self.priority_queue = PriorityQueue()
        
    def submit_cpu_task(self, func: Callable, *args, **kwargs) -> Future:
        """CPU集約タスク実行"""
        return self.cpu_pool.submit(func, *args, **kwargs)
        
    def submit_io_task(self, func: Callable, *args, **kwargs) -> Future:
        """I/O集約タスク実行"""
        return self.io_pool.submit(func, *args, **kwargs)
        
    def submit_priority_task(self, priority: int, func: Callable, 
                           *args, **kwargs) -> Future:
        """優先度付きタスク実行"""
        future = Future()
        self.priority_queue.put((priority, func, args, kwargs, future))
        return future
        
    def shutdown(self, wait: bool = True):
        """スレッドプールシャットダウン"""
        self.cpu_pool.shutdown(wait=wait)
        self.io_pool.shutdown(wait=wait)
```

## ⚡ パフォーマンス要件詳細

### 処理性能目標
```yaml
video_loading:
  target: "実速度（1秒動画/1秒処理）"
  formats: ["mp4", "avi"]
  resolutions: ["4K", "1080p"]
  
frame_conversion:
  target: "30fps→5fps リアルタイム"
  output_format: "jpg"
  quality: "90%"
  
image_processing:
  target: "4K→表示サイズ 50ms以下"
  sizes: ["1920x1080", "1280x720", "640x360"]
  optimization: "OpenCV最適化フラグ"
  
file_io:
  target: "SSD活用・並列処理"
  operations: ["jpg読み込み", "jpg保存"]
```

### OpenCV最適化
```python
# OpenCV最適化設定
cv2.setNumThreads(multiprocessing.cpu_count())
cv2.setUseOptimized(True)

class OpenCVOptimizer:
    """OpenCV最適化管理"""
    
    @staticmethod
    def configure_opencv():
        """OpenCV最適化設定"""
        # マルチスレッド有効化
        cv2.setNumThreads(-1)  # 自動設定
        cv2.setUseOptimized(True)
        
        # メモリ最適化
        cv2.setBufferAreaMaxSize(1024 * 1024 * 100)  # 100MB
        
    @staticmethod
    def get_optimal_interpolation(scale_factor: float) -> int:
        """スケールファクターに応じた最適補間方法"""
        if scale_factor > 1.0:
            return cv2.INTER_CUBIC  # 拡大
        elif scale_factor < 0.5:
            return cv2.INTER_AREA   # 大幅縮小
        else:
            return cv2.INTER_LINEAR # 通常縮小
```

## 🔗 他Agent連携インターフェース

### Cache層との連携（重要）
```python
class InfrastructureCacheInterface:
    """Infrastructure→Cache連携"""
    
    def provide_frame_data(self, frame_id: str) -> FrameData:
        """Cache層へのフレームデータ提供（45ms以下）"""
        
    def provide_optimized_image(self, image: np.ndarray, 
                              optimization_type: str) -> np.ndarray:
        """最適化画像提供"""
        
    def preload_frame_batch(self, frame_ids: List[str]):
        """フレーム一括先読み（バックグラウンド）"""
```

### Data Bus層との連携
```python
class InfrastructureDataBusInterface:
    """Infrastructure→Data Bus連携"""
    
    def report_processing_progress(self, operation: str, progress: float):
        """処理進捗報告"""
        
    def report_system_status(self, status: SystemStatus):
        """システム状態報告"""
        
    def request_memory_cleanup(self, urgency: str):
        """メモリクリーンアップ要求"""
```

## 🧪 テスト要件（TDD必須）

### 単体テスト必須項目
```python
# tests/unit/test_infrastructure/test_video_loader.py
class TestVideoLoader:
    def test_video_loading_real_time(self):
        """動画読み込み実速度確認"""
        
    def test_supported_formats(self):
        """対応フォーマット確認"""
        
    def test_4k_video_handling(self):
        """4K動画処理確認"""

# tests/unit/test_infrastructure/test_image_processor.py
class TestImageProcessor:
    def test_4k_resize_50ms(self):
        """4Kリサイズ50ms以下確認"""
        
    def test_image_quality_preservation(self):
        """画像品質保持確認"""
        
    def test_memory_efficiency(self):
        """メモリ効率確認"""

# tests/unit/test_infrastructure/test_frame_extractor.py
class TestFrameExtractor:
    def test_fps_conversion_real_time(self):
        """FPS変換リアルタイム確認"""
        
    def test_parallel_processing(self):
        """並列処理効率確認"""
```

### 統合テスト必須項目
```python
# tests/integration/test_infrastructure_integration.py
class TestInfrastructureIntegration:
    def test_cache_layer_communication(self):
        """Cache層連携確認"""
        
    def test_complete_video_processing_flow(self):
        """完全動画処理フロー確認"""
        
    def test_memory_management_integration(self):
        """メモリ管理統合確認"""
```

## 🛠️ 実装ガイドライン

### 必須技術スタック
```python
import cv2                 # OpenCV
import numpy as np         # 数値計算
import multiprocessing    # 並列処理
from concurrent.futures import ThreadPoolExecutor, Future
import psutil             # システム監視
import mmap              # メモリマップ
import os
import time
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass
```

### エラーハンドリング
```python
class InfrastructureError(Exception):
    """Infrastructure層エラー基底クラス"""
    
class VideoProcessingError(InfrastructureError):
    """動画処理エラー"""
    
class ImageProcessingError(InfrastructureError):
    """画像処理エラー"""
    
class SystemResourceError(InfrastructureError):
    """システムリソースエラー"""

def with_resource_monitoring(func):
    """リソース監視付きデコレータ"""
    def wrapper(*args, **kwargs):
        # リソース使用量監視
        start_time = time.time()
        start_memory = psutil.virtual_memory().used
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # リソース使用量記録
            end_time = time.time()
            end_memory = psutil.virtual_memory().used
            # 監視層に報告
            
    return wrapper
```

## ✅ Agent4完了条件

### 機能完了チェック
- [ ] 動画読み込み（mp4/avi対応）
- [ ] フレーム抽出（30fps→5fps変換）
- [ ] 画像処理（4K→表示サイズリサイズ）
- [ ] システム最適化（メモリ・スレッド管理）

### 性能完了チェック
- [ ] 動画読み込み実速度達成
- [ ] フレーム変換リアルタイム処理
- [ ] 4K画像処理50ms以下
- [ ] メモリ効率最適化

### テスト完了チェック
- [ ] 単体テスト100%通過
- [ ] 統合テスト100%通過
- [ ] 性能テスト100%通過
- [ ] Cache層連携テスト通過

---

**Agent4 Infrastructureは、高性能技術基盤を提供します。OpenCV活用による効率的動画・画像処理と、Cache層との密接な連携により、フレーム切り替え50ms以下の実現を技術的に支えます。**