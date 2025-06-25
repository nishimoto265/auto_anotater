#!/usr/bin/env python3
"""
包括的テストスクリプト
すべての修正が正しく動作することを確認
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor

from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
# from presentation.main_window.main_window import AnnotationWindow
from presentation.bb_canvas.canvas_widget import BBCanvas

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comprehensive Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # メインウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # テストボタン
        button_layout = QHBoxLayout()
        
        # ダイアログテスト
        dialog_btn = QPushButton("1. Test Dialog (既存選択)")
        dialog_btn.clicked.connect(self.test_dialog)
        button_layout.addWidget(dialog_btn)
        
        # キャンバステスト
        canvas_btn = QPushButton("2. Test Canvas (BB描画)")
        canvas_btn.clicked.connect(self.test_canvas)
        button_layout.addWidget(canvas_btn)
        
        # フレーム切り替えテスト
        frame_btn = QPushButton("3. Test Frame Switch")
        frame_btn.clicked.connect(self.test_frame_switch)
        button_layout.addWidget(frame_btn)
        
        layout.addLayout(button_layout)
        
        # ステータスラベル
        self.status_label = QLabel("Ready for testing...")
        layout.addWidget(self.status_label)
        
        # キャンバス
        self.canvas = BBCanvas()
        layout.addWidget(self.canvas)
        
        # テスト用画像作成
        self.create_test_images()
        
    def create_test_images(self):
        """テスト用画像を作成"""
        self.test_images = []
        
        for i in range(3):
            # 800x600の画像を作成
            image = QImage(800, 600, QImage.Format.Format_RGB32)
            image.fill(QColor(200 + i*20, 200 + i*20, 200 + i*20))
            
            # フレーム番号を描画
            painter = QPainter(image)
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(painter.font())
            font = painter.font()
            font.setPointSize(48)
            painter.setFont(font)
            painter.drawText(350, 300, f"Frame {i}")
            painter.end()
            
            pixmap = QPixmap.fromImage(image)
            self.test_images.append(pixmap)
            
    def test_dialog(self):
        """ダイアログテスト - 既存選択時の画像ディレクトリ表示確認"""
        self.status_label.setText("Testing dialog...")
        
        dialog = ProjectStartupDialog(self)
        
        # 既存選択をプログラムで設定
        dialog.existing_radio.setChecked(True)
        
        # 変更をトリガー
        dialog.on_project_type_changed()
        
        # 確認
        print("\n=== Dialog Test Results ===")
        print(f"Existing radio checked: {dialog.existing_radio.isChecked()}")
        print(f"Row index exists: {hasattr(dialog, 'existing_images_row_index')}")
        if hasattr(dialog, 'existing_images_row_index'):
            print(f"Row index: {dialog.existing_images_row_index}")
        print(f"Edit visible: {dialog.existing_images_edit.isVisible()}")
        print(f"Browse button visible: {dialog.existing_images_browse_btn.isVisible()}")
        
        # FormLayoutの状態確認
        form_layout = None
        for child in dialog.existing_images_edit.parent().children():
            if hasattr(child, 'rowCount'):  # FormLayoutの特徴
                form_layout = child
                break
                
        if form_layout:
            print(f"FormLayout found with {form_layout.rowCount()} rows")
            
        self.status_label.setText("Dialog test: Check if image directory selection is visible")
        
        dialog.exec()
        
    def test_canvas(self):
        """キャンバステスト - BB描画確認"""
        self.status_label.setText("Testing canvas BB rendering...")
        
        # 最初の画像を表示
        self.canvas.display_frame(self.test_images[0])
        
        # テスト用BBを作成
        test_bbs = [
            {
                'id': 'bb_1',
                'x': 0.3,
                'y': 0.3,
                'w': 0.1,
                'h': 0.15,
                'individual_id': 0,
                'action_id': 0,  # Sit
                'confidence': 0.95
            },
            {
                'id': 'bb_2',
                'x': 0.7,
                'y': 0.7,
                'w': 0.12,
                'h': 0.18,
                'individual_id': 1,
                'action_id': 1,  # Stand
                'confidence': 0.88
            }
        ]
        
        # BB描画
        render_time = self.canvas.update_bounding_boxes(test_bbs)
        
        print(f"\n=== Canvas Test Results ===")
        print(f"BB render time: {render_time:.2f}ms")
        print(f"Number of BBs: {len(self.canvas.current_bbs)}")
        print(f"Renderer items: {len(self.canvas.bb_renderer.rendered_items)}")
        
        self.status_label.setText(f"Canvas test: Rendered {len(test_bbs)} BBs in {render_time:.2f}ms")
        
    def test_frame_switch(self):
        """フレーム切り替えテスト - BBが消えないことを確認"""
        self.status_label.setText("Testing frame switch with BBs...")
        
        # 最初のフレームとBBを設定
        self.current_frame = 0
        self.canvas.display_frame(self.test_images[0])
        
        # BBを設定
        test_bbs = [
            {
                'id': f'bb_frame_{self.current_frame}_1',
                'x': 0.5,
                'y': 0.5,
                'w': 0.2,
                'h': 0.2,
                'individual_id': self.current_frame,
                'action_id': self.current_frame % 5,
                'confidence': 0.9
            }
        ]
        self.canvas.update_bounding_boxes(test_bbs)
        
        # タイマーでフレーム切り替えをシミュレート
        self.switch_timer = QTimer()
        self.switch_timer.timeout.connect(self.switch_frame)
        self.switch_timer.start(1000)  # 1秒ごとに切り替え
        
        self.status_label.setText("Frame switching started - BBs should remain visible")
        
    def switch_frame(self):
        """フレーム切り替え処理"""
        # 次のフレームに切り替え
        self.current_frame = (self.current_frame + 1) % len(self.test_images)
        
        print(f"\n=== Switching to frame {self.current_frame} ===")
        
        # フレーム表示
        display_time = self.canvas.display_frame(self.test_images[self.current_frame])
        print(f"Frame display time: {display_time:.2f}ms")
        
        # 新しいBBを設定
        test_bbs = [
            {
                'id': f'bb_frame_{self.current_frame}_1',
                'x': 0.3 + self.current_frame * 0.1,
                'y': 0.3 + self.current_frame * 0.1,
                'w': 0.15,
                'h': 0.15,
                'individual_id': self.current_frame,
                'action_id': self.current_frame % 5,
                'confidence': 0.85 + self.current_frame * 0.05
            }
        ]
        
        # BB更新
        render_time = self.canvas.update_bounding_boxes(test_bbs)
        print(f"BB render time: {render_time:.2f}ms")
        print(f"Current BBs: {len(self.canvas.current_bbs)}")
        print(f"Rendered items: {len(self.canvas.bb_renderer.rendered_items)}")
        
        # シーン内のアイテム数を確認
        scene_items = self.canvas.scene.items()
        print(f"Scene items: {len(scene_items)}")
        
        self.status_label.setText(
            f"Frame {self.current_frame}: "
            f"Display={display_time:.1f}ms, "
            f"Render={render_time:.1f}ms, "
            f"BBs={len(self.canvas.current_bbs)}"
        )
        
        # 5フレーム後に停止
        if self.current_frame == 2 and hasattr(self, 'switch_count'):
            self.switch_timer.stop()
            self.status_label.setText("Frame switch test completed - Check if BBs remained visible")
            print("\n=== Frame Switch Test Complete ===")
            print("BBs should have remained visible throughout the test")
        
        if not hasattr(self, 'switch_count'):
            self.switch_count = 0
        self.switch_count += 1

def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("=== Comprehensive Test Started ===")
    print("1. Click 'Test Dialog' to check if image directory selection is visible")
    print("2. Click 'Test Canvas' to check BB rendering")
    print("3. Click 'Test Frame Switch' to check if BBs remain visible during frame changes")
    print("")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()