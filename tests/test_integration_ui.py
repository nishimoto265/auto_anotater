#!/usr/bin/env python3
"""
UI統合テスト
実際の使用シナリオに基づいた統合テスト
"""

import sys
import os
import time
import pytest
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QColor, QKeyEvent
from PyQt6.QtTest import QTest

from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
from presentation.main_window.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """QApplicationのフィクスチャ"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()


class TestExistingProjectWorkflow:
    """既存プロジェクトワークフローの統合テスト"""
    
    def test_complete_existing_project_workflow(self, qapp, tmpdir):
        """
        既存プロジェクトの完全なワークフローをテスト
        1. ダイアログで既存プロジェクトを選択
        2. アノテーションと画像ディレクトリを指定
        3. プロジェクトを開始
        4. BBが正しく表示される
        """
        # テストデータの準備
        annotation_dir = tmpdir.mkdir("annotations")
        image_dir = tmpdir.mkdir("images")
        
        # テスト用画像を作成
        test_image = QImage(800, 600, QImage.Format.Format_RGB32)
        test_image.fill(QColor(200, 200, 200))
        test_image.save(str(image_dir.join("000000.jpg")))
        test_image.save(str(image_dir.join("000001.jpg")))
        
        # テスト用アノテーションを作成
        annotation_content = "0 0.5 0.5 0.2 0.2 0 0.95\n1 0.3 0.3 0.15 0.15 1 0.88"
        annotation_dir.join("000000.txt").write(annotation_content)
        annotation_dir.join("000001.txt").write("0 0.6 0.6 0.25 0.25 2 0.92")
        
        # ダイアログを開く
        dialog = ProjectStartupDialog()
        dialog.show()
        QTest.qWait(100)
        
        # 既存プロジェクトを選択
        dialog.existing_radio.setChecked(True)
        QTest.qWait(100)
        
        # 画像ディレクトリ選択が表示されることを確認
        assert dialog.existing_images_container.isVisible()
        
        # ディレクトリを設定
        dialog.existing_path_edit.setText(str(annotation_dir))
        dialog.existing_images_edit.setText(str(image_dir))
        QTest.qWait(100)
        
        # OKボタンが有効になることを確認
        assert dialog.ok_button.isEnabled()
        
        # プロジェクト情報を取得
        dialog.accept()
        project_type, path, config = dialog.get_project_info()
        
        assert project_type == "existing"
        assert config['annotations_directory'] == str(annotation_dir)
        assert config['images_directory'] == str(image_dir)
        
        dialog.close()


class TestFrameSwitchingWithAnnotations:
    """アノテーション付きフレーム切り替えテスト"""
    
    def test_frame_switching_preserves_annotations(self, qapp, tmpdir):
        """
        A/Dキーでフレーム切り替え時にアノテーションが保持されることをテスト
        """
        # テストデータの準備
        image_dir = tmpdir.mkdir("images")
        
        # 3つのテスト画像を作成
        for i in range(3):
            test_image = QImage(800, 600, QImage.Format.Format_RGB32)
            test_image.fill(QColor(200 + i * 10, 200 + i * 10, 200 + i * 10))
            test_image.save(str(image_dir.join(f"{i:06d}.jpg")))
        
        # メインウィンドウを作成
        window = MainWindow()
        window.show()
        QTest.qWait(100)
        
        # 画像ディレクトリを読み込む
        window.load_images_directory(str(image_dir))
        QTest.qWait(100)
        
        # 最初のフレームにアノテーションを追加
        window.current_annotations = [
            {
                'id': 'frame0_bb1',
                'x': 0.3,
                'y': 0.3,
                'w': 0.1,
                'h': 0.1,
                'individual_id': 0,
                'action_id': 0,  # Sit
                'confidence': 0.95
            }
        ]
        window.canvas_widget.update_bounding_boxes(window.current_annotations)
        window.update_bb_list_panel()
        
        # 初期状態の確認
        assert window.current_frame_index == 0
        assert len(window.canvas_widget.current_bbs) == 1
        assert window.bb_list_panel.rowCount() == 1
        
        # Dキーで次のフレームに移動
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_D, Qt.KeyboardModifier.NoModifier)
        window.keyPressEvent(key_event)
        QTest.qWait(100)
        
        # フレームが切り替わったことを確認
        assert window.current_frame_index == 1
        
        # 新しいフレームにアノテーションを追加
        window.current_annotations = [
            {
                'id': 'frame1_bb1',
                'x': 0.5,
                'y': 0.5,
                'w': 0.15,
                'h': 0.15,
                'individual_id': 1,
                'action_id': 1,  # Stand
                'confidence': 0.88
            }
        ]
        window.canvas_widget.update_bounding_boxes(window.current_annotations)
        window.update_bb_list_panel()
        
        # BBが表示されていることを確認
        assert len(window.canvas_widget.current_bbs) == 1
        assert len(window.canvas_widget.bb_renderer.rendered_items) == 1
        
        # Aキーで前のフレームに戻る
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        window.keyPressEvent(key_event)
        QTest.qWait(100)
        
        # 最初のフレームに戻ったことを確認
        assert window.current_frame_index == 0
        
        # 最初のフレームのアノテーションを再表示
        window.current_annotations = [
            {
                'id': 'frame0_bb1',
                'x': 0.3,
                'y': 0.3,
                'w': 0.1,
                'h': 0.1,
                'individual_id': 0,
                'action_id': 0,
                'confidence': 0.95
            }
        ]
        window.canvas_widget.update_bounding_boxes(window.current_annotations)
        
        # BBが正しく表示されていることを確認
        assert len(window.canvas_widget.current_bbs) == 1
        assert window.canvas_widget.current_bbs[0].action_id == 0
        
        window.close()


class TestBBDeletionAndDisplay:
    """BB削除と表示のテスト"""
    
    def test_bb_selection_and_deletion_workflow(self, qapp, tmpdir):
        """
        BB選択とS キーによる削除の完全なワークフローをテスト
        """
        # テストデータの準備
        image_dir = tmpdir.mkdir("images")
        test_image = QImage(800, 600, QImage.Format.Format_RGB32)
        test_image.fill(QColor(200, 200, 200))
        test_image.save(str(image_dir.join("000000.jpg")))
        
        # メインウィンドウを作成
        window = MainWindow()
        window.show()
        QTest.qWait(100)
        
        # 画像を読み込む
        window.load_images_directory(str(image_dir))
        QTest.qWait(100)
        
        # 複数のBBを追加
        window.current_annotations = [
            {
                'id': 'bb_1',
                'x': 0.3,
                'y': 0.3,
                'w': 0.1,
                'h': 0.1,
                'individual_id': 0,
                'action_id': 0,  # Sit
                'confidence': 0.95
            },
            {
                'id': 'bb_2',
                'x': 0.5,
                'y': 0.5,
                'w': 0.15,
                'h': 0.15,
                'individual_id': 1,
                'action_id': 1,  # Stand
                'confidence': 0.88
            },
            {
                'id': 'bb_3',
                'x': 0.7,
                'y': 0.7,
                'w': 0.12,
                'h': 0.12,
                'individual_id': 2,
                'action_id': 2,  # Milk
                'confidence': 0.92
            }
        ]
        window.canvas_widget.update_bounding_boxes(window.current_annotations)
        window.update_bb_list_panel()
        
        # 初期状態の確認
        assert len(window.current_annotations) == 3
        assert window.bb_list_panel.rowCount() == 3
        
        # BB一覧から2番目のBBを選択
        window.bb_list_panel.selectRow(1)
        QTest.qWait(100)
        
        # 選択されたBBの確認
        selected_bb = window.canvas_widget.get_selected_bb()
        assert selected_bb is not None
        assert selected_bb.individual_id == 1
        assert selected_bb.action_id == 1
        
        # Sキーで削除
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_S, Qt.KeyboardModifier.NoModifier)
        window.keyPressEvent(key_event)
        QTest.qWait(100)
        
        # 削除後の確認
        assert len(window.current_annotations) == 2
        assert window.bb_list_panel.rowCount() == 2
        
        # 削除されたBBが存在しないことを確認
        remaining_ids = [bb['individual_id'] for bb in window.current_annotations]
        assert 1 not in remaining_ids
        assert 0 in remaining_ids
        assert 2 in remaining_ids
        
        # BB一覧の表示内容を確認
        item00 = window.bb_list_panel.item(0, 1)  # Action
        item10 = window.bb_list_panel.item(1, 1)  # Action
        assert item00.text() == "Sit"
        assert item10.text() == "Milk"
        
        window.close()


class TestBBLabelDisplay:
    """BBラベル表示のテスト"""
    
    def test_bb_displays_action_names(self, qapp):
        """
        BBに行動名（Sit, Stand等）が表示されることをテスト
        問題: 行動IDの数字が表示されていた
        """
        canvas = BBCanvas()
        
        # テスト用画像
        test_image = QImage(800, 600, QImage.Format.Format_RGB32)
        test_image.fill(QColor(200, 200, 200))
        pixmap = QPixmap.fromImage(test_image)
        canvas.display_frame(pixmap)
        
        # 各行動タイプのBBを作成
        test_bbs = [
            {'id': 'bb_sit', 'x': 0.2, 'y': 0.2, 'w': 0.1, 'h': 0.1,
             'individual_id': 0, 'action_id': 0, 'confidence': 0.95},
            {'id': 'bb_stand', 'x': 0.4, 'y': 0.2, 'w': 0.1, 'h': 0.1,
             'individual_id': 1, 'action_id': 1, 'confidence': 0.95},
            {'id': 'bb_milk', 'x': 0.6, 'y': 0.2, 'w': 0.1, 'h': 0.1,
             'individual_id': 2, 'action_id': 2, 'confidence': 0.95},
            {'id': 'bb_water', 'x': 0.2, 'y': 0.4, 'w': 0.1, 'h': 0.1,
             'individual_id': 3, 'action_id': 3, 'confidence': 0.95},
            {'id': 'bb_food', 'x': 0.4, 'y': 0.4, 'w': 0.1, 'h': 0.1,
             'individual_id': 4, 'action_id': 4, 'confidence': 0.95},
        ]
        
        canvas.update_bounding_boxes(test_bbs)
        
        # 各BBのテキストラベルを確認
        action_names = ["Sit", "Stand", "Milk", "Water", "Food"]
        for i, item in enumerate(canvas.bb_renderer.rendered_items):
            if hasattr(item, 'text_item') and item.text_item:
                label_text = item.text_item.toPlainText()
                assert action_names[i] in label_text
                assert f"ID:{i}" in label_text


if __name__ == "__main__":
    # pytest実行
    pytest.main([__file__, "-v", "--tb=short"])