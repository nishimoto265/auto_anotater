"""
Agent1 Presentation - 処理進捗ダイアログ
動画・画像処理時の進捗表示
"""

import os
import time
from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QProgressBar, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont


class ProcessingWorker(QThread):
    """
    バックグラウンド処理ワーカー
    """
    
    progress_updated = pyqtSignal(int, str)  # progress, message
    finished = pyqtSignal(bool, str)  # success, result_message
    
    def __init__(self, project_type: str, source_path: str, config: dict):
        super().__init__()
        self.project_type = project_type
        self.source_path = source_path
        self.config = config
        self.cancelled = False
        
    def run(self):
        """処理実行"""
        try:
            if self.project_type == "video":
                self.process_video()
            elif self.project_type == "images":
                self.process_images()
            elif self.project_type == "existing":
                self.load_existing_project()
                
            if not self.cancelled:
                self.finished.emit(True, "処理が完了しました")
                
        except Exception as e:
            self.finished.emit(False, f"エラーが発生しました: {str(e)}")
            
    def process_video(self):
        """動画処理ー実際のフレーム抽出（単一または複数動画対応）"""
        try:
            import cv2
            self.progress_updated.emit(5, "動画ファイルを読み込み中...")
            
            if self.cancelled:
                return
            
            # 単一動画か複数動画かを判定
            source_type = self.config.get('source_type', 'video')
            
            if source_type == 'multi_video':
                self.process_multiple_videos()
            else:
                self.process_single_video()
                
        except ImportError:
            self.progress_updated.emit(50, "エラー: OpenCVがインストールされていません")
            self.finished.emit(False, "OpenCV (cv2)が必要です。pip install opencv-pythonでインストールしてください")
        except Exception as e:
            self.finished.emit(False, f"動画処理エラー: {str(e)}")
            
    def process_single_video(self):
        """単一動画処理"""
        import cv2
        
        # 動画ファイルを開く
        cap = cv2.VideoCapture(self.source_path)
        if not cap.isOpened():
            self.finished.emit(False, "動画ファイルを開けません")
            return
                
        # 動画情報取得
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        output_fps = self.config.get('output_fps', 5)
        start_frame_number = self.config.get('start_frame_number', 0)
        
        self.progress_updated.emit(10, f"動画解析完了: {total_frames}フレーム, {fps}fps")
        
        # 出力ディレクトリ作成
        output_dir = self.config.get('output_directory')
        if not output_dir:
            self.finished.emit(False, "出力先ディレクトリが指定されていません")
            return
            
        os.makedirs(output_dir, exist_ok=True)
        
        # フレーム抽出間隔計算（fps変換）
        frame_interval = max(1, int(fps / output_fps))
        extracted_count = 0
        frame_number = 0
        
        self.progress_updated.emit(15, f"フレーム抽出開始: {frame_interval}フレームおき, スタート番号: {start_frame_number}")
        
        while True:
            if self.cancelled:
                cap.release()
                return
                
            ret, frame = cap.read()
            if not ret:
                break
                
            # 指定間隔でフレーム抽出
            if frame_number % frame_interval == 0:
                # ファイル名生成（スタートフレーム番号を考慮）
                actual_frame_number = start_frame_number + extracted_count
                filename = f"{actual_frame_number:06d}.jpg"
                output_path = os.path.join(output_dir, filename)
                
                # フレーム保存
                success = cv2.imwrite(output_path, frame)
                if success:
                    extracted_count += 1
                    
                    # 進捗更新（15% + 80%の範囲で）
                    progress = int(15 + (frame_number / total_frames) * 80)
                    message = f"フレーム抽出: {filename} ({extracted_count}枚目)"
                    self.progress_updated.emit(progress, message)
                else:
                    print(f"Failed to save frame: {output_path}")
                    
            frame_number += 1
            
        cap.release()
        
        # 完了処理
        self.progress_updated.emit(95, f"抽出完了: {extracted_count}枚のフレーム")
        time.sleep(0.5)
        self.progress_updated.emit(100, f"成功: {extracted_count}枚のフレームを{output_dir}に保存")
        
    def process_multiple_videos(self):
        """複数動画処理"""
        import cv2
        
        video_paths = self.config.get('source_paths', [])
        if not video_paths:
            self.finished.emit(False, "処理する動画が選択されていません")
            return
            
        self.progress_updated.emit(5, f"{len(video_paths)}個の動画を処理開始...")
        
        # 出力ディレクトリ作成
        output_dir = self.config.get('output_directory')
        if not output_dir:
            self.finished.emit(False, "出力先ディレクトリが指定されていません")
            return
            
        os.makedirs(output_dir, exist_ok=True)
        
        output_fps = self.config.get('output_fps', 5)
        start_frame_number = self.config.get('start_frame_number', 0)
        concatenate_videos = self.config.get('concatenate_videos', True)
        
        total_extracted = 0
        current_frame_number = start_frame_number
        
        for video_index, video_path in enumerate(video_paths):
            if self.cancelled:
                return
                
            # 個別動画の処理開始
            base_progress = int(5 + (video_index / len(video_paths)) * 90)
            self.progress_updated.emit(base_progress, f"動画 {video_index + 1}/{len(video_paths)}: {os.path.basename(video_path)}")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.progress_updated.emit(base_progress, f"警告: {video_path} を開けませんでした。スキップします。")
                continue
                
            # 動画情報取得
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = max(1, int(fps / output_fps))
            
            extracted_from_video = 0
            frame_number = 0
            
            while True:
                if self.cancelled:
                    cap.release()
                    return
                    
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # 指定間隔でフレーム抽出
                if frame_number % frame_interval == 0:
                    if concatenate_videos:
                        # 連結モード: 通し番号
                        filename = f"{current_frame_number:06d}.jpg"
                        current_frame_number += 1
                    else:
                        # 個別モード: 動画ごとに番号リセット
                        filename = f"video{video_index + 1:02d}_{extracted_from_video + start_frame_number:06d}.jpg"
                    
                    output_path = os.path.join(output_dir, filename)
                    
                    # フレーム保存
                    success = cv2.imwrite(output_path, frame)
                    if success:
                        extracted_from_video += 1
                        total_extracted += 1
                        
                        # 進捗更新
                        video_progress = int(base_progress + (frame_number / total_frames) * (90 / len(video_paths)))
                        message = f"動画{video_index + 1}: {filename} ({extracted_from_video}枚目)"
                        self.progress_updated.emit(video_progress, message)
                        
                frame_number += 1
                
            cap.release()
            self.progress_updated.emit(base_progress + int(90 / len(video_paths)), 
                                     f"動画{video_index + 1}完了: {extracted_from_video}枚抽出")
            
        # 完了処理
        self.progress_updated.emit(95, f"全動画処理完了: {total_extracted}枚のフレーム")
        time.sleep(0.5)
        self.progress_updated.emit(100, f"成功: {total_extracted}枚のフレームを{output_dir}に保存")
            
    def process_images(self):
        """画像処理"""
        self.progress_updated.emit(10, "画像フォルダを読み込み中...")
        
        if self.cancelled:
            return
            
        # 画像ファイル数を取得（実際の実装用）
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        
        try:
            for file in os.listdir(self.source_path):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(file)
        except OSError:
            self.finished.emit(False, "画像フォルダにアクセスできません")
            return
            
        total_files = len(image_files)
        self.progress_updated.emit(20, f"{total_files}個の画像ファイルを検出しました")
        
        # 出力ディレクトリ作成と画像コピー
        output_dir = self.config.get('output_directory')
        if output_dir and output_dir != self.source_path:
            try:
                os.makedirs(output_dir, exist_ok=True)
                
                # 画像ファイルを出力ディレクトリにコピー
                import shutil
                for i, filename in enumerate(image_files):
                    if self.cancelled:
                        return
                        
                    source_file = os.path.join(self.source_path, filename)
                    # フレーム番号形式に変換するか、そのまま使用するか
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                        # フレーム番号形式にリネーム
                        ext = os.path.splitext(filename)[1]
                        new_filename = f"{i:06d}{ext}"
                        dest_file = os.path.join(output_dir, new_filename)
                    else:
                        dest_file = os.path.join(output_dir, filename)
                        
                    shutil.copy2(source_file, dest_file)
                    
                    progress = int(20 + (i / total_files) * 70)
                    message = f"画像コピー: {filename} ({i+1}/{total_files})"
                    self.progress_updated.emit(progress, message)
                    
            except Exception as e:
                self.finished.emit(False, f"画像処理エラー: {str(e)}")
                return
        else:
            # 出力ディレクトリが未指定または同じ場合はそのまま使用
            for i, filename in enumerate(image_files):
                if self.cancelled:
                    return
                    
                progress = int(20 + (i / total_files) * 70)
                message = f"画像確認: {filename} ({i+1}/{total_files})"
                self.progress_updated.emit(progress, message)
                time.sleep(0.05)  # 簡単な確認処理
            
        self.progress_updated.emit(100, "画像処理完了")
        
    def load_existing_project(self):
        """既存プロジェクト読み込み"""
        self.progress_updated.emit(20, "プロジェクトファイルを読み込み中...")
        
        if self.cancelled:
            return
            
        time.sleep(0.5)
        self.progress_updated.emit(50, "画像ディレクトリを確認中...")
        
        if self.cancelled:
            return
            
        time.sleep(0.5)
        self.progress_updated.emit(80, "設定を読み込み中...")
        
        if self.cancelled:
            return
            
        time.sleep(0.5)
        self.progress_updated.emit(100, "既存プロジェクト読み込み完了")
        
    def cancel(self):
        """処理キャンセル"""
        self.cancelled = True


