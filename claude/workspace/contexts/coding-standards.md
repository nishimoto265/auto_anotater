# コーディング規約

## 基本方針

### 品質優先
- **可読性**: 他の開発者が理解しやすいコード
- **保守性**: 変更・拡張しやすい構造
- **テスタビリティ**: テストしやすい設計
- **パフォーマンス**: 要件を満たす性能

### 一貫性
- **命名規則**: 統一された命名規則
- **コード構造**: 一貫したファイル・クラス構造
- **エラーハンドリング**: 統一されたエラー処理
- **ドキュメント**: 統一された文書化

## Python コーディング規約

### 基本規約
- **PEP 8**: Pythonの標準コーディング規約に準拠
- **行長**: 88文字以内（black formatter基準）
- **インデント**: スペース4文字
- **エンコーディング**: UTF-8

### 命名規則
```python
# クラス名: PascalCase
class VideoProcessor:
    pass

class FrameCache:
    pass

# 関数・変数名: snake_case
def load_video_file():
    pass

def get_frame_count():
    pass

frame_index = 0
bbox_list = []

# 定数: UPPER_SNAKE_CASE
MAX_CACHE_SIZE = 20480
DEFAULT_FPS = 5.0
SUPPORTED_FORMATS = ['.mp4', '.avi']

# プライベートメンバ: _で開始
class MyClass:
    def __init__(self):
        self._private_var = None
        self.__very_private = None
    
    def _private_method(self):
        pass
```

### ファイル・ディレクトリ構造
```python
# ファイル名: snake_case
video_processor.py
frame_cache.py
bbox_manager.py

# ディレクトリ名: kebab-case
ui-module/
video-processing-module/
annotation-module/

# パッケージ名: lowercase
backend/
frontend/
shared/
```

### インポート規則
```python
# 1. 標準ライブラリ
import os
import sys
import time
from typing import List, Dict, Optional

# 2. サードパーティライブラリ
import numpy as np
import cv2
from PyQt6.QtWidgets import QMainWindow

# 3. ローカルインポート
from backend.video_processing_module.video_processor import VideoProcessor
from shared.utils import validate_file_path

# 相対インポート（同一パッケージ内のみ）
from .frame_cache import FrameCache
from ..utils.validators import validate_bbox
```

### 型ヒント
```python
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path

# 関数の型ヒント
def load_video(video_path: str) -> Optional[VideoInfo]:
    """動画ファイルを読み込む"""
    pass

def get_frames(start: int, end: int) -> List[np.ndarray]:
    """指定範囲のフレームを取得"""
    pass

def process_bbox(bbox: BoundingBox) -> Dict[str, float]:
    """BBを処理してメトリクスを返す"""
    pass

# クラスの型ヒント
@dataclass
class BoundingBox:
    x: float
    y: float
    w: float
    h: float
    individual_id: Optional[int] = None
    action_id: Optional[str] = None
    confidence: float = 1.0

class VideoProcessor:
    def __init__(self, cache_size: int = 1024) -> None:
        self.cache_size = cache_size
        self._frames: Dict[int, np.ndarray] = {}
```

## クラス設計規約

### 単一責任原則
```python
# Good: 単一の責任を持つクラス
class VideoLoader:
    """動画ファイルの読み込みのみを担当"""
    def load_video(self, path: str) -> VideoInfo:
        pass

class FrameExtractor:
    """フレーム抽出のみを担当"""
    def extract_frame(self, video: VideoInfo, index: int) -> np.ndarray:
        pass

# Bad: 複数の責任を持つクラス
class VideoManager:
    """動画の読み込み、フレーム抽出、キャッシュ管理を全て担当（責任過多）"""
    def load_video(self, path: str): pass
    def extract_frame(self, index: int): pass
    def manage_cache(self): pass
```

### インターフェース分離
```python
from abc import ABC, abstractmethod

# インターフェースを細分化
class VideoReader(ABC):
    @abstractmethod
    def read_frame(self, index: int) -> np.ndarray:
        pass

class FrameCache(ABC):
    @abstractmethod
    def get_frame(self, index: int) -> Optional[np.ndarray]:
        pass
    
    @abstractmethod
    def store_frame(self, index: int, frame: np.ndarray) -> None:
        pass

# 具体実装
class OpenCVVideoReader(VideoReader):
    def read_frame(self, index: int) -> np.ndarray:
        # OpenCV実装
        pass

class LRUFrameCache(FrameCache):
    def get_frame(self, index: int) -> Optional[np.ndarray]:
        # LRU実装
        pass
```

### 依存性注入
```python
# Good: 依存性を注入
class VideoProcessor:
    def __init__(self, reader: VideoReader, cache: FrameCache):
        self.reader = reader
        self.cache = cache
    
    def get_frame(self, index: int) -> np.ndarray:
        cached = self.cache.get_frame(index)
        if cached is not None:
            return cached
        
        frame = self.reader.read_frame(index)
        self.cache.store_frame(index, frame)
        return frame

# Bad: 直接依存
class VideoProcessor:
    def __init__(self):
        self.reader = OpenCVVideoReader()  # 直接依存
        self.cache = LRUFrameCache()       # 直接依存
```

