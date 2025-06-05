"""
Agent1 Presentation - BBListPanel
BB一覧表示・編集パネル（リスト・編集・10ms更新）

性能要件:
- リスト更新: 10ms以下
- 項目選択: 1ms以下
- 編集操作: 5ms以下
- 同期処理: リアルタイム
"""

import time
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QFrame, QPushButton, QHeaderView, QAbstractItemView,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush


class BBTableItem(QTableWidgetItem):
    """カスタムBBテーブルアイテム（高速更新・色表示）"""
    
    def __init__(self, text: str, bb_entity: Any = None):
        super().__init__(text)
        self.bb_entity = bb_entity
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def update_from_entity(self, bb_entity: Any):
        """エンティティから値更新（1ms以下）"""
        start_time = time.perf_counter()
        
        try:
            self.bb_entity = bb_entity
            # 色設定
            if hasattr(bb_entity, 'color'):
                brush = QBrush(bb_entity.color)
                self.setBackground(brush)
                
        except Exception as e:
            print(f"BB table item update error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: BB table item update took {elapsed:.2f}ms (>1ms)")


class BBListPanel(QTableWidget):
    """
    BB一覧表示・編集パネル
    
    性能要件:
    - リスト更新: 10ms以下
    - 項目選択: 1ms以下
    - 編集操作: 5ms以下
    """
    
    # シグナル定義
    bb_selected = pyqtSignal(str)  # 選択されたBB ID
    bb_edited = pyqtSignal(str, dict)  # 編集されたBB ID, 変更内容
    bb_deleted = pyqtSignal(str)  # 削除されたBB ID
    
    # テーブル列定義
    COLUMNS = {
        'ID': {'index': 0, 'width': 80, 'editable': False},
        'Individual': {'index': 1, 'width': 70, 'editable': True},
        'Action': {'index': 2, 'width': 70, 'editable': True},
        'X': {'index': 3, 'width': 60, 'editable': True},
        'Y': {'index': 4, 'width': 60, 'editable': True},
        'W': {'index': 5, 'width': 60, 'editable': True},
        'H': {'index': 6, 'width': 60, 'editable': True},
        'Conf': {'index': 7, 'width': 60, 'editable': False},
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 状態管理
        self.bb_entities: Dict[str, Any] = {}
        self.selected_bb_id: Optional[str] = None
        self.edit_mode = False
        
        # 性能統計
        self.update_count = 0
        self.total_update_time = 0
        self.last_update_time = 0
        
        # UI構築
        self.setup_table()
        self.setup_connections()
        
        # 更新タイマー（リアルタイム同期用）
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._check_for_updates)
        self.update_timer.start(100)  # 100ms間隔でチェック
        
    def setup_table(self):
        """テーブル初期化"""
        # 列設定
        column_names = list(self.COLUMNS.keys())
        self.setColumnCount(len(column_names))
        self.setHorizontalHeaderLabels(column_names)
        
        # 列幅設定
        header = self.horizontalHeader()
        for col_name, config in self.COLUMNS.items():
            self.setColumnWidth(config['index'], config['width'])
            
        # テーブル設定
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # ヘッダー設定
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # スタイル設定
        self.setFont(QFont("Arial", 9))
        self.setGridStyle(Qt.PenStyle.SolidLine)
        
    def setup_connections(self):
        """シグナル接続"""
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.itemChanged.connect(self.on_item_changed)
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
    def update_bb_list(self, bb_list: List[Any]) -> float:
        """
        BB一覧更新（10ms以下必達）
        
        Args:
            bb_list: BBエンティティリスト
            
        Returns:
            float: 更新時間（ms）
        """
        start_time = time.perf_counter()
        
        try:
            # 既存リストとの差分チェック
            new_bb_dict = {bb.id: bb for bb in bb_list}
            
            # 削除されたBBを特定
            removed_bb_ids = set(self.bb_entities.keys()) - set(new_bb_dict.keys())
            
            # 追加・更新されたBBを特定
            added_or_updated = {}
            for bb_id, bb in new_bb_dict.items():
                if bb_id not in self.bb_entities or self._bb_changed(bb, self.bb_entities.get(bb_id)):
                    added_or_updated[bb_id] = bb
                    
            # テーブル更新（差分のみ）
            if removed_bb_ids or added_or_updated:
                self._update_table_differential(removed_bb_ids, added_or_updated)
            
            # 状態更新
            self.bb_entities = new_bb_dict
            
        except Exception as e:
            print(f"BB list update error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        
        # 統計更新
        self.update_count += 1
        self.total_update_time += elapsed
        self.last_update_time = elapsed
        
        # 性能監視
        if elapsed > 10:
            print(f"WARNING: BB list update took {elapsed:.2f}ms (>10ms)")
            
        return elapsed
        
    def _bb_changed(self, bb1: Any, bb2: Any) -> bool:
        """BB変更チェック"""
        if bb2 is None:
            return True
        return (bb1.x != bb2.x or bb1.y != bb2.y or 
                bb1.w != bb2.w or bb1.h != bb2.h or
                bb1.individual_id != bb2.individual_id or
                bb1.action_id != bb2.action_id)
        
    def _update_table_differential(self, removed_ids: set, added_or_updated: Dict[str, Any]):
        """差分テーブル更新"""
        # 削除処理
        for bb_id in removed_ids:
            row = self._find_row_by_id(bb_id)
            if row >= 0:
                self.removeRow(row)
                
        # 追加・更新処理
        for bb_id, bb in added_or_updated.items():
            row = self._find_row_by_id(bb_id)
            if row >= 0:
                # 既存行更新
                self._update_row(row, bb)
            else:
                # 新規行追加
                self._add_row(bb)
                
    def _find_row_by_id(self, bb_id: str) -> int:
        """ID指定行検索"""
        for row in range(self.rowCount()):
            item = self.item(row, 0)  # ID列
            if item and item.text() == bb_id:
                return row
        return -1
        
    def _add_row(self, bb_entity: Any):
        """行追加"""
        row = self.rowCount()
        self.insertRow(row)
        self._update_row(row, bb_entity)
        
    def _update_row(self, row: int, bb_entity: Any):
        """行更新"""
        try:
            # ID列
            id_item = BBTableItem(bb_entity.id, bb_entity)
            if not self.COLUMNS['ID']['editable']:
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 0, id_item)
            
            # Individual列
            ind_item = BBTableItem(str(bb_entity.individual_id), bb_entity)
            self.setItem(row, 1, ind_item)
            
            # Action列
            action_item = BBTableItem(str(bb_entity.action_id), bb_entity)
            self.setItem(row, 2, action_item)
            
            # 座標列
            x_item = BBTableItem(f"{bb_entity.x:.3f}", bb_entity)
            y_item = BBTableItem(f"{bb_entity.y:.3f}", bb_entity)
            w_item = BBTableItem(f"{bb_entity.w:.3f}", bb_entity)
            h_item = BBTableItem(f"{bb_entity.h:.3f}", bb_entity)
            
            self.setItem(row, 3, x_item)
            self.setItem(row, 4, y_item)
            self.setItem(row, 5, w_item)
            self.setItem(row, 6, h_item)
            
            # 信頼度列
            conf_item = BBTableItem(f"{bb_entity.confidence:.2f}", bb_entity)
            if not self.COLUMNS['Conf']['editable']:
                conf_item.setFlags(conf_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 7, conf_item)
            
            # 色設定
            if hasattr(bb_entity, 'color'):
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    if item:
                        brush = QBrush(bb_entity.color)
                        brush.setStyle(Qt.BrushStyle.Dense7Pattern)
                        item.setBackground(brush)
                        
        except Exception as e:
            print(f"Row update error: {e}")
            
    def select_bb(self, bb_id: str) -> float:
        """
        BB選択（1ms以下必達）
        
        Args:
            bb_id: 選択するBB ID
            
        Returns:
            float: 選択時間（ms）
        """
        start_time = time.perf_counter()
        
        try:
            row = self._find_row_by_id(bb_id)
            if row >= 0:
                self.selectRow(row)
                self.selected_bb_id = bb_id
                self.bb_selected.emit(bb_id)
                
        except Exception as e:
            print(f"BB selection error: {e}")
            import traceback
            traceback.print_exc()
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 1:
            print(f"WARNING: BB selection took {elapsed:.2f}ms (>1ms)")
            
        return elapsed
        
    def edit_bb_properties(self, bb_id: str, properties: dict) -> float:
        """
        BBプロパティ編集（5ms以下必達）
        
        Args:
            bb_id: 編集するBB ID
            properties: 変更プロパティ辞書
            
        Returns:
            float: 編集時間（ms）
        """
        start_time = time.perf_counter()
        
        try:
            row = self._find_row_by_id(bb_id)
            if row >= 0:
                # プロパティ更新
                for prop_name, value in properties.items():
                    if prop_name == 'individual_id':
                        item = self.item(row, 1)
                        if item:
                            item.setText(str(value))
                    elif prop_name == 'action_id':
                        item = self.item(row, 2)
                        if item:
                            item.setText(str(value))
                    elif prop_name in ['x', 'y', 'w', 'h']:
                        col_map = {'x': 3, 'y': 4, 'w': 5, 'h': 6}
                        item = self.item(row, col_map[prop_name])
                        if item:
                            item.setText(f"{float(value):.3f}")
                            
                # シグナル発出
                self.bb_edited.emit(bb_id, properties)
                
        except Exception as e:
            print(f"BB properties edit error: {e}")
            
        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 5:
            print(f"WARNING: BB properties edit took {elapsed:.2f}ms (>5ms)")
            
        return elapsed
        
    def delete_selected_bb(self) -> Optional[str]:
        """選択BB削除"""
        if self.selected_bb_id:
            row = self._find_row_by_id(self.selected_bb_id)
            if row >= 0:
                self.removeRow(row)
                bb_id = self.selected_bb_id
                self.selected_bb_id = None
                self.bb_deleted.emit(bb_id)
                return bb_id
        return None
        
    def on_selection_changed(self):
        """選択変更処理"""
        current_row = self.currentRow()
        if current_row >= 0:
            id_item = self.item(current_row, 0)
            if id_item:
                self.selected_bb_id = id_item.text()
                self.bb_selected.emit(self.selected_bb_id)
                
    def on_item_changed(self, item: QTableWidgetItem):
        """アイテム変更処理"""
        if not self.edit_mode:
            return
            
        try:
            row = item.row()
            col = item.column()
            id_item = self.item(row, 0)
            
            if id_item:
                bb_id = id_item.text()
                
                # 変更内容を特定
                properties = {}
                if col == 1:  # Individual
                    properties['individual_id'] = int(item.text())
                elif col == 2:  # Action
                    properties['action_id'] = int(item.text())
                elif col == 3:  # X
                    properties['x'] = float(item.text())
                elif col == 4:  # Y
                    properties['y'] = float(item.text())
                elif col == 5:  # W
                    properties['w'] = float(item.text())
                elif col == 6:  # H
                    properties['h'] = float(item.text())
                    
                if properties:
                    self.bb_edited.emit(bb_id, properties)
                    
        except Exception as e:
            print(f"Item change processing error: {e}")
            
    def on_cell_double_clicked(self, row: int, col: int):
        """セルダブルクリック処理"""
        if self.COLUMNS[list(self.COLUMNS.keys())[col]]['editable']:
            self.edit_mode = True
            self.editItem(self.item(row, col))
            
    def _check_for_updates(self):
        """更新チェック（タイマー）"""
        # 必要に応じて外部からの更新チェック
        pass
        
    def enable_edit_mode(self, enabled: bool = True):
        """編集モード切り替え"""
        self.edit_mode = enabled
        if enabled:
            self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        else:
            self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            
    def get_selected_bb_id(self) -> Optional[str]:
        """選択BB ID取得"""
        return self.selected_bb_id
        
    def get_bb_count(self) -> int:
        """BB数取得"""
        return len(self.bb_entities)
        
    def clear_all_bbs(self):
        """全BBクリア"""
        self.setRowCount(0)
        self.bb_entities.clear()
        self.selected_bb_id = None
        
    def get_performance_info(self) -> Dict[str, Any]:
        """性能情報取得"""
        avg_update_time = (self.total_update_time / self.update_count 
                          if self.update_count > 0 else 0)
        
        return {
            'bb_count': len(self.bb_entities),
            'selected_bb_id': self.selected_bb_id,
            'update_count': self.update_count,
            'avg_update_time': avg_update_time,
            'last_update_time': self.last_update_time,
            'edit_mode': self.edit_mode,
            'target_performance': {
                'list_update': '10ms以下',
                'item_selection': '1ms以下',
                'edit_operation': '5ms以下',
            }
        }


