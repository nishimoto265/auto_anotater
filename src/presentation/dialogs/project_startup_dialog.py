"""
Agent1 Presentation - プロジェクト開始選択ダイアログ
動画・画像・既存プロジェクト選択画面
"""

import os
from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QGroupBox, QRadioButton, QLineEdit, QTextEdit,
    QFormLayout, QDialogButtonBox, QMessageBox, QFrame,
    QListWidget, QListWidgetItem, QSpinBox, QCheckBox
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
    
    project_selected = pyqtSignal(str, object, dict)  # project_type, path(str or list), config
    
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
        
        # 動画選択コントロール
        video_controls_layout = QHBoxLayout()
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("動画ファイルを選択...")
        self.video_browse_btn = QPushButton("参照")
        self.multi_video_btn = QPushButton("複数選択")
        video_controls_layout.addWidget(self.video_path_edit)
        video_controls_layout.addWidget(self.video_browse_btn)
        video_controls_layout.addWidget(self.multi_video_btn)
        layout.addLayout(video_controls_layout)
        
        # 複数動画リスト
        self.video_list_widget = QListWidget()
        self.video_list_widget.setMaximumHeight(100)
        self.video_list_widget.setVisible(False)  # 初期状態では非表示
        layout.addWidget(self.video_list_widget)
        
        # 複数動画用コントロール
        multi_controls_layout = QHBoxLayout()
        self.remove_video_btn = QPushButton("削除")
        self.move_up_btn = QPushButton("↑ 上へ")
        self.move_down_btn = QPushButton("↓ 下へ")
        self.clear_videos_btn = QPushButton("クリア")
        multi_controls_layout.addWidget(self.remove_video_btn)
        multi_controls_layout.addWidget(self.move_up_btn)
        multi_controls_layout.addWidget(self.move_down_btn)
        multi_controls_layout.addWidget(self.clear_videos_btn)
        multi_controls_layout.addStretch()
        
        self.multi_controls_widget = QFrame()
        self.multi_controls_widget.setLayout(multi_controls_layout)
        self.multi_controls_widget.setVisible(False)  # 初期状態では非表示
        layout.addWidget(self.multi_controls_widget)
        
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
        
        # スタートフレーム番号
        self.start_frame_spin = QSpinBox()
        self.start_frame_spin.setMinimum(0)
        self.start_frame_spin.setMaximum(999999)
        self.start_frame_spin.setValue(0)
        self.start_frame_spin.setToolTip("最初のフレームの番号を指定（例: 300 → 000300.jpgから開始）")
        layout.addRow("スタートフレーム番号:", self.start_frame_spin)
        
        # 連結処理オプション（複数動画用）
        self.concatenate_videos_check = QCheckBox("複数動画を連結して処理")
        self.concatenate_videos_check.setToolTip("チェックすると、複数の動画を順番に連結して一つのフレームシーケンスとして処理")
        self.concatenate_videos_check.setVisible(False)  # 初期状態では非表示
        layout.addRow("連結オプション:", self.concatenate_videos_check)
        
        # 出力先ディレクトリ
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("出力先ディレクトリを選択...")
        self.output_browse_btn = QPushButton("参照")
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.output_browse_btn)
        layout.addRow("出力先ディレクトリ:", output_layout)
        
        # 既存プロジェクト用画像ディレクトリ（既存プロジェクト選択時のみ表示）
        self.existing_images_layout = QHBoxLayout()
        self.existing_images_edit = QLineEdit()
        self.existing_images_edit.setPlaceholderText("対応する画像ディレクトリを選択...")
        self.existing_images_browse_btn = QPushButton("参照")
        self.existing_images_layout.addWidget(self.existing_images_edit)
        self.existing_images_layout.addWidget(self.existing_images_browse_btn)
        self.existing_images_row = layout.addRow("画像ディレクトリ:", self.existing_images_layout)
        
        # 初期状態では非表示
        self.toggle_existing_images_visibility(False)
        
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
        self.multi_video_btn.clicked.connect(self.browse_multiple_videos)
        self.image_browse_btn.clicked.connect(self.browse_image_folder)
        self.existing_browse_btn.clicked.connect(self.browse_existing_project)
        
        # 複数動画制御ボタン
        self.remove_video_btn.clicked.connect(self.remove_selected_video)
        self.move_up_btn.clicked.connect(self.move_video_up)
        self.move_down_btn.clicked.connect(self.move_video_down)
        self.clear_videos_btn.clicked.connect(self.clear_video_list)
        
        # 出力ディレクトリ選択ボタン
        self.output_browse_btn.clicked.connect(self.browse_output_directory)
        self.existing_images_browse_btn.clicked.connect(self.browse_existing_images_directory)
        
        # パス変更
        self.video_path_edit.textChanged.connect(self.validate_input)
        self.image_path_edit.textChanged.connect(self.validate_input)
        self.existing_path_edit.textChanged.connect(self.validate_input)
        self.existing_images_edit.textChanged.connect(self.validate_input)
        self.project_name_edit.textChanged.connect(self.validate_input)
        self.output_dir_edit.textChanged.connect(self.validate_input)
        
    def on_project_type_changed(self):
        """プロジェクトタイプ変更時の処理"""
        # 既存プロジェクト選択時のみ画像ディレクトリ選択を表示
        self.toggle_existing_images_visibility(self.existing_radio.isChecked())
        
        # 動画プロジェクト選択時のみ複数動画関連UI表示
        self.toggle_multi_video_visibility(self.video_radio.isChecked())
        
        self.validate_input()
        
    def toggle_existing_images_visibility(self, visible: bool):
        """既存プロジェクト用画像ディレクトリの表示/非表示切り替え"""
        # レイアウト内のウィジェットの表示切り替え
        self.existing_images_edit.setVisible(visible)
        self.existing_images_browse_btn.setVisible(visible)
        
        # ラベルの表示切り替え（FormLayoutの場合）
        label_item = self.existing_images_row
        if hasattr(label_item, 'widget') and label_item.widget():
            label_item.widget().setVisible(visible)
            
    def toggle_multi_video_visibility(self, visible: bool):
        """複数動画関連UIの表示/非表示切り替え"""
        self.video_list_widget.setVisible(visible)
        self.multi_controls_widget.setVisible(visible)
        self.concatenate_videos_check.setVisible(visible)
        
        if visible:
            # 動画選択時はマルチ選択ボタンを表示
            self.multi_video_btn.setVisible(True)
        else:
            # 他のタイプ選択時はマルチ選択関連を非表示
            self.multi_video_btn.setVisible(False)
            self.clear_video_list()  # リストをクリア
        
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
                
    def browse_multiple_videos(self):
        """複数動画ファイル選択"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "動画ファイル選択（複数可）",
            "",
            "動画ファイル (*.mp4 *.avi *.mov *.mkv);;すべてのファイル (*)"
        )
        
        if file_paths:
            # 既存のリストに追加
            for file_path in file_paths:
                # 重複チェック
                existing_items = [self.video_list_widget.item(i).text() 
                                for i in range(self.video_list_widget.count())]
                if file_path not in existing_items:
                    self.video_list_widget.addItem(file_path)
            
            # プロジェクト名を最初の動画から自動生成（まだ設定されていない場合）
            if not self.project_name_edit.text() and file_paths:
                base_name = os.path.splitext(os.path.basename(file_paths[0]))[0]
                self.project_name_edit.setText(f"{base_name}_multi_annotation")
            
            # 単一選択欄をクリア（複数選択の場合）
            self.video_path_edit.clear()
            
            # 複数動画が選択された場合の表示更新
            self.update_video_selection_display()
            
    def remove_selected_video(self):
        """選択された動画をリストから削除"""
        current_row = self.video_list_widget.currentRow()
        if current_row >= 0:
            self.video_list_widget.takeItem(current_row)
            self.update_video_selection_display()
            
    def move_video_up(self):
        """選択された動画を上に移動"""
        current_row = self.video_list_widget.currentRow()
        if current_row > 0:
            item = self.video_list_widget.takeItem(current_row)
            self.video_list_widget.insertItem(current_row - 1, item)
            self.video_list_widget.setCurrentRow(current_row - 1)
            
    def move_video_down(self):
        """選択された動画を下に移動"""
        current_row = self.video_list_widget.currentRow()
        if current_row >= 0 and current_row < self.video_list_widget.count() - 1:
            item = self.video_list_widget.takeItem(current_row)
            self.video_list_widget.insertItem(current_row + 1, item)
            self.video_list_widget.setCurrentRow(current_row + 1)
            
    def clear_video_list(self):
        """動画リストをクリア"""
        self.video_list_widget.clear()
        self.update_video_selection_display()
        
    def update_video_selection_display(self):
        """動画選択表示の更新"""
        video_count = self.video_list_widget.count()
        if video_count > 0:
            # 複数動画が選択されている場合
            self.video_path_edit.setText(f"{video_count}個の動画が選択されています")
            self.video_path_edit.setReadOnly(True)
        else:
            # 動画が選択されていない場合
            self.video_path_edit.setText("")
            self.video_path_edit.setReadOnly(False)
            
        self.validate_input()
                
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
            # プロジェクトファイルからプロジェクト名を自動設定
            if not self.project_name_edit.text():
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                self.project_name_edit.setText(base_name)
            
    def validate_input(self):
        """入力値検証"""
        valid = False
        
        try:
            if self.video_radio.isChecked():
                # 動画プロジェクト
                project_name = self.project_name_edit.text().strip()
                
                # 単一動画または複数動画の選択確認
                single_video = self.video_path_edit.text().strip() and not self.video_path_edit.isReadOnly()
                multi_videos = self.video_list_widget.count() > 0
                
                valid = bool(project_name and (single_video or multi_videos))
                        
            elif self.image_radio.isChecked():
                # 画像フォルダプロジェクト
                image_path = self.image_path_edit.text().strip()
                project_name = self.project_name_edit.text().strip()
                valid = bool(image_path and project_name)
                        
            elif self.existing_radio.isChecked():
                # 既存プロジェクト
                existing_path = self.existing_path_edit.text().strip()
                existing_images = self.existing_images_edit.text().strip()
                valid = bool(existing_path and existing_images)
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
                
                # 複数動画または単一動画の処理
                if self.video_list_widget.count() > 0:
                    # 複数動画の場合
                    video_paths = []
                    for i in range(self.video_list_widget.count()):
                        video_paths.append(self.video_list_widget.item(i).text())
                    self.selected_path = video_paths  # リストとして保存
                    
                    self.project_config = {
                        "name": self.project_name_edit.text().strip(),
                        "description": self.description_edit.toPlainText().strip(),
                        "source_type": "multi_video",
                        "source_paths": video_paths,  # 複数パス
                        "output_fps": int(self.fps_edit.text() or "5"),
                        "output_directory": self.output_dir_edit.text().strip(),
                        "start_frame_number": self.start_frame_spin.value(),
                        "concatenate_videos": self.concatenate_videos_check.isChecked(),
                    }
                else:
                    # 単一動画の場合
                    self.selected_path = self.video_path_edit.text().strip()
                    
                    self.project_config = {
                        "name": self.project_name_edit.text().strip(),
                        "description": self.description_edit.toPlainText().strip(),
                        "source_type": "video",
                        "source_path": self.selected_path,
                        "output_fps": int(self.fps_edit.text() or "5"),
                        "output_directory": self.output_dir_edit.text().strip(),
                        "start_frame_number": self.start_frame_spin.value(),
                    }
                
            elif self.image_radio.isChecked():
                self.selected_type = "images"
                self.selected_path = self.image_path_edit.text().strip()
                self.project_config = {
                    "name": self.project_name_edit.text().strip(),
                    "description": self.description_edit.toPlainText().strip(),
                    "source_type": "images",
                    "source_path": self.selected_path,
                    "output_directory": self.output_dir_edit.text().strip(),
                }
                
            elif self.existing_radio.isChecked():
                self.selected_type = "existing"
                self.selected_path = self.existing_path_edit.text().strip()
                self.project_config = {
                    "source_type": "existing",
                    "project_path": self.selected_path,
                    "images_directory": self.existing_images_edit.text().strip(),
                    "output_directory": self.output_dir_edit.text().strip(),
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
            
    def browse_output_directory(self):
        """出力先ディレクトリ選択"""
        directory = QFileDialog.getExistingDirectory(
            self, "出力先ディレクトリ選択", ""
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            
    def browse_existing_images_directory(self):
        """既存プロジェクト用画像ディレクトリ選択"""
        directory = QFileDialog.getExistingDirectory(
            self, "画像ディレクトリ選択", ""
        )
        
        if directory:
            # ディレクトリ内に画像ファイルがあるか確認
            if self.has_image_files(directory):
                self.existing_images_edit.setText(directory)
            else:
                QMessageBox.warning(
                    self, "警告", 
                    "選択されたディレクトリに画像ファイル（jpg/png）が見つかりません。"
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