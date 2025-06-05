"""
Agent1 Presentation - MouseHandler
マウス操作処理（5ms以下応答）

機能:
- BBドラッグ作成
- BB選択・移動
- パン操作
- 高速レスポンス
"""

import time
from typing import Optional
from PyQt6.QtCore import QObject, QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QGraphicsView


class MouseHandler(QObject):
    """
    マウス操作処理
    
    性能要件:
    - マウス応答: 5ms以下
    - ドラッグ検知: 1ms以下
    - 選択処理: 1ms以下
    """
    
    # シグナル定義
    bb_drag_finished = pyqtSignal(QPointF, QPointF)  # start_pos, end_pos
    bb_selection_changed = pyqtSignal(str)  # bb_id
    pan_changed = pyqtSignal(QPointF)  # pan_offset
    
    def __init__(self, canvas: Optional[QGraphicsView] = None):
        super().__init__()
        self.canvas = canvas
        
        # マウス状態
        self.mouse_pressed = False
        self.drag_start_pos = QPointF()
        self.current_pos = QPointF()
        self.last_pos = QPointF()
        
        # 操作モード
        self.creation_mode = False
        self.pan_mode = False
        self.selection_mode = True
        
        # ドラッグ判定閾値
        self.drag_threshold = 5  # ピクセル
        
        # 性能測定
        self.last_mouse_time = 0
        
    def set_creation_mode(self, enabled: bool):
        """BB作成モード設定"""
        self.creation_mode = enabled
        self.selection_mode = not enabled
        
    def set_pan_mode(self, enabled: bool):
        """パンモード設定"""
        self.pan_mode = enabled
        
    def handle_mouse_press(self, position_or_event, button=None):
        """
        マウス押下処理（5ms以下必達）
        
        Args:
            position_or_event: QMouseEvent または QPoint
            button: Qt.MouseButton (QPointの場合のみ)
        """
        # オーバーロード対応：QPointとQMouseEventの両方をサポート
        if hasattr(position_or_event, 'position'):
            # QMouseEventの場合
            event = position_or_event
            return self._handle_mouse_press_event(event)
        else:
            # QPoint + Qt.MouseButtonの場合
            position = position_or_event
            return self._handle_mouse_press_point(position, button)
            
    def _handle_mouse_press_event(self, event: QMouseEvent):
        """マウスイベント版の処理"""
        start_time = time.perf_counter()
        
        try:
            self.mouse_pressed = True
            self.drag_start_pos = QPointF(event.position())
            self.current_pos = QPointF(event.position())
            self.last_pos = QPointF(event.position())
            
            # ボタン別処理
            if event.button() == Qt.MouseButton.LeftButton:
                self._handle_left_press(event)
            elif event.button() == Qt.MouseButton.RightButton:
                self._handle_right_press(event)
            elif event.button() == Qt.MouseButton.MiddleButton:
                self._handle_middle_press(event)
                
        except Exception as e:
            print(f"Mouse press error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Mouse press took {elapsed:.2f}ms (>5ms)")
            
        self.last_mouse_time = elapsed
        
    def _handle_mouse_press_point(self, position, button):
        """QPoint版の処理"""
        start_time = time.perf_counter()
        
        try:
            self.mouse_pressed = True
            self.drag_start_pos = QPointF(position)
            self.current_pos = QPointF(position)
            self.last_pos = QPointF(position)
            
            # ボタン別処理
            if button == Qt.MouseButton.LeftButton:
                if self.creation_mode:
                    pass  # BB作成開始
                elif self.selection_mode:
                    pass  # 選択処理
            elif button == Qt.MouseButton.RightButton:
                pass  # コンテキストメニュー
            elif button == Qt.MouseButton.MiddleButton:
                self.pan_mode = True
                
        except Exception as e:
            print(f"Mouse press (point) error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Mouse press (point) took {elapsed:.2f}ms (>5ms)")
            
        self.last_mouse_time = elapsed
        
    def handle_mouse_move(self, position_or_event):
        """
        マウス移動処理（5ms以下必達）
        
        Args:
            position_or_event: QMouseEvent または QPoint
        """
        # オーバーロード対応
        if hasattr(position_or_event, 'position'):
            # QMouseEventの場合
            event = position_or_event
            return self._handle_mouse_move_event(event)
        else:
            # QPointの場合
            position = position_or_event
            return self._handle_mouse_move_point(position)
            
    def _handle_mouse_move_event(self, event: QMouseEvent):
        """マウスイベント版の移動処理"""
        start_time = time.perf_counter()
        
        try:
            self.current_pos = QPointF(event.position())
            
            if self.mouse_pressed:
                if self.creation_mode:
                    self._handle_bb_drag(event)
                elif self.pan_mode:
                    self._handle_pan_drag(event)
                elif self.selection_mode:
                    self._handle_selection_drag(event)
                    
            self.last_pos = self.current_pos
            
        except Exception as e:
            print(f"Mouse move error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Mouse move took {elapsed:.2f}ms (>5ms)")
            
    def _handle_mouse_move_point(self, position):
        """QPoint版の移動処理"""
        start_time = time.perf_counter()
        
        try:
            self.current_pos = QPointF(position)
            
            if self.mouse_pressed:
                # ドラッグ処理
                delta = self.current_pos - self.last_pos
                if self.creation_mode:
                    pass  # BB作成ドラッグ
                elif self.pan_mode:
                    self.pan_changed.emit(delta)
                elif self.selection_mode:
                    pass  # 選択ドラッグ
                    
            self.last_pos = self.current_pos
            
        except Exception as e:
            print(f"Mouse move (point) error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Mouse move (point) took {elapsed:.2f}ms (>5ms)")
            
    def handle_mouse_release(self, position_or_event, button=None):
        """
        マウス離上処理（5ms以下必達）
        
        Args:
            position_or_event: QMouseEvent または QPoint
            button: Qt.MouseButton (QPointの場合のみ)
        """
        # オーバーロード対応
        if hasattr(position_or_event, 'position'):
            # QMouseEventの場合
            event = position_or_event
            return self._handle_mouse_release_event(event)
        else:
            # QPoint + Qt.MouseButtonの場合
            position = position_or_event
            return self._handle_mouse_release_point(position, button)
            
    def _handle_mouse_release_event(self, event: QMouseEvent):
        """マウスイベント版の離上処理"""
        start_time = time.perf_counter()
        
        try:
            if self.mouse_pressed:
                # ドラッグ終了処理
                if self.creation_mode and self._is_drag_gesture():
                    self.bb_drag_finished.emit(self.drag_start_pos, self.current_pos)
                elif self.selection_mode:
                    self._handle_selection_click(event)
                    
            self.mouse_pressed = False
            self.pan_mode = False
            
        except Exception as e:
            print(f"Mouse release error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Mouse release took {elapsed:.2f}ms (>5ms)")
            
    def _handle_mouse_release_point(self, position, button):
        """QPoint版の離上処理"""
        start_time = time.perf_counter()
        
        try:
            if self.mouse_pressed:
                self.current_pos = QPointF(position)
                
                # ドラッグ終了処理
                if self.creation_mode and self._is_drag_gesture():
                    self.bb_drag_finished.emit(self.drag_start_pos, self.current_pos)
                elif self.selection_mode and button == Qt.MouseButton.LeftButton:
                    # クリック選択処理
                    pass
                    
            self.mouse_pressed = False
            self.pan_mode = False
            
        except Exception as e:
            print(f"Mouse release (point) error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: Mouse release (point) took {elapsed:.2f}ms (>5ms)")
            
    def _handle_left_press(self, event: QMouseEvent):
        """左クリック処理"""
        if self.creation_mode:
            # BB作成開始
            pass
        elif self.selection_mode:
            # BB選択処理
            self._handle_bb_selection(event)
            
    def _handle_right_press(self, event: QMouseEvent):
        """右クリック処理"""
        # コンテキストメニュー等
        pass
        
    def _handle_middle_press(self, event: QMouseEvent):
        """中クリック処理（パン開始）"""
        self.pan_mode = True
        self.canvas.setCursor(Qt.CursorShape.ClosedHandCursor)
        
    def _handle_bb_drag(self, event: QMouseEvent):
        """BBドラッグ処理"""
        # ドラッグ中の視覚フィードバック
        # TODO: リアルタイム矩形描画
        pass
        
    def _handle_pan_drag(self, event: QMouseEvent):
        """パンドラッグ処理"""
        if self.pan_mode:
            delta = self.current_pos - self.last_pos
            
            # スクロールバー操作
            h_scroll = self.canvas.horizontalScrollBar()
            v_scroll = self.canvas.verticalScrollBar()
            
            h_scroll.setValue(h_scroll.value() - int(delta.x()))
            v_scroll.setValue(v_scroll.value() - int(delta.y()))
            
            self.pan_changed.emit(delta)
            
    def _handle_selection_drag(self, event: QMouseEvent):
        """選択ドラッグ処理"""
        # BB移動等
        pass
        
    def _handle_bb_selection(self, event: QMouseEvent):
        """BB選択処理（1ms以下必達）"""
        start_time = time.perf_counter()
        
        try:
            # シーン座標に変換
            scene_pos = self.canvas.mapToScene(event.position().toPoint())
            
            # シーンを取得
            scene = self.canvas.scene()
            if scene is None:
                return
            
            # アイテム検索
            item = scene.itemAt(scene_pos, self.canvas.transform())
            
            if item and hasattr(item, 'bb_entity'):
                bb_id = item.bb_entity.id
                self.bb_selection_changed.emit(bb_id)
            else:
                self.bb_selection_changed.emit("")  # 選択解除
                
        except Exception as e:
            print(f"BB selection error: {e}")
            import traceback
            traceback.print_exc()
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: BB selection took {elapsed:.2f}ms (>1ms)")
            
    def _handle_selection_click(self, event: QMouseEvent):
        """選択クリック処理"""
        if not self._is_drag_gesture():
            self._handle_bb_selection(event)
            
    def _is_drag_gesture(self) -> bool:
        """ドラッグジェスチャー判定"""
        distance = (self.current_pos - self.drag_start_pos)
        return (abs(distance.x()) > self.drag_threshold or 
                abs(distance.y()) > self.drag_threshold)
                
    def cancel_current_action(self):
        """現在アクションキャンセル"""
        self.mouse_pressed = False
        self.pan_mode = False
        self.canvas.setCursor(Qt.CursorShape.ArrowCursor)
        
    def get_mouse_performance_info(self) -> dict:
        """マウス性能情報取得"""
        return {
            'last_mouse_time': self.last_mouse_time,
            'creation_mode': self.creation_mode,
            'pan_mode': self.pan_mode,
            'selection_mode': self.selection_mode,
            'drag_threshold': self.drag_threshold,
            'target_performance': '5ms以下',
        }


if __name__ == "__main__":
    # マウスハンドラーテスト
    from PyQt6.QtWidgets import QApplication, QGraphicsView
    from PyQt6.QtCore import QTimer
    import sys
    
    app = QApplication(sys.argv)
    
    # テスト用キャンバス
    canvas = QGraphicsView()
    mouse_handler = MouseHandler(canvas)
    
    # パフォーマンステスト
    print("MouseHandler Performance Test")
    print("=" * 30)
    
    # テスト結果表示
    info = mouse_handler.get_mouse_performance_info()
    for key, value in info.items():
        print(f"{key}: {value}")
        
    print("\nMouseHandler created successfully")
    print("Target performance: 5ms以下")