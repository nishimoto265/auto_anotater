import sys
import cv2
import os
from PyQt6.QtWidgets import (QDialog, QFileDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QProgressBar, 
                            QListWidget, QMessageBox, QSpinBox, QCheckBox,
                            QListWidgetItem, QShortcut)
from PyQt6.QtCore import Qt, QTimer, QSize, QMimeData, QByteArray, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QKeySequence, QDrag, QImage

class StartupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("起動オプション選択")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.video_button = QPushButton("動画から開始")
        self.frames_button = QPushButton("フレームから開始")
        self.resume_button = QPushButton("前回の続きから")
        
        layout.addWidget(self.video_button)
        layout.addWidget(self.frames_button)
        layout.addWidget(self.resume_button)
        
        self.setLayout(layout)
        
        self.video_button.clicked.connect(lambda: self.done(1))
        self.frames_button.clicked.connect(lambda: self.done(2))
        self.resume_button.clicked.connect(lambda: self.done(3))

class VideoSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("動画選択と設定")
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # 説明ラベル
        info_label = QLabel("動画をドラッグ&ドロップで並べ替えできます")
        info_label.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(info_label)
        
        # 動画リスト（カスタマイズ版）
        self.video_list = DragDropListWidget()
        self.video_list.setIconSize(QSize(120, 90))
        self.video_list.setSpacing(5)
        self.video_list.itemMoved.connect(self.update_numbers)
        layout.addWidget(self.video_list)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        # 動画追加ボタン
        add_button = QPushButton("動画追加 (Ctrl+A)")
        add_button.clicked.connect(self.add_videos)
        button_layout.addWidget(add_button)
        
        # 削除ボタン
        remove_button = QPushButton("選択削除 (Delete)")
        remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(remove_button)
        
        # 全削除ボタン
        clear_button = QPushButton("全削除")
        clear_button.clicked.connect(self.clear_all)
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)
        
        # 開始番号設定
        number_layout = QHBoxLayout()
        number_layout.addWidget(QLabel("開始番号:"))
        self.start_number = QSpinBox()
        self.start_number.setRange(0, 999999)
        self.start_number.setFixedWidth(100)
        self.start_number.valueChanged.connect(self.update_numbers)
        number_layout.addWidget(self.start_number)
        number_layout.addStretch()
        layout.addLayout(number_layout)
        
        # 確定ボタン
        ok_button = QPushButton("確定")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        self.setLayout(layout)
        
        # キーボードショートカット設定
        self.setup_shortcuts()
        
        # ドラッグ&ドロップ受け入れ設定
        self.setAcceptDrops(True)
    
    def setup_shortcuts(self):
        # Ctrl+A: 動画追加
        QShortcut(QKeySequence("Ctrl+A"), self, self.add_videos)
        # Delete: 選択削除
        QShortcut(QKeySequence("Delete"), self, self.remove_selected)
        # Ctrl+Shift+Delete: 全削除
        QShortcut(QKeySequence("Ctrl+Shift+Delete"), self, self.clear_all)
        # 上下キー: 選択移動
        QShortcut(QKeySequence("Up"), self, lambda: self.move_selection(-1))
        QShortcut(QKeySequence("Down"), self, lambda: self.move_selection(1))
        # Ctrl+上下: アイテム移動
        QShortcut(QKeySequence("Ctrl+Up"), self, lambda: self.move_item(-1))
        QShortcut(QKeySequence("Ctrl+Down"), self, lambda: self.move_item(1))
    
    def add_videos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "動画ファイルを選択", "", "動画ファイル (*.mp4 *.avi *.mov *.mkv)"
        )
        for file_path in files:
            self.add_video_with_thumbnail(file_path)
        self.update_numbers()
    
    def add_video_with_thumbnail(self, file_path):
        # サムネイル生成
        thumbnail = self.generate_thumbnail(file_path)
        
        # リストアイテム作成
        item = QListWidgetItem()
        item.setSizeHint(QSize(550, 100))
        
        # ファイル名から番号を推定
        basename = os.path.basename(file_path)
        
        # アイコンとテキスト設定
        if thumbnail:
            item.setIcon(QIcon(thumbnail))
        
        item.setText(basename)
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        
        self.video_list.addItem(item)
    
    def generate_thumbnail(self, video_path):
        try:
            # 動画を開く
            cap = cv2.VideoCapture(video_path)
            
            # 最初のフレームを取得
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # リサイズ
                height, width = frame.shape[:2]
                aspect_ratio = width / height
                new_width = 120
                new_height = int(new_width / aspect_ratio)
                
                frame = cv2.resize(frame, (new_width, new_height))
                
                # BGRからRGBに変換
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # QPixmapに変換
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                
                # QImageを作成
                q_image = QImage(frame.data, width, height, bytes_per_line, 
                                QImage.Format.Format_RGB888)
                
                # QPixmapに変換
                pixmap = QPixmap.fromImage(q_image)
                
                return pixmap
        except Exception as e:
            print(f"サムネイル生成エラー: {e}")
        
        return None
    
    def update_numbers(self):
        """連番管理の更新"""
        start = self.start_number.value()
        for i in range(self.video_list.count()):
            item = self.video_list.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            basename = os.path.basename(file_path)
            item.setText(f"{start + i:06d}: {basename}")
    
    def remove_selected(self):
        """選択アイテムの削除"""
        for item in self.video_list.selectedItems():
            self.video_list.takeItem(self.video_list.row(item))
        self.update_numbers()
    
    def clear_all(self):
        """全アイテムの削除"""
        if confirm_dialog(self, "すべての動画を削除しますか？"):
            self.video_list.clear()
    
    def move_selection(self, direction):
        """選択を上下に移動"""
        current_row = self.video_list.currentRow()
        new_row = current_row + direction
        if 0 <= new_row < self.video_list.count():
            self.video_list.setCurrentRow(new_row)
    
    def move_item(self, direction):
        """アイテムを上下に移動"""
        current_row = self.video_list.currentRow()
        if current_row < 0:
            return
            
        new_row = current_row + direction
        if 0 <= new_row < self.video_list.count():
            item = self.video_list.takeItem(current_row)
            self.video_list.insertItem(new_row, item)
            self.video_list.setCurrentRow(new_row)
            self.update_numbers()
    
    def dragEnterEvent(self, event):
        """ドラッグエンターイベント"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """ドロップイベント"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.add_video_with_thumbnail(file_path)
        self.update_numbers()
    
    def get_video_paths(self):
        """動画パスのリストを取得"""
        paths = []
        for i in range(self.video_list.count()):
            item = self.video_list.item(i)
            paths.append(item.data(Qt.ItemDataRole.UserRole))
        return paths


class DragDropListWidget(QListWidget):
    """ドラッグ&ドロップ機能を拡張したリストウィジェット"""
    
    # カスタムシグナル
    itemMoved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
    
    def dropEvent(self, event):
        """ドロップイベントをオーバーライド"""
        super().dropEvent(event)
        # アイテムが移動したことを通知
        self.itemMoved.emit()

class OutputFolderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("フレーム出力先選択")
        
        layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        browse_button = QPushButton("参照...")
        browse_button.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)
        
        ok_button = QPushButton("確定")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        self.setLayout(layout)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "出力フォルダを選択")
        if folder:
            self.path_edit.setText(folder)

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("処理中...")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("処理中...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
    
    def update_progress(self, value, status=""):
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)

def show_error(parent, message, title="エラー"):
    QMessageBox.critical(parent, title, message)

def show_warning(parent, message, title="警告"):
    QMessageBox.warning(parent, title, message)

def show_info(parent, message, title="情報"):
    QMessageBox.information(parent, title, message)

def confirm_dialog(parent, message, title="確認"):
    reply = QMessageBox.question(parent, title, message,
                               QMessageBox.StandardButton.Yes | 
                               QMessageBox.StandardButton.No)
    return reply == QMessageBox.StandardButton.Yes