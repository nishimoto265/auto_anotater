# 修正内容まとめ

## 修正1: A/Dキーでフレーム移動時のBB表示

**問題の原因**: 
- `display_frame()`メソッド内で`update_bounding_boxes_fast()`を呼んでいたが、その時点で`current_bbs`が空だったため、BBがクリアされていた

**修正内容**:
- `canvas_widget.py`の`display_frame()`メソッド内の`update_bounding_boxes_fast()`呼び出しをコメントアウト
- フレーム切り替え時は`on_frame_selected()`で適切にアノテーションを読み込んでから`update_bounding_boxes()`が呼ばれるため、重複した呼び出しは不要

## 修正2: 既存アノテーション選択時の画像ディレクトリ表示

**問題の原因**:
- FormLayoutとQWidgetの組み合わせで、レイアウトが適切に更新されていなかった

**修正内容**:
- `project_startup_dialog.py`の`toggle_existing_images_visibility()`にレイアウト更新処理を追加
- `updateGeometry()`と`adjustSize()`を呼び出してレイアウトを強制的に更新

## その他の修正済み項目

1. **Sキー削除**: 選択されたBBを`current_annotations`から削除
2. **BB行動ラベル**: action_idを行動名（Sit, Stand等）に変換
3. **ズームエラー**: QPointF型変換の修正
4. **再帰エラー**: blockSignals()による循環参照防止

## 動作確認

```bash
python src/main.py
```

1. A/Dキーでフレーム移動 → BBが正しく表示される
2. 既存アノテーション選択 → 画像ディレクトリ選択欄が表示される
3. Sキーで削除 → 選択したBBまたは最新のBBが削除される
4. BBラベル → "ID:0 Sit"のように行動名が表示される