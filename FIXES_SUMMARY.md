# Fast Auto-Annotation System - Fixes Summary

## 修正完了項目 (2024-06-24)

### 1. ✓ 既存アノテーション選択時の画像ディレクトリ選択表示
**問題**: 既存アノテーション選択時に画像ディレクトリ選択が表示されない
**修正内容**:
- `project_startup_dialog.py`: FormLayoutのラベル表示処理を修正
- `toggle_existing_images_visibility()`メソッドで`labelForField`を使用してラベルも適切に表示/非表示

### 2. ✓ s,dキーでのフレーム移動時のアノテーション表示
**問題**: フレーム切り替え時にアノテーションが表示されない
**修正内容**:
- `main_window.py`: 全プロジェクトタイプで`annotation_output_dir`を設定
- 動画プロジェクト: `os.path.join(output_dir, 'annotations')`
- 画像プロジェクト: 同上または画像フォルダ隣の`annotations`
- 既存プロジェクト: アノテーションディレクトリを直接使用

### 3. ✓ BBと文字サイズを1.5倍に拡大
**問題**: BBと文字が小さい
**修正内容**:
- `bb_renderer.py`: フォントサイズを24→36ピクセルに変更
- `bb_renderer.py`: ボーダー幅を2→3ピクセルに変更

### 4. ✓ BB一覧の表示
**問題**: BB一覧に何も表示されない
**修正内容**:
- `main_window.py`: `update_bb_list_panel()`メソッドを追加
- `on_bb_created()`でBB作成時に一覧を更新
- `on_frame_selected()`でフレーム選択時に一覧を更新

### 5. ✓ Sキーでの削除機能
**問題**: Sキーを押してもBBが削除されない
**修正内容**:
- `main_window.py`: `delete_selected_bb()`で最新BBを削除する処理を実装
- 削除後に`update_bb_list_panel()`を呼び出してBB一覧も更新

### 6. ✓ モジュールインポートエラー修正
**問題**: `ModuleNotFoundError: No module named 'src'`
**修正内容**:
- `main_window.py`: インポートパスから`src.`プレフィックスを削除
- `from src.presentation.bb_canvas.canvas_widget` → `from presentation.bb_canvas.canvas_widget`

## テスト結果
全ての修正が正常に実装されていることを確認:
- コード構造の検証完了
- 各機能の実装確認完了

## 使用方法
```bash
# 仮想環境をアクティベート
source venv/bin/activate  # または app_venv/bin/activate

# アプリケーションを起動
python src/main.py
```

## 注意事項
- PyQt6が必要です
- 画像ディレクトリとアノテーションディレクトリは同じ構造である必要があります
- YOLO形式のアノテーション（.txt）をサポート