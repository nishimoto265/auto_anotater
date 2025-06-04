"""
Agent1 Presentation - プロジェクト開始選択ダイアログ
動画・画像・既存プロジェクト選択画面
"""

import os
from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QGroupBox, QRadioButton, QLineEdit, QTextEdit,
    QFormLayout, QDialogButtonBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPalette


class ProjectStartupDialog(QDialog):
    """
    プロジェクト開始選択ダイアログ
    
    選択肢:
    1. 新規動画プロジェクト（mp4/avi）
    2. 画像フォルダプロジェクト（jpg/png）
    3. 既存プロジェクト読み込み
    """
    
    project_selected = pyqtSignal(str, str, dict)  # project_type, path, config
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fast Auto-Annotation System - プロジェクト選択")
        self.setModal(True)
        self.setFixedSize(800, 600)
        
        # 選択された情報
        self.selected_type = None
        self.selected_path = None
        self.project_config = {}
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("プロジェクトを選択してください")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # プロジェクト選択グループ
        self.create_project_selection_group(layout)
        
        # プロジェクト設定グループ
        self.create_project_config_group(layout)
        
        # ボタン群
        self.create_buttons(layout)
        
    def create_project_selection_group(self, parent_layout):
        """プロジェクト選択グループ作成"""
        group = QGroupBox("プロジェクトタイプ")
        layout = QVBoxLayout(group)
        
        # 新規動画プロジェクト
        self.video_radio = QRadioButton("新規動画プロジェクト（mp4/avi）")
        self.video_radio.setChecked(True)  # デフォルト選択
        layout.addWidget(self.video_radio)
        
        video_layout = QHBoxLayout()
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("動画ファイルを選択...")
        self.video_browse_btn = QPushButton("参照")
        video_layout.addWidget(self.video_path_edit)
        video_layout.addWidget(self.video_browse_btn)
        layout.addLayout(video_layout)
        
        # 画像フォルダプロジェクト
        self.image_radio = QRadioButton("画像フォルダプロジェクト（jpg/png）")
        layout.addWidget(self.image_radio)
        
        image_layout = QHBoxLayout()
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setPlaceholderText("画像フォルダを選択...")
        self.image_browse_btn = QPushButton("参照")
        image_layout.addWidget(self.image_path_edit)
        image_layout.addWidget(self.image_browse_btn)
        layout.addLayout(image_layout)
        
        # 既存プロジェクト読み込み
        self.existing_radio = QRadioButton("既存プロジェクト読み込み")
        layout.addWidget(self.existing_radio)
        
        existing_layout = QHBoxLayout()
        self.existing_path_edit = QLineEdit()
        self.existing_path_edit.setPlaceholderText("プロジェクトファイル（.json）を選択...")
        self.existing_browse_btn = QPushButton("参照")
        existing_layout.addWidget(self.existing_path_edit)
        existing_layout.addWidget(self.existing_browse_btn)
        layout.addLayout(existing_layout)
        
        parent_layout.addWidget(group)
        
    def create_project_config_group(self, parent_layout):
        """プロジェクト設定グループ作成"""
        group = QGroupBox("プロジェクト設定")
        layout = QFormLayout(group)
        
        # プロジェクト名
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("例: mouse_behavior_2024")
        layout.addRow("プロジェクト名:", self.project_name_edit)
        
        # 説明
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("プロジェクトの説明（オプション）")
        layout.addRow("説明:", self.description_edit)
        
        # 出力フレームレート（動画の場合）
        self.fps_edit = QLineEdit("5")
        self.fps_edit.setPlaceholderText("5")
        layout.addRow("出力FPS（動画のみ）:", self.fps_edit)
        
        parent_layout.addWidget(group)
        
    def create_buttons(self, parent_layout):
        """ボタン群作成"""
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("プロジェクト開始")
        self.ok_button.setEnabled(False)  # 初期状態では無効
        
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("キャンセル")
        
        parent_layout.addWidget(buttons)
        
        # ボタン接続
        buttons.accepted.connect(self.accept_project)
        buttons.rejected.connect(self.reject)
        
    def connect_signals(self):
        """シグナル接続"""
        # ラジオボタン変更
        self.video_radio.toggled.connect(self.on_project_type_changed)
        self.image_radio.toggled.connect(self.on_project_type_changed)
        self.existing_radio.toggled.connect(self.on_project_type_changed)
        
        # ファイル選択ボタン
        self.video_browse_btn.clicked.connect(self.browse_video_file)
        self.image_browse_btn.clicked.connect(self.browse_image_folder)
        self.existing_browse_btn.clicked.connect(self.browse_existing_project)
        
        # パス変更
        self.video_path_edit.textChanged.connect(self.validate_input)
        self.image_path_edit.textChanged.connect(self.validate_input)
        self.existing_path_edit.textChanged.connect(self.validate_input)
        self.project_name_edit.textChanged.connect(self.validate_input)
        
    def on_project_type_changed(self):
        """プロジェクトタイプ変更時の処理"""
        self.validate_input()
        
    def browse_video_file(self):
        """動画ファイル選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "動画ファイル選択",
            "",
            "動画ファイル (*.mp4 *.avi *.mov *.mkv);;すべてのファイル (*)"
        )
        
        if file_path:
            self.video_path_edit.setText(file_path)
            # プロジェクト名を動画ファイル名から自動生成
            if not self.project_name_edit.text():
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                self.project_name_edit.setText(f"{base_name}_annotation")
                
    def browse_image_folder(self):
        """画像フォルダ選択"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "画像フォルダ選択", ""
        )
        
        if folder_path:
            # フォルダ内に画像ファイルがあるか確認
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                for file in os.listdir(folder_path):
                    if file.lower().endswith(ext):
                        image_files.append(file)
                        
            if not image_files:
                QMessageBox.warning(
                    self, "警告", 
                    "選択されたフォルダに画像ファイル（jpg/png）が見つかりません。"
                )
                return
                
            self.image_path_edit.setText(folder_path)
            # プロジェクト名をフォルダ名から自動生成
            if not self.project_name_edit.text():
                folder_name = os.path.basename(folder_path)
                self.project_name_edit.setText(f"{folder_name}_annotation")
                
    def browse_existing_project(self):
        """既存プロジェクト選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "プロジェクトファイル選択",
            "",
            "プロジェクトファイル (*.json);;すべてのファイル (*)"
        )
        
        if file_path:
            self.existing_path_edit.setText(file_path)
            
    def validate_input(self):
        """入力値検証"""
        valid = False
        
        try:
            if self.video_radio.isChecked():
                # 動画プロジェクト
                video_path = self.video_path_edit.text().strip()
                project_name = self.project_name_edit.text().strip()
                valid = bool(video_path and project_name)
                        
            elif self.image_radio.isChecked():
                # 画像フォルダプロジェクト
                image_path = self.image_path_edit.text().strip()
                project_name = self.project_name_edit.text().strip()
                valid = bool(image_path and project_name)
                        
            elif self.existing_radio.isChecked():
                # 既存プロジェクト
                existing_path = self.existing_path_edit.text().strip()
                valid = bool(existing_path)
        except Exception:
            valid = False
                        
        self.ok_button.setEnabled(valid)
        
    def is_valid_video_file(self, file_path: str) -> bool:
        """動画ファイル検証"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        return any(file_path.lower().endswith(ext) for ext in video_extensions)
        
    def has_image_files(self, folder_path: str) -> bool:
        """画像ファイル存在確認"""
        try:
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            for file in os.listdir(folder_path):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    return True
            return False
        except OSError:
            return False
            
    def accept_project(self):
        """プロジェクト開始処理"""
        try:
            # 選択内容に基づいて設定作成
            if self.video_radio.isChecked():
                self.selected_type = "video"
                self.selected_path = self.video_path_edit.text().strip()
                self.project_config = {
                    "name": self.project_name_edit.text().strip(),
                    "description": self.description_edit.toPlainText().strip(),
                    "source_type": "video",
                    "source_path": self.selected_path,
                    "output_fps": int(self.fps_edit.text() or "5"),
                }
                
            elif self.image_radio.isChecked():
                self.selected_type = "images"
                self.selected_path = self.image_path_edit.text().strip()
                self.project_config = {
                    "name": self.project_name_edit.text().strip(),
                    "description": self.description_edit.toPlainText().strip(),
                    "source_type": "images",
                    "source_path": self.selected_path,
                }
                
            elif self.existing_radio.isChecked():
                self.selected_type = "existing"
                self.selected_path = self.existing_path_edit.text().strip()
                self.project_config = {
                    "source_type": "existing",
                    "project_path": self.selected_path,
                }
                
            # シグナル発信
            self.project_selected.emit(
                self.selected_type, 
                self.selected_path, 
                self.project_config
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "エラー", 
                f"プロジェクト開始中にエラーが発生しました:\n{str(e)}"
            )
            
    def get_project_info(self) -> Tuple[Optional[str], Optional[str], dict]:
        """選択されたプロジェクト情報取得"""
        return self.selected_type, self.selected_path, self.project_config


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = ProjectStartupDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        project_type, path, config = dialog.get_project_info()
        print(f"Selected: {project_type}, Path: {path}, Config: {config}")
    
    sys.exit()