## エラーハンドリング

### 例外処理
```python
# カスタム例外の定義
class VideoProcessingError(Exception):
    """動画処理関連のエラー"""
    pass

class FrameNotFoundError(VideoProcessingError):
    """フレームが見つからない"""
    pass

class InvalidVideoFormatError(VideoProcessingError):
    """サポートされていない動画形式"""
    pass

# 例外処理の実装
def load_video(video_path: str) -> VideoInfo:
    """動画ファイルを読み込む"""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not _is_supported_format(video_path):
        raise InvalidVideoFormatError(f"Unsupported format: {video_path}")
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise VideoProcessingError(f"Failed to open video: {video_path}")
        
        return VideoInfo(
            path=video_path,
            frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            fps=cap.get(cv2.CAP_PROP_FPS)
        )
    except Exception as e:
        raise VideoProcessingError(f"Error loading video: {e}") from e
    finally:
        if 'cap' in locals():
            cap.release()

# エラーハンドリングの呼び出し側
try:
    video_info = load_video("sample.mp4")
except FileNotFoundError:
    logger.error("動画ファイルが存在しません")
except InvalidVideoFormatError:
    logger.error("サポートされていない動画形式です")
except VideoProcessingError as e:
    logger.error(f"動画処理エラー: {e}")
```

### ログ記録
```python
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ログ使用例
class VideoProcessor:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_video(self, path: str) -> VideoInfo:
        self.logger.info(f"Loading video: {path}")
        
        try:
            video_info = self._load_video_impl(path)
            self.logger.info(f"Video loaded successfully: {video_info.frame_count} frames")
            return video_info
        except Exception as e:
            self.logger.error(f"Failed to load video: {e}")
            raise
```

## パフォーマンス規約

### 効率的なコード
```python
# Good: 効率的な実装
def process_frames_batch(frames: List[np.ndarray]) -> List[np.ndarray]:
    """フレームをバッチ処理"""
    # NumPyのベクトル演算を活用
    frame_array = np.stack(frames)
    processed = cv2.blur(frame_array, (5, 5))  # バッチ処理
    return [processed[i] for i in range(len(processed))]

# Bad: 非効率な実装
def process_frames_slow(frames: List[np.ndarray]) -> List[np.ndarray]:
    """フレームを個別処理（非効率）"""
    result = []
    for frame in frames:
        # 個別処理（遅い）
        processed = cv2.blur(frame, (5, 5))
        result.append(processed)
    return result

# メモリ効率的な実装
def process_large_video(video_path: str, batch_size: int = 100):
    """大容量動画の効率的処理"""
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    for start_idx in range(0, frame_count, batch_size):
        end_idx = min(start_idx + batch_size, frame_count)
        
        # バッチ単位でフレームを処理
        batch_frames = []
        for i in range(start_idx, end_idx):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                batch_frames.append(frame)
        
        # バッチ処理
        processed_batch = process_frames_batch(batch_frames)
        
        # 結果を保存（メモリ解放）
        for i, processed_frame in enumerate(processed_batch):
            cv2.imwrite(f"output/{start_idx + i:06d}.jpg", processed_frame)
        
        # メモリ解放
        del batch_frames, processed_batch
    
    cap.release()
```

### マルチスレッド
```python
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

class AsyncFrameLoader:
    """非同期フレーム読み込み"""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.cache = {}
        self.cache_lock = threading.Lock()
    
    def load_frames_async(self, frame_indices: List[int]) -> None:
        """フレームを非同期で読み込み"""
        futures = []
        for index in frame_indices:
            future = self.executor.submit(self._load_single_frame, index)
            futures.append((index, future))
        
        # 完了したフレームをキャッシュに追加
        for index, future in futures:
            try:
                frame = future.result(timeout=5.0)
                with self.cache_lock:
                    self.cache[index] = frame
            except Exception as e:
                logger.error(f"Failed to load frame {index}: {e}")
    
    def _load_single_frame(self, index: int) -> np.ndarray:
        """単一フレーム読み込み（スレッドセーフ）"""
        # フレーム読み込み実装
        pass
```

## テスト規約

