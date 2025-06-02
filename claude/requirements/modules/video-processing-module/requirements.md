# Video Processing モジュール要件

## 1. 概要
動画ファイルの読み込み、フレーム抽出、形式変換を担当するモジュール。OpenCVを使用した高速処理を提供。

## 2. 機能要件

### 2.1 動画読み込み機能
- **対応形式**: mp4, avi（4K解像度対応）
- **メタデータ取得**: フレーム数、fps、解像度、時間長
- **エラーハンドリング**: 破損動画・非対応形式の検出

### 2.2 フレーム抽出機能
- **fps変換**: 30fps → 5fps変換
- **フレーム番号指定**: 任意フレームの直接取得
- **連続取得**: 指定範囲の連続フレーム取得
- **品質保持**: 無劣化でのフレーム抽出

### 2.3 画像変換機能
- **形式変換**: フレーム → jpg形式
- **リサイズ**: 表示用サイズ変換（1/2サイズ）
- **色空間**: RGB ↔ BGR変換
- **ファイル命名**: 6桁連番（000000.jpg～）

### 2.4 バッチ処理機能
- **複数動画**: 連続動画の一括処理
- **順番制御**: ユーザー指定順序での処理
- **番号継続**: 連続した番号での出力
- **進捗表示**: 処理進捗のリアルタイム表示

### 2.5 キャッシュ機能
- **先読み**: 前後100フレームの先読み
- **LRU管理**: 最近使用頻度による自動削除
- **メモリ制限**: 20GB上限でのキャッシュ管理
- **非同期読み込み**: バックグラウンドでの画像読み込み

## 3. 非機能要件

### 3.1 パフォーマンス
- **読み込み速度**: 200MB/秒以上
- **フレーム取得**: 10ms以下
- **変換速度**: リアルタイム変換（30fps以上）
- **メモリ効率**: 効率的なメモリ使用

### 3.2 品質
- **画質保持**: 無劣化フレーム抽出
- **精度**: 正確なフレーム番号対応
- **安定性**: 長時間動作での安定性
- **エラー回復**: 一時的エラーからの自動回復

### 3.3 スケーラビリティ
- **大容量対応**: 数GBファイルの処理
- **長時間動画**: 数時間動画の処理
- **メモリ制約**: 限られたメモリでの効率動作

## 4. インターフェース

### 4.1 API設計
```python
class VideoProcessor:
    def load_video(self, video_path: str) -> VideoInfo
    def get_frame(self, frame_index: int) -> np.ndarray
    def get_frame_range(self, start: int, end: int) -> List[np.ndarray]
    def extract_all_frames(self, output_dir: str) -> None
    def get_video_info(self) -> VideoInfo
    
class FrameCache:
    def get_cached_frame(self, frame_index: int) -> Optional[np.ndarray]
    def preload_frames(self, center_index: int, radius: int) -> None
    def clear_cache(self) -> None
    def get_cache_status(self) -> CacheStatus
    
class BatchProcessor:
    def add_video(self, video_path: str) -> None
    def set_output_directory(self, output_dir: str) -> None
    def start_processing(self) -> None
    def get_progress(self) -> ProcessProgress
```

### 4.2 データ構造
```python
@dataclass
class VideoInfo:
    path: str
    frame_count: int
    fps: float
    width: int
    height: int
    duration: float
    
@dataclass
class ProcessProgress:
    current_video: int
    total_videos: int
    current_frame: int
    total_frames: int
    elapsed_time: float
    estimated_remaining: float
    
@dataclass
class CacheStatus:
    used_memory: int
    cached_frames: int
    hit_ratio: float
    miss_count: int
```

### 4.3 設定パラメータ
```python
@dataclass
class VideoProcessingConfig:
    target_fps: float = 5.0
    output_format: str = "jpg"
    output_quality: int = 95
    cache_size_mb: int = 20480  # 20GB
    preload_frames: int = 100
    resize_factor: float = 0.5
    thread_count: int = 4
```

## 5. エラーハンドリング

### 5.1 ファイルエラー
- **ファイル不存在**: 適切なエラーメッセージと代替案提示
- **アクセス権限**: 権限不足時の対処法案内
- **破損ファイル**: 読み込み可能部分の部分処理

### 5.2 処理エラー
- **メモリ不足**: グレースフルデグラデーション
- **ディスク容量**: 容量不足警告と処理継続
- **ハードウェア**: GPU/CPU負荷制御

### 5.3 データエラー
- **フレーム取得失敗**: 前後フレームでの補完
- **解像度不一致**: 自動リサイズ・警告表示
- **フォーマット非対応**: 変換提案・代替処理

## 6. 最適化戦略

### 6.1 メモリ最適化
- **遅延読み込み**: 必要時のみフレーム読み込み
- **圧縮キャッシュ**: 軽量化されたキャッシュデータ
- **ガベージコレクション**: 定期的なメモリ解放

### 6.2 I/O最適化
- **シーケンシャル読み込み**: 連続アクセスの最適化
- **並列処理**: マルチスレッドでの並列読み込み
- **バッファリング**: 効率的なバッファ管理

### 6.3 CPU最適化
- **SIMD活用**: ベクトル演算の活用
- **並列化**: OpenCVの並列処理機能活用
- **キャッシュ効率**: CPUキャッシュ効率の向上

## 7. テスト要件

### 7.1 機能テスト
- **形式対応**: 各動画形式での動作確認
- **フレーム精度**: 正確なフレーム抽出の確認
- **大容量**: 大容量ファイルでの動作確認

### 7.2 パフォーマンステスト
- **読み込み速度**: 目標性能の達成確認
- **メモリ使用量**: メモリ制限内での動作確認
- **長時間動作**: 安定性の確認

### 7.3 エラーテスト
- **異常ファイル**: 破損・非対応ファイルでの動作
- **リソース不足**: 各種リソース不足での動作
- **割り込み**: 処理中断・復旧の確認

## 8. ドキュメント要件

### 8.1 API ドキュメント
- **関数仕様**: 全API関数の詳細仕様
- **使用例**: 典型的な使用パターンの例示
- **エラー**: エラーコードと対処法

### 8.2 設定ガイド
- **パラメータ**: 各設定項目の説明
- **最適化**: 環境別の最適設定
- **トラブルシューティング**: 問題対処法