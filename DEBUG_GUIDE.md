# デバッグガイド

## 問題2: A/Dキーでフレーム移動時のアノテーション表示

アプリケーション実行時に以下を確認してください：

1. コンソール出力を確認
   - `Loading annotations for frame X` が表示されるか
   - `No annotation_output_dir set` が表示される場合は、ディレクトリが設定されていない
   - `Looking for annotation file: /path/to/file.txt` でパスを確認

2. 可能な原因：
   - annotation_output_dir が正しく設定されていない
   - アノテーションファイルのパスが間違っている
   - フレーム番号がずれている

## 問題3: 既存アノテーション選択時の画像ディレクトリ表示

1. コンソール出力を確認
   - `on_project_type_changed: existing_radio.isChecked() = True` が表示されるか
   - `toggle_existing_images_visibility: visible = True` が表示されるか
   - `After toggle: container.isVisible() = True` が表示されるか

2. もし表示されない場合の対処法：
   - ダイアログを開いた時点で「既存アノテーション読み込み」を選択
   - 他のオプションを選択してから「既存アノテーション読み込み」に戻す

## デバッグ情報の確認方法

```bash
# アプリケーションを起動
python src/main.py

# コンソール出力を監視
# 特に以下のメッセージに注目：
# - "Loading annotations for frame"
# - "No annotation_output_dir set"
# - "toggle_existing_images_visibility"
```

## 追加の修正が必要な場合

上記のデバッグ情報を基に、具体的なエラーメッセージや動作を教えてください。