# Auto Annotater - 動画・画像アノテーションツール

PyQt6を使用した高速で直感的な動画・画像アノテーションツールです。機械学習プロジェクトでのデータセット作成を効率化します。

## 機能

- **マルチメディア対応**: 動画ファイルと画像ファイルの両方をサポート
- **16個体管理**: 最大16個体のIDを同時に管理
- **5種類の行動ラベル**: sit, stand, milk, water, food
- **高速画像キャッシュ**: 20GB上限のインテリジェントキャッシュシステム
- **リアルタイム描画**: バウンディングボックスのドラッグ＆ドロップ編集
- **YOLO形式出力**: 機械学習に最適化されたデータ形式
- **アンドゥ・リドゥ機能**: 誤操作を簡単に修正
- **自動保存**: データ損失を防ぐ自動保存機能

## システム要件

- Python 3.8以上
- Linux環境（Ubuntu 20.04以上推奨）
- PyQt6対応のシステム
- 最低4GB RAM（推奨8GB以上）

## インストール

### 1. システム依存関係のインストール

```bash
sudo apt update
sudo apt install -y libxcb-cursor0 libxcb-cursor-dev python3-venv python3-pip
```

### 2. プロジェクトのクローン

```bash
git clone https://github.com/nishimoto265/auto_anotater.git
cd auto_anotater
```

### 3. 仮想環境のセットアップ

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 使用方法

### 基本的な起動

```bash
source venv/bin/activate
python main.py
```

### 設定オプション

アプリケーションは `config/app_config.json` ファイルで設定をカスタマイズできます：

```json
{
  "performance": {
    "auto_save_interval": 30,
    "cache_size_gb": 20
  },
  "ui": {
    "default_zoom": 1.0,
    "grid_enabled": false
  }
}
```

## 主な操作

### キーボードショートカット

- `Ctrl+Z`: 元に戻す
- `Ctrl+Y`: やり直し  
- `←/→`: フレーム移動
- `Delete`: 選択バウンディングボックス削除

### マウス操作

- **左クリック + ドラッグ**: 新しいバウンディングボックス作成
- **バウンディングボックスをクリック**: 選択
- **選択状態でドラッグ**: 移動
- **マウスホイール**: ズームイン/アウト

## プロジェクト構造

```
auto_anotater/
├── main.py                 # メインエントリーポイント
├── requirements.txt        # Python依存関係
├── config/
│   ├── app_config.json    # アプリケーション設定
│   └── id_config.json     # ID設定
├── src/
│   ├── core/              # コアロジック
│   │   ├── annotation_manager.py
│   │   ├── bbox_manager.py
│   │   └── image_cache.py
│   ├── ui/                # ユーザーインターフェース
│   │   ├── main_window.py
│   │   ├── frame_viewer.py
│   │   ├── id_panel.py
│   │   └── navigation_panel.py
│   └── utils/             # ユーティリティ
│       ├── coordinate_converter.py
│       ├── color_manager.py
│       └── logger.py
└── docs/                  # ドキュメント
```

## 技術仕様

- **フレームワーク**: PyQt6
- **画像処理**: OpenCV (headless)
- **データ形式**: YOLO format (normalized coordinates)
- **設定管理**: JSON
- **ログ**: Python標準logging

## トラブルシューティング

### よくある問題

1. **Qt platform plugin エラー**
   ```bash
   sudo apt install libxcb-cursor0 libxcb-cursor-dev
   ```

2. **仮想環境の問題**
   ```bash
   deactivate
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **依存関係の競合**
   - `opencv-python-headless`を使用（GUI競合回避）

## 貢献

プロジェクトへの貢献を歓迎します！

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 作者

**nishimoto265**

- GitHub: [@nishimoto265](https://github.com/nishimoto265)

## 謝辞

- PyQt6コミュニティ
- OpenCVプロジェクト
- YOLOフォーマット仕様

pip install -r requirements.txt

python main.py --video path/to/video.mp4

python main.py --frames path/to/frames

python main.py --resume path/to/project

UI Layer
 ├── MainWindow
 ├── FrameViewer
 ├── IDPanel
 └── NavigationPanel

Core Layer
 ├── AnnotationManager
 ├── VideoProcessor
 ├── ImageCache
 └── TrackingSystem

Utils Layer
 ├── CoordinateConverter
 ├── ColorManager
 └── FileManager

<object-id> <x> <y> <width> <height> <action-id> <confidence>

0 0.716797 0.395833 0.216406 0.202778 1 0.98
1 0.287109 0.600694 0.158594 0.184722 2 0.95

{
  "individual_ids": [0-15],
  "action_ids": ["sit", "stand", "milk", "water", "food"],
  "colors": {"0": "#FF0000", ...},
  "performance": {
    "cache_size_gb": 20,
    "preload_frames": 100
  }
};