### ユニットテスト
```python
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

class TestVideoProcessor:
    """VideoProcessorのテストクラス"""
    
    @pytest.fixture
    def video_processor(self):
        """テスト用VideoProcessorインスタンス"""
        return VideoProcessor()
    
    @pytest.fixture
    def sample_frame(self):
        """テスト用フレームデータ"""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    def test_load_video_success(self, video_processor):
        """動画読み込み成功テスト"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap.return_value.isOpened.return_value = True
            mock_cap.return_value.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FRAME_COUNT: 1000,
                cv2.CAP_PROP_FPS: 30.0
            }[prop]
            
            result = video_processor.load_video("test.mp4")
            
            assert result.frame_count == 1000
            assert result.fps == 30.0
    
    def test_load_video_file_not_found(self, video_processor):
        """ファイル未存在エラーテスト"""
        with pytest.raises(FileNotFoundError):
            video_processor.load_video("nonexistent.mp4")
    
    def test_get_frame_from_cache(self, video_processor, sample_frame):
        """キャッシュからのフレーム取得テスト"""
        # キャッシュにフレームを設定
        video_processor.cache = {100: sample_frame}
        
        result = video_processor.get_frame(100)
        
        np.testing.assert_array_equal(result, sample_frame)
    
    @pytest.mark.parametrize("frame_index,expected", [
        (0, True),
        (999, True),
        (1000, False),
        (-1, False)
    ])
    def test_is_valid_frame_index(self, video_processor, frame_index, expected):
        """フレームインデックス検証テスト"""
        video_processor.frame_count = 1000
        assert video_processor.is_valid_frame_index(frame_index) == expected
```

### 統合テスト
```python
class TestUIVideoIntegration:
    """UI-動画処理統合テスト"""
    
    @pytest.fixture
    def main_window(self, qtbot):
        """メインウィンドウ"""
        window = MainWindow()
        qtbot.addWidget(window)
        return window
    
    def test_load_and_display_video(self, main_window, qtbot):
        """動画読み込みと表示の統合テスト"""
        # 動画読み込み
        main_window.load_video("tests/data/sample.mp4")
        
        # フレーム表示
        main_window.display_frame(100)
        
        # UI状態確認
        assert main_window.current_frame == 100
        assert main_window.frame_viewer.scene.items()  # 画像が表示されている
```

## ドキュメント規約

### docstring
```python
def get_frame(self, frame_index: int) -> Optional[np.ndarray]:
    """指定されたインデックスのフレームを取得する.
    
    Args:
        frame_index: 取得するフレームのインデックス（0以上）
        
    Returns:
        フレーム画像（HWC形式のnumpy配列）、取得できない場合はNone
        
    Raises:
        ValueError: frame_indexが負の値の場合
        FrameNotFoundError: 指定されたフレームが存在しない場合
        
    Examples:
        >>> processor = VideoProcessor()
        >>> processor.load_video("sample.mp4")
        >>> frame = processor.get_frame(100)
        >>> print(frame.shape)
        (480, 640, 3)
    """
    if frame_index < 0:
        raise ValueError("Frame index must be non-negative")
    
    # 実装...
```

### コメント
```python
class FrameCache:
    """フレームキャッシュの実装.
    
    LRU（Least Recently Used）アルゴリズムを使用して、
    メモリ使用量を制限しながら高速なフレーム取得を提供する。
    """
    
    def __init__(self, max_size_mb: int = 20480):
        # キャッシュサイズをMB単位で指定（デフォルト20GB）
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # LRU管理用のデータ構造
        self.cache = {}              # frame_index -> frame_data
        self.access_order = []       # アクセス順序のリスト
        self.current_size = 0        # 現在のキャッシュサイズ（バイト）
    
    def _update_access_order(self, frame_index: int) -> None:
        """アクセス順序を更新する（LRU管理）.
        
        最近アクセスされたフレームを先頭に移動する。
        """
        if frame_index in self.access_order:
            self.access_order.remove(frame_index)
        self.access_order.insert(0, frame_index)
    
    def _evict_old_frames(self) -> None:
        """古いフレームを削除してメモリを確保する."""
        while (self.current_size > self.max_size_bytes and 
               len(self.access_order) > 0):
            # 最も古いフレームを削除
            oldest_frame = self.access_order.pop()
            frame_data = self.cache.pop(oldest_frame)
            
            # メモリサイズを更新
            self.current_size -= frame_data.nbytes
```

## 品質チェック

### 自動チェック
```bash
# コードフォーマット
black implementation/src/
isort implementation/src/

# 静的解析
flake8 implementation/src/
mypy implementation/src/

# テスト実行
pytest testing/test-code/ --cov=implementation/src/ --cov-report=html

# セキュリティチェック
bandit -r implementation/src/
```

### コミット前チェック
```bash
#!/bin/bash
# scripts/pre_commit_check.sh

echo "=== Pre-commit checks ==="

# 1. Code formatting
echo "Checking code format..."
black --check implementation/src/
if [ $? -ne 0 ]; then
    echo "Code formatting failed. Run 'black implementation/src/' to fix."
    exit 1
fi

# 2. Static analysis
echo "Running static analysis..."
flake8 implementation/src/
if [ $? -ne 0 ]; then
    echo "Static analysis failed."
    exit 1
fi

# 3. Type checking
echo "Running type checks..."
mypy implementation/src/
if [ $? -ne 0 ]; then
    echo "Type checking failed."
    exit 1
fi

# 4. Unit tests
echo "Running unit tests..."
pytest testing/test-code/unit/
if [ $? -ne 0 ]; then
    echo "Unit tests failed."
    exit 1
fi

echo "All checks passed!"
```

この規約に従うことで、一貫性があり保守しやすい高品質なコードを作成できます。全Agentはこの規約を遵守してください。