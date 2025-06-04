"""
Agent1 Presentation - ActionPanel
行動選択パネル（5行動・ボタンUI）

性能要件:
- 行動切り替え: 1ms以下
- 状態更新: 1ms以下
- 表示更新: リアルタイム

行動定義:
- 0: Sit (座る)
- 1: Stand (立つ)
- 2: Milk (授乳)
- 3: Water (水飲み)
- 4: Food (食事)
"""

import time
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QPushButton, QLabel, QFrame, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPalette, QFont, QIcon


class ActionButton(QPushButton):
    """行動ボタン（高速応答・視覚フィードバック）"""
    
    def __init__(self, action_id: int, action_name: str, color: QColor, parent=None):
        super().__init__(parent)
        self.action_id = action_id
        self.action_name = action_name
        self.action_color = color
        
        # ボタン設定
        self.setText(f"{action_id}: {action_name}")
        self.setFixedSize(120, 40)
        self.setCheckable(True)
        self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        # 初期色設定
        self.update_appearance()
        
    def update_appearance(self):
        """外観更新（1ms以下必達）"""
        start_time = time.perf_counter()
        
        try:
            if self.isChecked():
                # 選択時: 背景色、白文字
                style = f"""
                QPushButton {{
                    background-color: rgb({self.action_color.red()}, {self.action_color.green()}, {self.action_color.blue()});
                    color: white;
                    border: 2px solid black;
                    border-radius: 5px;
                    font-weight: bold;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    border: 3px solid black;
                }}
                """
            else:
                # 非選択時: 白背景、色ボーダー
                style = f"""
                QPushButton {{
                    background-color: white;
                    color: rgb({self.action_color.red()}, {self.action_color.green()}, {self.action_color.blue()});
                    border: 2px solid rgb({self.action_color.red()}, {self.action_color.green()}, {self.action_color.blue()});
                    border-radius: 5px;
                    font-weight: bold;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: rgb({min(255, self.action_color.red() + 40)}, {min(255, self.action_color.green() + 40)}, {min(255, self.action_color.blue() + 40)});
                }}
                """
                
            self.setStyleSheet(style)
            
        except Exception as e:
            print(f"Action button appearance update error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: Action button appearance update took {elapsed:.2f}ms (>1ms)")