if __name__ == "__main__":
    # BBListPanelテスト
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    import sys
    from dataclasses import dataclass
    import random
    
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
        color: QColor = QColor(255, 0, 0)
    
    app = QApplication(sys.argv)
    
    # メインウィンドウ作成
    main_window = QMainWindow()
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # BBListPanel作成
    bb_list_panel = BBListPanel()
    layout.addWidget(bb_list_panel)
    
    main_window.setCentralWidget(central_widget)
    main_window.resize(600, 400)
    main_window.show()
    
    # テスト用BBリスト生成
    def create_test_bbs(count: int) -> List[TestBBEntity]:
        bbs = []
        for i in range(count):
            bb = TestBBEntity(
                id=f"bb_{i:03d}",
                x=random.uniform(0.1, 0.9),
                y=random.uniform(0.1, 0.9),
                w=random.uniform(0.05, 0.2),
                h=random.uniform(0.05, 0.2),
                individual_id=random.randint(0, 15),
                action_id=random.randint(0, 4),
                confidence=random.uniform(0.7, 1.0),
                color=QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            )
            bbs.append(bb)
        return bbs
    
    # 性能テスト
    print("BBListPanel Performance Test")
    print("=" * 35)
    
    # 更新性能テスト
    test_counts = [10, 50, 100, 200]
    
    for count in test_counts:
        print(f"\\nTesting {count} BBs:")
        test_bbs = create_test_bbs(count)
        
        # 更新時間測定
        times = []
        for _ in range(5):  # 5回実行
            update_time = bb_list_panel.update_bb_list(test_bbs)
            times.append(update_time)
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"  Average update time: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms, Max: {max_time:.2f}ms")
        print(f"  Target: <10ms, Status: {'PASS' if avg_time < 10 else 'FAIL'}")
        
    # 選択性能テスト
    if test_bbs:
        selection_times = []
        for bb in test_bbs[:10]:  # 最初の10個
            select_time = bb_list_panel.select_bb(bb.id)
            selection_times.append(select_time)
            
        if selection_times:
            avg_select_time = sum(selection_times) / len(selection_times)
            print(f"\\nSelection average time: {avg_select_time:.3f}ms")
            print(f"Selection target: <1ms, Status: {'PASS' if avg_select_time < 1 else 'FAIL'}")
    
    # 編集性能テスト
    if test_bbs:
        edit_times = []
        for bb in test_bbs[:5]:  # 最初の5個
            properties = {'individual_id': random.randint(0, 15)}
            edit_time = bb_list_panel.edit_bb_properties(bb.id, properties)
            edit_times.append(edit_time)
            
        if edit_times:
            avg_edit_time = sum(edit_times) / len(edit_times)
            print(f"\\nEdit average time: {avg_edit_time:.3f}ms")
            print(f"Edit target: <5ms, Status: {'PASS' if avg_edit_time < 5 else 'FAIL'}")
    
    # 性能情報表示
    perf_info = bb_list_panel.get_performance_info()
    print("\\nPerformance Info:")
    for key, value in perf_info.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")
            
    print("BBListPanel test completed")
    
    # アプリケーション実行（テスト用）
    # sys.exit(app.exec())