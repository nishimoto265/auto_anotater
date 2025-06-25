#!/usr/bin/env python3
"""
BB可視性テスト - BBが実際に見えるかどうかを確認
"""

import sys
import os
sys.path.append('/media/thithilab/volume/auto_anotatation/src')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPen, QColor

def test_bb_visibility():
    """BB可視性テスト"""
    app = QApplication(sys.argv)
    
    print("=== BB Visibility Test ===")
    
    # メインウィンドウ作成（プロジェクト情報なし）
    from presentation.main_window.main_window import MainWindow
    
    main_window = MainWindow()
    
    # アノテーションディレクトリを手動設定
    main_window.annotation_output_dir = "/media/thithilab/volume/auto_anotatation/test_annotations"
    main_window.current_frame = 0
    
    # フレーム画像を手動読み込み
    frame_path = "/media/thithilab/volume/auto_anotatation/data/frames/000000.jpg"
    if os.path.exists(frame_path):
        success = main_window.bb_canvas.load_frame(frame_path)
        print(f"Frame loaded: {success}")
        
        # アノテーションを手動読み込み
        main_window.load_current_annotations()
        print(f"Loaded {len(main_window.current_annotations)} annotations")
        
        # BBを表示
        if main_window.current_annotations:
            main_window.bb_canvas.update_bounding_boxes(main_window.current_annotations)
            
            # BBリストパネルも更新
            if hasattr(main_window, 'bb_list_panel'):
                main_window.bb_list_panel.update_bb_list(main_window.current_annotations)
    
    # テスト用のボタンを追加
    test_widget = QWidget()
    test_layout = QVBoxLayout(test_widget)
    
    # シーン情報表示ボタン
    def show_scene_info():
        canvas = main_window.bb_canvas
        print(f"\n=== Scene Info ===")
        print(f"Scene rect: {canvas.scene.sceneRect()}")
        print(f"View rect: {canvas.rect()}")
        print(f"Transform: {canvas.transform()}")
        print(f"Zoom level: {canvas.zoom_controller.get_current_zoom()}")
        
        # すべてのアイテムの詳細情報
        for i, item in enumerate(canvas.scene.items()):
            if hasattr(item, 'bb_entity'):
                print(f"BB {i}: rect={item.rect()}, visible={item.isVisible()}, zValue={item.zValue()}")
                print(f"  Position: ({item.rect().x()}, {item.rect().y()})")
                print(f"  Size: {item.rect().width()}x{item.rect().height()}")
                print(f"  Pen: width={item.pen().width()}, color={item.pen().color().name()}")
    
    info_btn = QPushButton("Show Scene Info")
    info_btn.clicked.connect(show_scene_info)
    test_layout.addWidget(info_btn)
    
    # 手動でBBを追加するボタン
    def add_test_bb():
        print("\n=== Adding Test BB ===")
        canvas = main_window.bb_canvas
        
        # 大きな赤い矩形を画面中央に追加
        from PyQt6.QtWidgets import QGraphicsRectItem
        from PyQt6.QtCore import QRectF
        
        test_rect = QGraphicsRectItem(QRectF(500, 300, 400, 200))
        test_rect.setPen(QPen(QColor(255, 0, 0), 10))  # 太い赤線
        test_rect.setBrush(QColor(255, 0, 0, 100))  # 半透明赤
        test_rect.setZValue(100)  # 最前面
        
        canvas.scene.addItem(test_rect)
        canvas.viewport().update()
        print("Added large red test rectangle")
    
    test_bb_btn = QPushButton("Add Test BB")
    test_bb_btn.clicked.connect(add_test_bb)
    test_layout.addWidget(test_bb_btn)
    
    # ビューをリセットするボタン
    def reset_view():
        canvas = main_window.bb_canvas
        canvas.fitInView(canvas.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        canvas.viewport().update()
        print("View reset to fit scene")
    
    reset_btn = QPushButton("Reset View")
    reset_btn.clicked.connect(reset_view)
    test_layout.addWidget(reset_btn)
    
    # ズームアウトボタン
    def zoom_out():
        canvas = main_window.bb_canvas
        canvas.scale(0.5, 0.5)
        canvas.viewport().update()
        print("Zoomed out")
    
    zoom_out_btn = QPushButton("Zoom Out")
    zoom_out_btn.clicked.connect(zoom_out)
    test_layout.addWidget(zoom_out_btn)
    
    # ズームインボタン
    def zoom_in():
        canvas = main_window.bb_canvas
        canvas.scale(2.0, 2.0)
        canvas.viewport().update()
        print("Zoomed in")
    
    zoom_in_btn = QPushButton("Zoom In")
    zoom_in_btn.clicked.connect(zoom_in)
    test_layout.addWidget(zoom_in_btn)
    
    # テストウィジェットを右側に配置
    main_layout = main_window.centralWidget().layout()
    main_layout.addWidget(test_widget)
    
    main_window.show()
    
    # 2秒後に自動的に情報表示
    QTimer.singleShot(2000, show_scene_info)
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    test_bb_visibility()