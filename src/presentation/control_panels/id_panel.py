"""
Agent1 Presentation - IDPanel
個体ID選択パネル（0-15、色分け表示）

性能要件:
- ID切り替え: 1ms以下
- 色更新: 1ms以下
- 状態表示: リアルタイム
"""

import time
from typing import Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QPushButton, QLabel, QFrame, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPalette, QFont


class IDButton(QPushButton):
    """個体IDボタン（高速応答・色表示）"""
    
    def __init__(self, id_number: int, color: QColor, parent=None):
        super().__init__(parent)
        self.id_number = id_number
        self.id_color = color
        
        # ボタン設定
        self.setText(str(id_number))
        self.setFixedSize(40, 40)
        self.setCheckable(True)
        self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        # 色設定
        self.update_color()
        
    def update_color(self):
        """色更新（1ms以下必達）"""
        start_time = time.perf_counter()
        
        try:
            # 選択状態に応じた色設定
            if self.isChecked():
                # 選択時: 背景色、白文字
                style = f"""
                QPushButton {{
                    background-color: rgb({self.id_color.red()}, {self.id_color.green()}, {self.id_color.blue()});
                    color: white;
                    border: 2px solid black;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    border: 3px solid black;
                }}
                """
            else:
                # 非選択時: 白背景、色文字
                style = f"""
                QPushButton {{
                    background-color: white;
                    color: rgb({self.id_color.red()}, {self.id_color.green()}, {self.id_color.blue()});
                    border: 2px solid rgb({self.id_color.red()}, {self.id_color.green()}, {self.id_color.blue()});
                    border-radius: 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: rgb({min(255, self.id_color.red() + 30)}, {min(255, self.id_color.green() + 30)}, {min(255, self.id_color.blue() + 30)});
                }}
                """
                
            self.setStyleSheet(style)
            
        except Exception as e:
            print(f"ID button color update error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: ID button color update took {elapsed:.2f}ms (>1ms)")


