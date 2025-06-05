# Auto Annotater - 研究用半自動アノテーションツール

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-red.svg)](https://opencv.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 概要

**auto_annotater** は研究用の半自動アノテーションツールです。コンピュータビジョン研究における画像データのアノテーション作業を効率化し、研究者の生産性向上を支援します。

### 主な特徴

- 🎯 **高速フレーム切り替え**: 50ms以下のフレーム表示（64GBメモリ活用）
- 🖱️ **直感的UI**: PyQt6による高レスポンスなデスクトップアプリケーション
- 📦 **多様な入力形式**: 動画ファイル、画像フォルダ、既存プロジェクト対応
- 🎨 **16個体対応**: 最大16個体の同時トラッキング・アノテーション
- 💾 **YOLO形式出力**: 機械学習モデル学習に即利用可能
- ⚡ **高性能キャッシュ**: LRUキャッシュによる高速画像表示

## AI駆動型開発手法による実装

このプロジェクトでは、複数のAIツールを戦略的に組み合わせた革新的な開発手法を採用しました：

1. **Claude** - 全体の要件定義、システム構造決定
2. **Cursor** - 細かい要件定義、テストケース作成  
3. **Claude Code** - 8並列でテストケースに基づいたテストコード作成
4. **Cursor** - 統合処理
5. **Claude Code** - 8並列実装（レイヤー別専門Agent開発）
6. **Cursor** - 最終統合、仕上げ

この手法により、従来の開発時間を大幅に短縮しつつ、高品質なコードを実現しています。

## 使用技術

### フロントエンド
- **PyQt6** - 高性能GUIフレームワーク
- **OpenGL** - 高速画像描画（オプション）
- **QGraphicsView** - 拡大縮小・バウンディングボックス描画

### バックエンド・処理
- **Python 3.8+** - メイン開発言語
- **OpenCV** - 動画処理・画像変換
- **NumPy** - 数値計算・配列処理
- **Pillow** - 画像ファイル読み込み

### データ処理・機械学習
- **YOLO形式** - バウンディングボックス座標系
- **JSON** - プロジェクト設定・メタデータ
- **LRU Cache** - 高速フレームキャッシュ

### 開発・テスト
- **pytest** - 単体テスト・統合テスト
- **TDD** - テスト駆動開発手法
- **V字モデル** - 品質保証プロセス

## システム要件

### 推奨環境
- **OS**: Linux (Ubuntu 20.04+), Windows 10+, macOS 11+
- **Python**: 3.8 以上
- **メモリ**: 8GB以上（64GB推奨）
- **ストレージ**: 10GB以上の空き容量

### 依存関係
```bash
# 主要依存関係
PyQt6>=6.4.0
opencv-python>=4.8.0
numpy>=1.21.0
Pillow>=9.0.0

# 開発・テスト用
pytest>=7.0.0
pytest-qt>=4.2.0
black>=22.0.0
flake8>=5.0.0
```

## インストール・セットアップ

### 1. リポジトリクローン
```bash
git clone https://github.com/your-username/auto_annotater.git
cd auto_annotater
```

### 2. 仮想環境作成
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows
```

### 3. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 4. アプリケーション起動
```bash
python src/main.py
```

## 使用方法

### 基本的な使用手順

1. **プロジェクト作成**
   - アプリケーション起動時にプロジェクト選択ダイアログが表示
   - 動画ファイル、画像フォルダ、または既存プロジェクトを選択

2. **フレーム表示・ナビゲーション**
   - 左パネル: フレーム画像・バウンディングボックス表示
   - 右パネル: フレーム一覧・操作パネル
   - キーボードショートカット: A(前), D(次), W(作成), S(削除)

3. **アノテーション作業**
   - 個体ID選択（0-15）
   - 行動ID選択（0-4）
   - マウスドラッグでバウンディングボックス作成
   - 既存BBの編集・削除

4. **保存・エクスポート**
   - 自動保存機能（作業中断対応）
   - YOLO形式でエクスポート
   - プロジェクトファイル保存

### キーボードショートカット

| キー | 機能 | 性能目標 |
|------|------|----------|
| `A` | 前のフレーム | 50ms以下 |
| `D` | 次のフレーム | 50ms以下 |
| `W` | BB作成モード切り替え | 1ms以下 |
| `S` | 選択BB削除 | 1ms以下 |
| `Ctrl+Z` | 元に戻す | 10ms以下 |
| `Escape` | 現在のアクションキャンセル | 1ms以下 |

## アーキテクチャ

### 8層並列開発アーキテクチャ

```
┌─────────────────┬─────────────────┐
│  Presentation   │  Application    │ ← Agent1,2: UI・ビジネスロジック
├─────────────────┼─────────────────┤
│     Domain      │ Infrastructure  │ ← Agent3,4: ドメイン・技術基盤
├─────────────────┼─────────────────┤
│   Data Bus      │   Cache Layer   │ ← Agent5,6: 通信・高速キャッシュ
├─────────────────┼─────────────────┤
│  Persistence    │   Monitoring    │ ← Agent7,8: 永続化・監視
└─────────────────┴─────────────────┘
```

### 性能目標

| 層 | 担当Agent | 性能目標 |
|----|-----------|-----------| 
| Cache | Agent6 | フレーム切り替え50ms以下（最重要） |
| Presentation | Agent1 | BB描画16ms以下、キー応答1ms以下 |
| Application | Agent2 | ビジネスロジック処理10ms以下 |
| Domain | Agent3 | IOU計算1ms以下、座標変換0.5ms以下 |
| Infrastructure | Agent4 | 動画変換実速度、4K画像処理50ms以下 |
| Data Bus | Agent5 | イベント配信1ms以下 |
| Persistence | Agent7 | ファイル保存100ms以下 |
| Monitoring | Agent8 | 監視オーバーヘッド10ms以下 |

## アノテーション仕様

### 個体識別・行動識別
- **個体ID**: 0-15（最大16個体）
- **行動ID**: 0-4（sit, stand, milk, water, food）
- **座標系**: YOLO正規化座標（0.0-1.0）

### 出力形式
```
# frame_000000.txt
個体ID 中心X 中心Y 幅 高さ 行動ID 信頼度
0 0.5123 0.3456 0.1234 0.0987 2 0.95
1 0.2345 0.7890 0.0876 0.1234 0 0.87
```

## テスト

### テスト実行
```bash
# 全テスト実行
pytest

# 特定レイヤーのテスト
pytest tests/unit/test_cache_layer/ -v

# 性能テスト
pytest tests/integration/test_performance/ -v

# カバレッジ付きテスト
pytest --cov=src tests/
```

### テスト構成
- **単体テスト**: 各Agent（層）別の独立テスト
- **統合テスト**: Agent間連携テスト
- **E2Eテスト**: 全体ワークフローテスト
- **性能テスト**: 50ms目標達成確認テスト

## 開発

### 開発環境セットアップ
```bash
# 開発依存関係インストール
pip install -r requirements-dev.txt

# コード品質チェック
black src/
flake8 src/
mypy src/

# Agent別並列開発
git worktree add worktrees/agent1_presentation agent1_presentation
```

### Agent別開発ガイド
- 各AgentはPythonが独立して開発可能
- `CLAUDE.md`に詳細な開発指示を記載
- TDD（テスト駆動開発）を採用
- 性能目標達成が必須要件

## 貢献

1. フォークして開発ブランチ作成
2. 機能実装・テスト追加
3. コード品質チェック実行
4. プルリクエスト作成

### 貢献ガイドライン
- Agent専門領域を尊重
- 性能目標を遵守
- テストカバレッジ90%以上維持
- ドキュメント更新

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照

## 連絡先・サポート

- **Issues**: [GitHub Issues](https://github.com/your-username/auto_annotater/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/auto_annotater/discussions)
- **Wiki**: [プロジェクトWiki](https://github.com/your-username/auto_annotater/wiki)

## 謝辞

このプロジェクトは以下のAIツールとの協働により実現されました：

- **Anthropic Claude** - システム設計・要件定義
- **Claude Code** - 8並列Agent実装
- **Cursor** - 統合・仕上げ開発

AI駆動型開発手法の実証例として、従来手法では数ヶ月要する開発を大幅に短縮しつつ、高品質なソフトウェアを実現しています。