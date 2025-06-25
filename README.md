# 🐾 高速オートアノテーションシステム
**Fast Auto-Annotation System for Animal Behavior Analysis**

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)](https://pypi.org/project/PyQt6/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-red.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

個人用動物行動解析向けの高速半自動アノテーションツール

[機能](#-主な機能) • [インストール](#-インストール) • [使い方](#-使い方) • [キーボードショートカット](#-キーボードショートカット) • [トラブルシューティング](#-トラブルシューティング)

</div>

## 📋 概要

このツールは、動物行動研究者向けに開発された**高速アノテーションツール**です。4K動画から5fpsでフレームを抽出し、最大16個体の動物に対してバウンディングボックス（BB）でアノテーションを行えます。

### 🎯 こんな方におすすめ
- 🐭 動物行動研究をしている研究者
- 📹 大量の動画データをアノテーションする必要がある方
- ⚡ 高速で効率的なアノテーションツールを探している方
- 🎮 キーボードショートカットで素早く作業したい方

## ✨ 主な機能

### 🎥 動画処理
- **4K動画対応**: 高解像度動画からフレーム抽出
- **5fps変換**: 動画を5fpsに変換して作業効率化
- **高速フレーム切り替え**: 50ms以下の切り替え速度

### 🎯 アノテーション機能
- **マルチ個体対応**: 最大16個体の同時追跡
- **5つの行動カテゴリ**: カスタマイズ可能な行動分類
- **YOLO形式出力**: 機械学習にそのまま使用可能
- **IOU追跡**: 簡易的な自動追跡機能

### 💾 データ管理
- **自動保存**: フレーム切り替え時に自動保存
- **バックアップ機能**: データロスト防止
- **プロジェクト管理**: 複数プロジェクトの切り替え

### ⚡ パフォーマンス
- **高速キャッシュ**: 64GBメモリを活用した先読みキャッシュ
- **マルチスレッド処理**: 効率的なリソース活用
- **OpenGL描画**: 高速なBB描画

## 🚀 インストール

### 必要要件
- Python 3.8以上
- 64GB RAM（推奨）
- Windows/Mac/Linux対応

### インストール手順

1. **リポジトリのクローン**
```bash
git clone https://github.com/yourusername/auto_annotation.git
cd auto_annotation
```

2. **仮想環境の作成**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. **依存ライブラリのインストール**
```bash
pip install -r requirements.txt
```

4. **アプリケーションの起動**
```bash
python src/main.py
```

## 📖 使い方

### 1. プロジェクトの作成/選択

アプリケーション起動時に表示されるダイアログで：
- **新規プロジェクト**: 新しいアノテーションプロジェクトを開始
- **既存プロジェクト**: 過去のプロジェクトを継続

### 2. 動画の読み込み

1. プロジェクトフォルダ内の`videos/`に動画ファイルを配置
2. アプリケーションが自動的に動画を検出
3. 5fpsでフレーム抽出が開始（初回のみ）

### 3. アノテーション作業

#### 基本的な流れ：
1. **個体IDを選択**（右パネル）
2. **行動カテゴリを選択**（右パネル）
3. **BBを描画**（マウスドラッグ）
4. **次のフレームへ**（Dキー）

#### BB（バウンディングボックス）の操作：
- **描画**: マウスでドラッグ
- **選択**: BBをクリック
- **削除**: BBを選択してSキー
- **調整**: BBの角をドラッグ

### 4. データの保存

- **自動保存**: フレーム切り替え時に自動的に保存
- **手動保存**: Ctrl+S（Cmd+S on Mac）
- **保存形式**: YOLO形式（.txt）

## ⌨️ キーボードショートカット

### ナビゲーション
| キー | 機能 |
|------|------|
| **A** | 前のフレーム |
| **D** | 次のフレーム |
| **Q** | 10フレーム戻る |
| **E** | 10フレーム進む |
| **Space** | 現在のフレーム番号を表示 |

### BB操作
| キー | 機能 |
|------|------|
| **W** | BB作成モード |
| **S** | 選択中のBBを削除 |
| **C** | すべてのBBをコピー |
| **V** | BBをペースト |
| **X** | 選択中のBBをカット |

### 個体ID選択
| キー | 機能 |
|------|------|
| **1-9** | 個体ID 1-9を選択 |
| **0** | 個体ID 10を選択 |
| **Shift+1-6** | 個体ID 11-16を選択 |

### その他
| キー | 機能 |
|------|------|
| **Ctrl+S** | 手動保存 |
| **Ctrl+Z** | 元に戻す |
| **Ctrl+Y** | やり直し |
| **F1** | ヘルプ表示 |

## 🏗️ アーキテクチャ

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

| 層 | 性能目標 |
|----|-----------| 
| Cache | フレーム切り替え50ms以下（最重要） |
| Presentation | BB描画16ms以下、キー応答1ms以下 |
| Application | ビジネスロジック処理10ms以下 |
| Domain | IOU計算1ms以下、座標変換0.5ms以下 |

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. アプリケーションが起動しない
```bash
# Pythonバージョンを確認
python --version  # 3.8以上であることを確認

# 依存ライブラリを再インストール
pip install -r requirements.txt --force-reinstall
```

#### 2. フレーム切り替えが遅い
- メモリ使用量を確認（タスクマネージャー等）
- `config/default_config.json`でキャッシュサイズを調整
- デバッグモードをOFFにする: `python src/main.py`（--debugなし）

#### 3. 動画が読み込めない
- 対応形式: MP4, AVI, MOV
- 動画ファイルを`data/videos/`フォルダに配置
- ファイル名に特殊文字が含まれていないか確認

#### 4. BBが保存されない
- `data/annotations/`フォルダの書き込み権限を確認
- ディスク容量が十分にあるか確認
- 自動保存が有効になっているか設定を確認

## 📊 パフォーマンス最適化

### メモリ使用量の調整
```json
// config/default_config.json
{
  "cache": {
    "max_memory_gb": 20,  // 最大メモリ使用量
    "preload_frames": 100  // 先読みフレーム数
  }
}
```

### フレームレートの調整
```json
{
  "video": {
    "target_fps": 5,  // 抽出フレームレート
    "quality": 95     // JPEG品質（0-100）
  }
}
```

## 🗂️ プロジェクト構造

詳細なプロジェクト構造については、[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)を参照してください。

```
auto_annotation/
├── src/              # ソースコード
├── tests/            # テストコード
├── data/             # プロジェクトデータ
├── config/           # 設定ファイル
├── docs/             # ドキュメント
└── requirements.txt  # 依存ライブラリ
```

## 🤖 AI駆動型開発

このプロジェクトは、複数のAIツールを戦略的に組み合わせた革新的な開発手法を採用しました：

1. **Claude** - 全体の要件定義、システム構造決定
2. **Cursor** - 細かい要件定義、テストケース作成  
3. **Claude Code** - 8並列でテストケースに基づいたテストコード作成
4. **Cursor** - 統合処理
5. **Claude Code** - 8並列実装（レイヤー別専門Agent開発）
6. **Cursor** - 最終統合、仕上げ

この手法により、従来の開発時間を大幅に短縮しつつ、高品質なコードを実現しています。

## 🤝 貢献方法

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙏 謝辞

- OpenCVコミュニティ
- PyQt6開発チーム
- 動物行動研究コミュニティ
- Anthropic Claude - システム設計・要件定義
- Claude Code - 8並列Agent実装
- Cursor - 統合・仕上げ開発

## 📞 サポート

問題や質問がある場合は、[Issues](https://github.com/yourusername/auto_annotation/issues)でお知らせください。

---

<div align="center">

**Happy Annotating! 🎉**

[トップへ戻る](#-高速オートアノテーションシステム)

</div>