class ActionPanel(QWidget):
    """
    行動選択パネル（5行動・ボタンUI）
    
    性能要件:
    - 行動切り替え: 1ms以下
    - 状態更新: 1ms以下
    - 表示更新: リアルタイム
    """
    
    # シグナル定義
    action_selected = pyqtSignal(int)  # 選択された行動ID
    
    # 5行動定義
    ACTIONS = {
        0: {"name": "Sit", "color": QColor(0, 150, 0), "description": "座る"},
        1: {"name": "Stand", "color": QColor(100, 100, 255), "description": "立つ"},
        2: {"name": "Milk", "color": QColor(255, 200, 100), "description": "授乳"},
        3: {"name": "Water", "color": QColor(0, 200, 255), "description": "水飲み"},
        4: {"name": "Food", "color": QColor(255, 100, 100), "description": "食事"},
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 状態管理
        self.selected_action = 0
        self.action_buttons: List[ActionButton] = []
        self.button_group = QButtonGroup()
        
        # 統計管理
        self.action_usage_count = {i: 0 for i in range(5)}
        self.last_selection_time = 0
        
        # UI構築
        self.setup_ui()
        self.setup_connections()
        
        # 初期選択
        self.select_action(0)
        
    def setup_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # タイトル
        title_label = QLabel("行動選択")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 行動ボタングリッド
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        button_layout = QVBoxLayout(button_frame)
        button_layout.setSpacing(3)
        
        # 5つの行動ボタン作成
        for action_id in range(5):
            action_config = self.ACTIONS[action_id]
            button = ActionButton(
                action_id, 
                action_config["name"], 
                action_config["color"]
            )
            button.clicked.connect(lambda checked, aid=action_id: self.on_action_button_clicked(aid))
            
            self.action_buttons.append(button)
            self.button_group.addButton(button, action_id)
            button_layout.addWidget(button)
            
        layout.addWidget(button_frame)
        
        # 選択情報表示
        self.info_label = QLabel("選択: 0 - Sit (座る)")
        self.info_label.setFont(QFont("Arial", 10))
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        # 使用統計表示
        self.stats_label = QLabel("使用統計: 各行動0回")
        self.stats_label.setFont(QFont("Arial", 9))
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)
        
        # 説明ラベル
        self.description_label = QLabel("BB作成時に使用される行動が選択されます")
        self.description_label.setFont(QFont("Arial", 8))
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        # スペーサー
        layout.addStretch()
        
    def setup_connections(self):
        """シグナル接続"""
        self.button_group.buttonClicked.connect(self.on_button_group_clicked)
        
    def on_action_button_clicked(self, action_id: int):
        """行動ボタンクリック処理（1ms以下必達）"""
        start_time = time.perf_counter()
        
        self.select_action(action_id)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: Action button click took {elapsed:.2f}ms (>1ms)")
            
        self.last_selection_time = elapsed
        
    def on_button_group_clicked(self, button: ActionButton):
        """ボタングループクリック処理"""
        if hasattr(button, 'action_id'):
            self.select_action(button.action_id)
            
    def select_action(self, action_id: int):
        """
        行動選択（1ms以下必達）
        
        Args:
            action_id: 選択する行動ID（0-4）
        """
        start_time = time.perf_counter()
        
        try:
            # 範囲チェック
            if not (0 <= action_id <= 4):
                return
                
            # 前回選択解除
            if 0 <= self.selected_action <= 4:
                self.action_buttons[self.selected_action].setChecked(False)
                self.action_buttons[self.selected_action].update_appearance()
                
            # 新しい選択設定
            self.selected_action = action_id
            self.action_buttons[action_id].setChecked(True)
            self.action_buttons[action_id].update_appearance()
            
            # 使用回数更新
            self.action_usage_count[action_id] += 1
            
            # 情報表示更新
            action_config = self.ACTIONS[action_id]
            self.info_label.setText(
                f"選択: {action_id} - {action_config['name']} ({action_config['description']})"
            )
            
            # 統計表示更新
            self._update_stats_display()
            
            # シグナル発出
            self.action_selected.emit(action_id)
            
        except Exception as e:
            print(f"Action selection error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: Action selection took {elapsed:.2f}ms (>1ms)")
            
    def _update_stats_display(self):
        """統計表示更新"""
        # 最も使用頻度の高い行動を特定
        most_used = max(self.action_usage_count, key=self.action_usage_count.get)
        total_uses = sum(self.action_usage_count.values())
        
        if total_uses > 0:
            most_used_name = self.ACTIONS[most_used]["name"]
            most_used_count = self.action_usage_count[most_used]
            self.stats_label.setText(
                f"使用統計: 総数{total_uses}回, 最多 {most_used_name}({most_used_count}回)"
            )
        else:
            self.stats_label.setText("使用統計: 各行動0回")
            
    def get_selected_action(self) -> int:
        """選択行動取得"""
        return self.selected_action
        
    def get_selected_action_name(self) -> str:
        """選択行動名取得"""
        return self.ACTIONS[self.selected_action]["name"]
        
    def get_selected_action_color(self) -> QColor:
        """選択行動色取得"""
        return self.ACTIONS[self.selected_action]["color"]
        
    def reset_usage_stats(self):
        """使用統計リセット"""
        self.action_usage_count = {i: 0 for i in range(5)}
        self._update_stats_display()
        
    def get_usage_stats(self) -> Dict[int, int]:
        """使用統計取得"""
        return self.action_usage_count.copy()
        
    def set_action_by_shortcut(self, shortcut_key: str) -> bool:
        """
        ショートカットキーによる行動選択
        
        Args:
            shortcut_key: ショートカットキー (1-5)
            
        Returns:
            bool: 選択成功フラグ
        """
        key_to_action = {
            '1': 0, '2': 1, '3': 2, '4': 3, '5': 4
        }
        
        if shortcut_key in key_to_action:
            self.select_action(key_to_action[shortcut_key])
            return True
        return False
        
    def get_performance_info(self) -> Dict[str, any]:
        """性能情報取得"""
        return {
            'selected_action': self.selected_action,
            'last_selection_time': self.last_selection_time,
            'button_count': len(self.action_buttons),
            'total_uses': sum(self.action_usage_count.values()),
            'usage_stats': self.action_usage_count,
            'target_performance': '1ms以下',
        }


if __name__ == "__main__":
    # ActionPanelテスト
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # ActionPanel作成
    action_panel = ActionPanel()
    action_panel.show()
    
    # 性能テスト
    print("ActionPanel Performance Test")
    print("=" * 30)
    
    # 行動選択性能テスト
    times = []
    for i in range(5):
        start_time = time.perf_counter()
        action_panel.select_action(i)
        elapsed = (time.perf_counter() - start_time) * 1000
        times.append(elapsed)
        
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    print(f"Action selection average time: {avg_time:.3f}ms")
    print(f"Action selection max time: {max_time:.3f}ms")
    print(f"Target: <1ms, Status: {'PASS' if avg_time < 1 else 'FAIL'}")
    
    # ショートカットテスト
    shortcut_times = []
    for key in ['1', '2', '3', '4', '5']:
        start_time = time.perf_counter()
        success = action_panel.set_action_by_shortcut(key)
        elapsed = (time.perf_counter() - start_time) * 1000
        if success:
            shortcut_times.append(elapsed)
            
    if shortcut_times:
        avg_shortcut_time = sum(shortcut_times) / len(shortcut_times)
        print(f"Shortcut selection average time: {avg_shortcut_time:.3f}ms")
        print(f"Shortcut selection status: {'PASS' if avg_shortcut_time < 1 else 'FAIL'}")
    
    # 性能情報表示
    perf_info = action_panel.get_performance_info()
    print("\nPerformance Info:")
    for key, value in perf_info.items():
        print(f"{key}: {value}")
        
    print("ActionPanel test completed")
    
    # アプリケーション実行（テスト用）
    # sys.exit(app.exec())