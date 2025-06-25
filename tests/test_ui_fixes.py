#!/usr/bin/env python3
"""
UI修正の回帰テストスイート
今回修正した問題が再発しないことを確認するテスト
"""

import sys
import os
import time
import pytest
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPixmap, QImage, QColor
from PyQt6.QtTest import QTest

from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
from presentation.main_window.main_window import MainWindow
from presentation.bb_canvas.canvas_widget import BBCanvas
from presentation.bb_canvas.bb_renderer import BBRenderer
from presentation.control_panels.bb_list_panel import BBListPanel


@pytest.fixture(scope="session")
def qapp():
    """QApplicationのフィクスチャ"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()


class TestProjectStartupDialog:
    """プロジェクト開始ダイアログのテスト"""
    
    def test_existing_project_image_directory_visibility(self, qapp):
        """
        既存プロジェクト選択時に画像ディレクトリ選択が表示されることを確認
        問題: 既存アノテーション選択時に画像ディレクトリ選択欄が表示されない
        """
        dialog = ProjectStartupDialog()
        dialog.show()
        
        # 初期状態（動画選択）では非表示
        assert dialog.video_radio.isChecked()
        assert not dialog.existing_images_container.isVisible()
        
        # 既存プロジェクトを選択
        dialog.existing_radio.setChecked(True)
        QTest.qWait(100)  # UIの更新を待つ
        
        # 画像ディレクトリ選択が表示される
        assert dialog.existing_radio.isChecked()
        assert dialog.existing_images_container.isVisible()
        assert dialog.existing_images_edit.isVisible()
        assert dialog.existing_images_browse_btn.isVisible()
        
        # 動画に戻すと非表示になる
        dialog.video_radio.setChecked(True)
        QTest.qWait(100)
        
        assert dialog.video_radio.isChecked()
        assert not dialog.existing_images_container.isVisible()
        
        dialog.close()
    
    def test_existing_project_layout_position(self, qapp):
        """
        画像ディレクトリ選択がアノテーションディレクトリの下に配置されることを確認
        問題: プロジェクト設定グループに配置されていた
        """
        dialog = ProjectStartupDialog()
        dialog.show()
        
        # 既存プロジェクトを選択
        dialog.existing_radio.setChecked(True)
        QTest.qWait(100)
        
        # レイアウト内の位置を確認
        # existing_path_editとexisting_images_editが同じ親（プロジェクト選択グループ）を持つ
        annotation_parent = dialog.existing_path_edit.parent().parent()
        images_parent = dialog.existing_images_container.parent()
        
        assert annotation_parent == images_parent
        
        dialog.close()
    
    def test_dialog_validation_with_existing_project(self, qapp):
        """
        既存プロジェクト選択時の入力検証が正しく動作することを確認
        """
        dialog = ProjectStartupDialog()
        dialog.show()
        
        # 既存プロジェクトを選択
        dialog.existing_radio.setChecked(True)
        QTest.qWait(100)
        
        # 初期状態ではOKボタンが無効
        assert not dialog.ok_button.isEnabled()
        
        # アノテーションディレクトリのみ設定
        dialog.existing_path_edit.setText("/path/to/annotations")
        QTest.qWait(100)
        assert not dialog.ok_button.isEnabled()
        
        # 画像ディレクトリも設定
        dialog.existing_images_edit.setText("/path/to/images")
        QTest.qWait(100)
        assert dialog.ok_button.isEnabled()
        
        dialog.close()


class TestBBCanvas:
    """BBキャンバスのテスト"""
    
    def test_bb_persistence_on_frame_switch(self, qapp):
        """
        フレーム切り替え時にBBが消えないことを確認
        問題: A/Dキーでフレーム移動時にBBが消える
        """
        canvas = BBCanvas()
        
        # テスト用画像を作成
        test_image1 = QImage(800, 600, QImage.Format.Format_RGB32)
        test_image1.fill(QColor(200, 200, 200))
        pixmap1 = QPixmap.fromImage(test_image1)
        
        test_image2 = QImage(800, 600, QImage.Format.Format_RGB32)
        test_image2.fill(QColor(220, 220, 220))
        pixmap2 = QPixmap.fromImage(test_image2)
        
        # 最初のフレームを表示
        canvas.display_frame(pixmap1)
        
        # BBを追加
        test_bbs = [
            {
                'id': 'test_bb_1',
                'x': 0.5,
                'y': 0.5,
                'w': 0.2,
                'h': 0.2,
                'individual_id': 0,
                'action_id': 0,
                'confidence': 0.95
            }
        ]
        canvas.update_bounding_boxes(test_bbs)
        
        # BBが描画されていることを確認
        assert len(canvas.current_bbs) == 1
        assert len(canvas.bb_renderer.rendered_items) == 1
        
        # フレームを切り替え
        canvas.display_frame(pixmap2)
        
        # 同じBBを再描画
        canvas.update_bounding_boxes(test_bbs)
        
        # BBが保持されていることを確認
        assert len(canvas.current_bbs) == 1
        assert len(canvas.bb_renderer.rendered_items) == 1
        assert canvas.scene.items()  # シーンにアイテムが存在
    
    def test_bb_text_size_and_content(self, qapp):
        """
        BBのテキストサイズと内容が正しいことを確認
        問題: BBと文字の大きさが小さい、行動がIDで表示されていた
        """
        renderer = BBRenderer()
        
        # テスト用BBエンティティ
        from dataclasses import dataclass
        
        @dataclass
        class TestBBEntity:
            id: str
            x: float
            y: float
            w: float
            h: float
            individual_id: int
            action_id: int
            confidence: float
            color: QColor
            
            def to_pixel_rect(self, width, height):
                from PyQt6.QtCore import QRectF
                px = self.x * width - (self.w * width) / 2
                py = self.y * height - (self.h * height) / 2
                pw = self.w * width
                ph = self.h * height
                return QRectF(px, py, pw, ph)
        
        bb_entity = TestBBEntity(
            id='test_bb',
            x=0.5, y=0.5, w=0.2, h=0.2,
            individual_id=0,
            action_id=1,  # Stand
            confidence=0.95,
            color=QColor(255, 0, 0)
        )
        
        # BBアイテムを作成
        item = renderer._create_bb_item(bb_entity, 800, 600)
        
        # ペンの幅が3であることを確認
        assert item.pen().width() == 3
        
        # テキストアイテムが存在し、正しい内容であることを確認
        assert item.text_item is not None
        assert "Stand" in item.text_item.toPlainText()
        assert "ID:0" in item.text_item.toPlainText()
        
        # フォントサイズが36であることを確認
        assert item.text_item.font().pointSize() == 36


class TestMainWindow:
    """メインウィンドウのテスト"""
    
    def test_s_key_deletion(self, qapp, tmpdir):
        """
        Sキーで実際にBBが削除されることを確認
        問題: Sキーを押しても削除されない
        """
        # テスト用の画像ディレクトリを作成
        image_dir = tmpdir.mkdir("images")
        test_image = QImage(800, 600, QImage.Format.Format_RGB32)
        test_image.fill(QColor(200, 200, 200))
        test_image.save(str(image_dir.join("000000.jpg")))
        
        # メインウィンドウを作成
        window = MainWindow()
        window.show()
        
        # 画像を読み込む
        window.load_images_directory(str(image_dir))
        QTest.qWait(100)
        
        # テスト用BBを追加
        test_bb = {
            'id': 'test_bb_delete',
            'x': 0.5,
            'y': 0.5,
            'w': 0.2,
            'h': 0.2,
            'individual_id': 0,
            'action_id': 0,
            'confidence': 0.95
        }
        window.current_annotations = [test_bb]
        window.canvas_widget.update_bounding_boxes(window.current_annotations)
        
        # BBを選択
        window.canvas_widget.selected_bb_id = 'test_bb_delete'
        
        # 削除前の確認
        assert len(window.current_annotations) == 1
        
        # Sキーをシミュレート
        from PyQt6.QtGui import QKeyEvent
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_S, Qt.KeyboardModifier.NoModifier)
        window.keyPressEvent(key_event)
        
        # 削除後の確認
        assert len(window.current_annotations) == 0
        
        window.close()
    
    def test_bb_list_panel_update(self, qapp, tmpdir):
        """
        BB一覧パネルが正しく更新されることを確認
        問題: BB一覧に何も表示されていない
        """
        # テスト用の画像ディレクトリを作成
        image_dir = tmpdir.mkdir("images")
        test_image = QImage(800, 600, QImage.Format.Format_RGB32)
        test_image.fill(QColor(200, 200, 200))
        test_image.save(str(image_dir.join("000000.jpg")))
        
        # メインウィンドウを作成
        window = MainWindow()
        window.show()
        
        # 画像を読み込む
        window.load_images_directory(str(image_dir))
        QTest.qWait(100)
        
        # テスト用BBを追加
        test_bbs = [
            {
                'id': 'bb_1',
                'x': 0.3,
                'y': 0.3,
                'w': 0.1,
                'h': 0.1,
                'individual_id': 0,
                'action_id': 0,
                'confidence': 0.95
            },
            {
                'id': 'bb_2',
                'x': 0.7,
                'y': 0.7,
                'w': 0.15,
                'h': 0.15,
                'individual_id': 1,
                'action_id': 2,
                'confidence': 0.88
            }
        ]
        
        window.current_annotations = test_bbs
        window.canvas_widget.update_bounding_boxes(window.current_annotations)
        window.update_bb_list_panel()
        
        # BB一覧パネルの確認
        assert window.bb_list_panel.rowCount() == 2
        
        # 各行の内容を確認
        item00 = window.bb_list_panel.item(0, 0)  # ID
        item01 = window.bb_list_panel.item(0, 1)  # Action
        assert item00.text() == "0"
        assert item01.text() == "Sit"
        
        item10 = window.bb_list_panel.item(1, 0)  # ID
        item11 = window.bb_list_panel.item(1, 1)  # Action
        assert item10.text() == "1"
        assert item11.text() == "Milk"
        
        window.close()


class TestZoomController:
    """ズームコントローラーのテスト"""
    
    def test_wheel_zoom_type_compatibility(self, qapp):
        """
        ホイールズームでQPointF/QPoint型の互換性が保たれることを確認
        問題: unsupported operand type(s) for -: 'QPointF' and 'QPoint'
        """
        canvas = BBCanvas()
        
        # テスト用画像を設定
        test_image = QImage(800, 600, QImage.Format.Format_RGB32)
        test_image.fill(QColor(200, 200, 200))
        pixmap = QPixmap.fromImage(test_image)
        canvas.display_frame(pixmap)
        
        # ホイールイベントをシミュレート
        from PyQt6.QtGui import QWheelEvent
        from PyQt6.QtCore import QPoint
        
        # 異なる型の組み合わせでテスト
        wheel_delta = QPoint(0, 120)  # 上方向スクロール
        pos = QPointF(400, 300)
        
        # エラーが発生しないことを確認
        try:
            event = QWheelEvent(
                pos,
                pos,
                wheel_delta,
                QPoint(0, 120),
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
                Qt.ScrollPhase.NoScrollPhase,
                False
            )
            canvas.wheelEvent(event)
            assert True  # エラーが発生しなければ成功
        except TypeError:
            pytest.fail("Type error in wheel zoom")


class TestBBListPanel:
    """BB一覧パネルのテスト"""
    
    def test_circular_reference_prevention(self, qapp):
        """
        BB選択時の循環参照が防止されることを確認
        問題: RecursionError: maximum recursion depth exceeded
        """
        panel = BBListPanel()
        
        # テスト用データを追加
        panel.update_bb_list([
            {'individual_id': 0, 'action_id': 0},
            {'individual_id': 1, 'action_id': 1}
        ])
        
        # 選択変更のカウンター
        selection_count = [0]
        
        def on_selection_changed(row):
            selection_count[0] += 1
            # 再帰的な選択を試みる
            if selection_count[0] < 10:  # 安全のため上限を設定
                panel.select_bb_by_row(0)
        
        panel.bb_selected.connect(on_selection_changed)
        
        # 選択を実行
        panel.select_bb_by_row(1)
        
        # 循環参照が防止され、無限ループにならないことを確認
        assert selection_count[0] < 10
        assert panel.currentRow() == 0  # 最終的に最初の行が選択される


class TestImportPaths:
    """インポートパスのテスト"""
    
    def test_no_src_prefix_imports(self):
        """
        'src.'プレフィックスなしでインポートできることを確認
        問題: ModuleNotFoundError: No module named 'src'
        """
        # main_window.pyからのインポートをテスト
        try:
            from presentation.main_window.main_window import MainWindow
            from presentation.dialogs.project_startup_dialog import ProjectStartupDialog
            from presentation.bb_canvas.canvas_widget import BBCanvas
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    # pytest実行
    pytest.main([__file__, "-v", "--tb=short"])