class IDPanel(QWidget):
    """
    個体ID選択パネル（0-15、色分け表示）
    
    性能要件:
    - ID切り替え: 1ms以下
    - 色更新: 1ms以下
    - 状態表示: リアルタイム
    """
    
    # シグナル定義
    id_selected = pyqtSignal(int)  # 選択されたID
    
    # 16個体色定義（BBCanvasと同一）
    ID_COLORS = [
        QColor(255, 0, 0),    # 0: Red
        QColor(0, 255, 0),    # 1: Green
        QColor(0, 0, 255),    # 2: Blue
        QColor(255, 255, 0),  # 3: Yellow
        QColor(255, 0, 255),  # 4: Magenta
        QColor(0, 255, 255),  # 5: Cyan
        QColor(255, 128, 0),  # 6: Orange
        QColor(128, 0, 255),  # 7: Purple
        QColor(255, 192, 203),# 8: Pink
        QColor(165, 42, 42),  # 9: Brown
        QColor(128, 128, 128),# 10: Gray
        QColor(0, 128, 0),    # 11: Dark Green
        QColor(0, 0, 128),    # 12: Navy
        QColor(128, 128, 0),  # 13: Olive
        QColor(128, 0, 128),  # 14: Maroon
        QColor(0, 128, 128),  # 15: Teal
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 状態管理
        self.selected_id = 0
        self.id_buttons: List[IDButton] = []
        self.button_group = QButtonGroup()
        
        # 性能測定
        self.last_selection_time = 0
        
        # UI構築
        self.setup_ui()
        self.setup_connections()
        
        # 初期選択
        self.select_id(0)
        
    def setup_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # タイトル
        title_label = QLabel("個体ID選択")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # ID選択グリッド（4x4）
        grid_frame = QFrame()
        grid_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setSpacing(3)
        
        # 16個のIDボタン作成
        for i in range(16):
            row = i // 4
            col = i % 4
            
            button = IDButton(i, self.ID_COLORS[i])
            button.clicked.connect(lambda checked, id_num=i: self.on_id_button_clicked(id_num))
            
            self.id_buttons.append(button)
            self.button_group.addButton(button, i)
            grid_layout.addWidget(button, row, col)
            
        layout.addWidget(grid_frame)
        
        # 選択情報表示
        self.info_label = QLabel("選択: ID 0 (Red)")
        self.info_label.setFont(QFont("Arial", 10))
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        # 使用状況表示
        self.usage_label = QLabel("使用中: 0個体")
        self.usage_label.setFont(QFont("Arial", 9))
        self.usage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.usage_label)
        
        # スペーサー
        layout.addStretch()
        
    def setup_connections(self):
        """シグナル接続"""
        self.button_group.buttonClicked.connect(self.on_button_group_clicked)
        
    def on_id_button_clicked(self, id_number: int):
        """IDボタンクリック処理（1ms以下必達）"""
        start_time = time.perf_counter()
        
        self.select_id(id_number)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: ID button click took {elapsed:.2f}ms (>1ms)")
            
        self.last_selection_time = elapsed
        
    def on_button_group_clicked(self, button: IDButton):
        """ボタングループクリック処理"""
        if hasattr(button, 'id_number'):
            self.select_id(button.id_number)
            
    def select_id(self, id_number: int):
        """
        ID選択（1ms以下必達）
        
        Args:
            id_number: 選択するID（0-15）
        """
        start_time = time.perf_counter()
        
        try:
            # 範囲チェック
            if not (0 <= id_number <= 15):
                return
                
            # 前回選択解除
            if 0 <= self.selected_id <= 15:
                self.id_buttons[self.selected_id].setChecked(False)
                self.id_buttons[self.selected_id].update_color()
                
            # 新しい選択設定
            self.selected_id = id_number
            self.id_buttons[id_number].setChecked(True)
            self.id_buttons[id_number].update_color()
            
            # 情報表示更新
            color_name = self._get_color_name(id_number)
            self.info_label.setText(f"選択: ID {id_number} ({color_name})")
            
            # シグナル発出
            self.id_selected.emit(id_number)
            
        except Exception as e:
            print(f"ID selection error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: ID selection took {elapsed:.2f}ms (>1ms)")
            
    def update_id_colors(self, color_mapping: Dict[int, QColor]):
        """
        色マッピング更新（1ms以下必達）
        
        Args:
            color_mapping: IDごとの色マッピング
        """
        start_time = time.perf_counter()
        
        try:
            for id_number, color in color_mapping.items():
                if 0 <= id_number <= 15:
                    self.id_buttons[id_number].id_color = color
                    self.id_buttons[id_number].update_color()
                    
        except Exception as e:
            print(f"Color mapping update error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: Color mapping update took {elapsed:.2f}ms (>1ms)")
            
    def update_usage_info(self, used_ids: List[int]):
        """
        使用状況更新
        
        Args:
            used_ids: 使用中のIDリスト
        """
        try:
            # 全ボタンを非使用状態に
            for button in self.id_buttons:
                button.setEnabled(True)
                
            # 使用中IDを強調表示
            for id_number in used_ids:
                if 0 <= id_number <= 15:
                    # 使用中の視覚的表示は選択状態で表現
                    pass
                    
            # 使用状況ラベル更新
            self.usage_label.setText(f"使用中: {len(used_ids)}個体")
            
        except Exception as e:
            print(f"Usage info update error: {e}")
            
    def get_selected_id(self) -> int:
        """選択ID取得"""
        return self.selected_id
        
    def get_selected_color(self) -> QColor:
        """選択色取得"""
        return self.ID_COLORS[self.selected_id]
        
    def _get_color_name(self, id_number: int) -> str:
        """色名取得"""
        color_names = [
            "Red", "Green", "Blue", "Yellow", "Magenta", "Cyan", 
            "Orange", "Purple", "Pink", "Brown", "Gray", "Dark Green",
            "Navy", "Olive", "Maroon", "Teal"
        ]
        if 0 <= id_number < len(color_names):
            return color_names[id_number]
        return "Unknown"
        
    def get_performance_info(self) -> Dict[str, any]:
        """性能情報取得"""
        return {
            'selected_id': self.selected_id,
            'last_selection_time': self.last_selection_time,
            'button_count': len(self.id_buttons),
            'target_performance': '1ms以下',
        }


if __name__ == "__main__":
    # IDPanelテスト
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # IDPanel作成
    id_panel = IDPanel()
    id_panel.show()
    
    # 性能テスト
    print("IDPanel Performance Test")
    print("=" * 25)
    
    # ID選択性能テスト
    times = []
    for i in range(16):
        start_time = time.perf_counter()
        id_panel.select_id(i)
        elapsed = (time.perf_counter() - start_time) * 1000
        times.append(elapsed)
        
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    print(f"ID selection average time: {avg_time:.3f}ms")
    print(f"ID selection max time: {max_time:.3f}ms")
    print(f"Target: <1ms, Status: {'PASS' if avg_time < 1 else 'FAIL'}")
    
    # 性能情報表示
    perf_info = id_panel.get_performance_info()
    for key, value in perf_info.items():
        print(f"{key}: {value}")
        
    print("IDPanel test completed")
    
    # アプリケーション実行（テスト用）
    # sys.exit(app.exec())