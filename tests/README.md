# UI修正テストスイート

このディレクトリには、UI修正の回帰テストが含まれています。

## テストの目的

今回修正した以下の問題が再発しないことを確認：

1. **既存アノテーション選択時の画像ディレクトリ表示問題**
   - 問題: 画像ディレクトリ選択欄が表示されない
   - テスト: `test_ui_fixes.py::TestProjectStartupDialog`

2. **A/Dキーでフレーム移動時にBBが消える問題**
   - 問題: フレーム切り替え時にBBが消失
   - テスト: `test_ui_fixes.py::TestBBCanvas::test_bb_persistence_on_frame_switch`

3. **Sキー削除が動作しない問題**
   - 問題: Sキーを押してもBBが削除されない
   - テスト: `test_ui_fixes.py::TestMainWindow::test_s_key_deletion`

4. **BBラベル表示の問題**
   - 問題: 行動IDの数字が表示される
   - テスト: `test_ui_fixes.py::TestBBCanvas::test_bb_text_size_and_content`

5. **BB一覧パネルの問題**
   - 問題: BB一覧に何も表示されない
   - テスト: `test_ui_fixes.py::TestMainWindow::test_bb_list_panel_update`

## テストの実行方法

### すべてのテストを実行
```bash
python tests/run_tests.py
```

### 特定のテストのみ実行
```bash
# ダイアログ関連のテスト
python tests/run_tests.py dialog

# キャンバス関連のテスト
python tests/run_tests.py canvas

# 削除機能のテスト
python tests/run_tests.py deletion

# 統合テスト
python tests/run_tests.py integration
```

### pytestで直接実行
```bash
# 基本的なテスト
pytest tests/test_ui_fixes.py -v

# 統合テスト
pytest tests/test_integration_ui.py -v

# カバレッジ付き
pytest tests/ --cov=src --cov-report=html

# 特定のテストクラスのみ
pytest tests/test_ui_fixes.py::TestProjectStartupDialog -v

# 特定のテストメソッドのみ
pytest tests/test_ui_fixes.py::TestMainWindow::test_s_key_deletion -v
```

## テストファイルの構成

### `test_ui_fixes.py`
個別の修正項目に対する単体テスト：
- `TestProjectStartupDialog`: ダイアログの表示問題
- `TestBBCanvas`: キャンバスとBB描画の問題
- `TestMainWindow`: メインウィンドウの機能問題
- `TestZoomController`: ズーム機能の型エラー
- `TestBBListPanel`: BB一覧パネルの循環参照
- `TestImportPaths`: インポートパスの問題

### `test_integration_ui.py`
実際の使用シナリオに基づいた統合テスト：
- `TestExistingProjectWorkflow`: 既存プロジェクトの完全なワークフロー
- `TestFrameSwitchingWithAnnotations`: フレーム切り替えとアノテーション保持
- `TestBBDeletionAndDisplay`: BB選択と削除の統合動作
- `TestBBLabelDisplay`: BBラベルの正しい表示

### `conftest.py`
pytest設定とフィクスチャ定義

### `run_tests.py`
テスト実行ヘルパースクリプト

## CI/CD統合

これらのテストは継続的インテグレーションに統合できます：

```yaml
# .github/workflows/test.yml の例
name: UI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-qt
    - name: Run tests
      run: python tests/run_tests.py
```

## テストの拡張

新しい機能を追加する際は、対応するテストも追加してください：

1. 新機能の単体テストを`test_ui_fixes.py`に追加
2. 統合シナリオを`test_integration_ui.py`に追加
3. 必要に応じて新しいテストファイルを作成

## トラブルシューティング

### QApplicationエラー
```
RuntimeError: Please destroy the QApplication singleton before creating a new QApplication instance.
```
解決: `conftest.py`のフィクスチャを使用してQApplicationを管理

### ディスプレイエラー（CI環境）
```
qt.qpa.xcb: could not connect to display
```
解決: `xvfb-run`を使用するか、`QT_QPA_PLATFORM=offscreen`を設定