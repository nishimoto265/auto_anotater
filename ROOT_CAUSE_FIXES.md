# 根本原因と修正内容

## 問題1: A/Dキーでフレーム移動時にBBが消える

### 根本原因
1. `load_frame()` → `display_frame()` → BBレンダラーのアイテムがクリアされる
2. その後`update_bounding_boxes()`が呼ばれるが、レンダラーのアイテムがシーンに追加されていない状態になっていた

### 修正内容
`canvas_widget.py`の`display_frame()`で、BBレンダラーのアイテムをクリアするように修正。これにより、後続の`update_bounding_boxes()`で新しいアイテムが正しくシーンに追加される。

## 問題2: 既存アノテーション選択時の画像ディレクトリが表示されない

### 根本原因
FormLayoutとQWidgetコンテナの組み合わせで、visibility制御が正しく動作していなかった。

### 修正内容
1. QWidgetコンテナを使わず、直接QHBoxLayoutをFormLayoutに追加
2. FormLayoutの行インデックスを保存し、該当行のラベルとフィールドを直接制御
3. `toggle_existing_images_visibility()`でFormLayoutのitemAt()メソッドを使用して正確に制御

## テスト方法

```bash
python src/main.py
```

1. 画像プロジェクトを開く
2. A/Dキーでフレーム移動 → BBが正しく表示されることを確認
3. 新規プロジェクトダイアログで「既存アノテーション読み込み」を選択 → 画像ディレクトリ選択欄が表示されることを確認