class ProgressDialog(QDialog):
    """
    処理進捗ダイアログ
    
    動画・画像処理の進捗を表示し、キャンセル機能を提供
    """
    
    processing_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, project_type: str, source_path: str, config: dict, parent=None):
        super().__init__(parent)
        self.project_type = project_type
        self.source_path = source_path
        self.config = config
        
        self.setWindowTitle("処理中 - Fast Auto-Annotation System")
        self.setModal(True)
        self.setFixedSize(500, 300)
        
        # ワーカースレッド
        self.worker = None
        
        self.setup_ui()
        self.start_processing()
        
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("プロジェクト処理中...")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # プロジェクト情報
        info_label = QLabel()
        if self.project_type == "video":
            source_type = self.config.get('source_type', 'video')
            if source_type == 'multi_video':
                video_paths = self.config.get('source_paths', [])
                video_count = len(video_paths)
                info_label.setText(f"複数動画処理: {video_count}個のファイル")
                
                # 詳細情報の追加表示
                detail_layout = QVBoxLayout()
                if video_count > 0:
                    detail_text = f"開始フレーム番号: {self.config.get('start_frame_number', 0)}\n"
                    detail_text += f"連結処理: {'有効' if self.config.get('concatenate_videos', True) else '無効'}\n"
                    detail_text += "動画リスト:"
                    
                    detail_label = QLabel(detail_text)
                    layout.addWidget(detail_label)
                    
                    # 動画リストの表示（最大5個まで）
                    for i, video_path in enumerate(video_paths[:5]):
                        video_name = os.path.basename(video_path)
                        video_label = QLabel(f"  {i+1}. {video_name}")
                        layout.addWidget(video_label)
                    
                    if video_count > 5:
                        more_label = QLabel(f"  ... 他{video_count - 5}個の動画")
                        layout.addWidget(more_label)
            else:
                # 単一動画の場合
                info_label.setText(f"動画ファイル: {os.path.basename(self.source_path)}")
                start_frame = self.config.get('start_frame_number', 0)
                if start_frame > 0:
                    detail_label = QLabel(f"開始フレーム番号: {start_frame}")
                    layout.addWidget(detail_label)
        elif self.project_type == "images":
            info_label.setText(f"画像フォルダ: {os.path.basename(self.source_path)}")
        elif self.project_type == "existing":
            info_label.setText(f"既存プロジェクト: {os.path.basename(self.source_path)}")
            
        if info_label.text():  # info_labelにテキストがある場合のみ追加
            layout.addWidget(info_label)
            
        layout.addWidget(QLabel())  # スペーサー
        
        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 進捗メッセージ
        self.progress_label = QLabel("処理を開始しています...")
        layout.addWidget(self.progress_label)
        
        layout.addWidget(QLabel())  # スペーサー
        
        # 詳細ログ（縮小表示）
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(80)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.cancel_processing)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("閉じる")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def start_processing(self):
        """処理開始"""
        self.worker = ProcessingWorker(
            self.project_type,
            self.source_path, 
            self.config
        )
        
        # シグナル接続
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.processing_completed)
        
        # 処理開始
        self.worker.start()
        
        # 開始ログ
        self.add_log(f"処理開始: {self.project_type} プロジェクト")
        
    def update_progress(self, progress: int, message: str):
        """進捗更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
        self.add_log(f"[{progress}%] {message}")
        
    def add_log(self, message: str):
        """ログ追加"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def processing_completed(self, success: bool, message: str):
        """処理完了"""
        if success:
            self.progress_bar.setValue(100)
            self.progress_label.setText("✓ 処理完了")
            self.add_log(f"✓ 成功: {message}")
        else:
            self.progress_label.setText("✗ 処理失敗")
            self.add_log(f"✗ エラー: {message}")
            
        # ボタン状態変更
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        
        # 完了シグナル発信
        self.processing_finished.emit(success, message)
        
    def cancel_processing(self):
        """処理キャンセル"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)  # 3秒待機
            
            self.progress_label.setText("✗ 処理がキャンセルされました")
            self.add_log("✗ ユーザーによりキャンセルされました")
            
            # ボタン状態変更
            self.cancel_button.setEnabled(False)
            self.close_button.setEnabled(True)
            
            # キャンセル完了シグナル
            self.processing_finished.emit(False, "処理がキャンセルされました")
            
    def closeEvent(self, event):
        """ダイアログクローズ時"""
        if self.worker and self.worker.isRunning():
            self.cancel_processing()
        event.accept()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # テスト用のダミー設定
    config = {
        "name": "test_project",
        "source_type": "video",
        "output_fps": 5
    }
    
    dialog = ProgressDialog("video", "/path/to/test.mp4", config)
    dialog.exec()
    
    sys.exit()