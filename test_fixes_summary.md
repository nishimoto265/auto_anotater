# 修正内容まとめ

## 実装した修正

### 1. 既存アノテーション選択時の画像ディレクトリ表示問題

**修正ファイル**: `src/presentation/dialogs/project_startup_dialog.py`

**修正内容**:
- QWidgetコンテナを使わず、FormLayoutに直接追加
- 行インデックスを保存して正確な表示制御を実現
```python
# 行番号199-201
self.existing_images_row_index = layout.rowCount()
layout.addRow("画像ディレクトリ:", existing_images_layout)
```

### 2. A/Dキーでフレーム移動時にBBが消える問題

**修正ファイル**: `src/presentation/bb_canvas/canvas_widget.py`

**修正内容**:
- `display_frame()`メソッドでBBレンダラーのアイテムをクリア
```python
# 行番号219-220
if not hasattr(self, '_skip_bb_update'):
    self.bb_renderer._clear_rendered_items()
```

### 3. Sキー削除が実際に削除されない問題

**修正ファイル**: `src/presentation/main_window/main_window.py`

**修正内容**:
- `current_annotations`リストから実際にBBを削除
```python
self.current_annotations = [bb for bb in self.current_annotations if bb.get('id') != selected_bb.id]
```

### 4. BB描画サイズとラベル表示

**修正ファイル**: `src/presentation/bb_canvas/bb_renderer.py`

**修正内容**:
- フォントサイズ: 24 → 36ピクセル
- 境界線幅: 2 → 3ピクセル
- ラベル表示: ID → 行動名（Sit, Stand, Milk, Water, Food）

### 5. その他の修正

- モジュールインポートパス修正（'src.'プレフィックスを削除）
- QPointF型変換エラー修正
- 循環参照によるRecursionError修正

## テスト方法

### 包括的テストスクリプト実行
```bash
python test_comprehensive.py
```

このスクリプトで以下を確認：
1. ダイアログで既存選択時に画像ディレクトリ選択が表示されるか
2. BBが正しく描画されるか（行動名表示、サイズ確認）
3. フレーム切り替え時にBBが消えないか

### 実際のアプリケーション実行
```bash
python src/main.py
```

確認ポイント：
- 新規プロジェクトダイアログで「既存アノテーション読み込み」選択時に画像ディレクトリ選択欄が表示される
- A/Dキーでフレーム移動してもBBが消えない
- Sキーで選択したBBが実際に削除される
- BBのラベルに行動名が表示される（Sit, Stand等）
- BB一覧パネルに項目が表示される