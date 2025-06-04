# Agent1 Presentation Layer

PyQt6高速UI・BB描画16ms以下・キー応答1ms以下を実現するPresentationレイヤー

## 🎯 Agent1の使命

**フレーム切り替え50ms以下レスポンス実現** - ユーザー体験の要となる高速UI

## 📋 実装範囲

### コア機能
- PyQt6メインウィンドウ（70%:30%レイアウト）
- BBキャンバス（OpenGL描画・16ms以下）
- キーボードショートカット（A/D/W/S/Ctrl+Z・1ms応答）
- 操作パネル（ID・行動・BB一覧）

### 性能目標
- **BB描画**: 16ms以下
- **キーボード応答**: 1ms以下  
- **マウス応答**: 5ms以下
- **ズーム操作**: 100ms以下
- **フレーム表示**: 50ms以下（Cache連携）

## 🚀 Quick Start

### 環境セットアップ
```bash
# Python仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# Agent開発環境セットアップ
python scripts/setup_agent_env.py
```

### アプリケーション実行
```bash
# アノテーションアプリ起動
python src/main.py

# デバッグモード
python src/main.py --debug

# 動画指定起動
python src/main.py --video /path/to/video.mp4
```

### パフォーマンステスト
```bash
# フレーム切り替え50ms確認
pytest tests/e2e/test_frame_switching_performance/ -v

# 総合ベンチマーク
python scripts/performance_benchmark.py
```

## 📋 基本操作

### キーボードショートカット
- **A/D**: フレーム切り替え（前/次）
- **W**: BB作成モード
- **S**: BB削除
- **Ctrl+Z**: 元に戻す

### マウス操作
- **ドラッグ**: BB作成・移動
- **ホイール**: ズーム
- **中クリック+ドラッグ**: パン

### UI構成（70%:30%レイアウト）
- **左70%**: 4Kフレーム表示・BB描画キャンバス
- **右30%**: 操作パネル（ID選択・行動選択・BB一覧・ファイル一覧）

## 🔧 Agent並列開発ガイド

### Agent別ワークツリー作成
```bash
# Cache Agent（最重要）
git worktree add worktrees/agent6_cache_layer agent6_cache_layer

# Presentation Agent
git worktree add worktrees/agent1_presentation agent1_presentation

# その他Agent
git worktree add worktrees/agent2_application agent2_application
# ... 全8Agent分
```

### Agent別テスト実行
```bash
# Cache Agent（最重要）- フレーム切り替え50msテスト
pytest tests/unit/test_cache_layer/ -v

# Presentation Agent - UI性能テスト
pytest tests/unit/test_presentation/ -v

# 統合テスト
python scripts/run_integration_tests.py
```

### Agent開発手順
1. **仕様確認**: `requirements/layers/[agent_name].md`
2. **インターフェース確認**: `config/layer_interfaces.yaml`
3. **性能目標確認**: `config/performance_targets.yaml`
4. **TDD実装**: 単体テスト先行作成→実装
5. **統合参加**: Agent間通信確認→全体統合

## 📊 パフォーマンス目標

### 最重要目標
- **フレーム切り替え**: 50ms以下（絶対達成）
- **キャッシュヒット率**: 95%以上
- **メモリ使用量**: 20GB上限（64GBの1/3）

### Agent別目標
| Agent | 重要メトリクス | 目標値 |
|-------|----------------|--------|
| **Cache** | フレーム切り替え | **50ms以下** |
| Presentation | BB描画 | 16ms以下 |
| Application | ビジネスロジック | 10ms以下 |
| Domain | IOU計算 | 1ms以下 |
| Infrastructure | 4K画像処理 | 50ms以下 |
| Data Bus | イベント配信 | 1ms以下 |
| Persistence | ファイル保存 | 100ms以下 |
| Monitoring | 監視オーバーヘッド | 10ms以下 |

## 📁 データ形式

### アノテーションファイル（YOLO形式）
```
# 000000.txt, 000001.txt, ...
個体ID YOLO_X YOLO_Y YOLO_W YOLO_H 行動ID 信頼度

例:
0 0.5123 0.3456 0.1234 0.0987 2 0.9512
1 0.2345 0.7890 0.0876 0.1234 0 0.8743
```

### 行動カテゴリ
- **0**: sit（座る）
- **1**: stand（立つ）
- **2**: milk（授乳）
- **3**: water（飲水）
- **4**: food（摂食）

### 個体ID
- **範囲**: 0-15（16個体上限）
- **色分け**: 自動色マッピング

## 🔄 開発ワークフロー

### Phase 2: Agent別仕様定義（8並列）
```bash
# 8つのTerminalで並列実行
claude "Agent1 Presentation仕様: PyQt6 UI・BB描画・ショートカット処理"
claude "Agent6 Cache仕様: フレーム切り替え50ms以下絶対達成のLRUキャッシュ"
# ... 全Agent分
```

### Phase 4: Agent並列実装
**Day 1-2**: 基盤Agent（Cache・Data Bus）  
**Day 2-3**: コアAgent（Domain・Infrastructure・Application）  
**Day 3-4**: 統合Agent（Presentation・Persistence・Monitoring）

### Phase 5: 統合戦略
1. **基盤統合** (2h): Data Bus ↔ Cache
2. **コア統合** (3h): Domain ↔ Application ↔ Infrastructure  
3. **全体統合** (3h): 8Agent統合・フレーム切り替え50ms確認

## 🧪 テスト戦略

### テスト種別
- **単体テスト**: Agent別TDD・100%通過必須
- **統合テスト**: Agent間通信・性能確認
- **E2Eテスト**: フレーム切り替え50ms確認・完全ワークフロー

### 重要テストシナリオ
1. **フレーム切り替え性能**: 1000回連続・50ms以下100%達成
2. **メモリ使用量**: 4時間連続動作・20GB以下維持
3. **操作性**: 全ショートカット・マウス操作正常動作
4. **データ整合性**: アノテーション保存・読み込み100%正確

## 📂 ディレクトリ構造

```
annotation_app/
├── CLAUDE.md                   # Agent共通開発指示書
├── requirement.yaml            # システム要件定義
├── requirements/layers/        # Agent別仕様
├── tests/                      # テストコード
├── src/                        # 実装コード（8Agent別）
├── config/                     # 設定・インターフェース
├── data/                       # プロジェクトデータ
├── scripts/                    # 開発・運用スクリプト
└── worktrees/                  # Agent並列開発用
```

## ⚠️ 重要な制約

### 禁止事項
- ❌ React/Web技術（PyQt6デスクトップアプリのみ）
- ❌ 動画再生機能（静的フレーム表示のみ）
- ❌ Agent責任範囲外実装（レイヤー越境禁止）
- ❌ フレーム切り替え50ms目標の妥協（絶対達成）

### 必須事項
- ✅ PyQt6 GUI framework使用
- ✅ YOLO形式データ出力
- ✅ フレーム切り替え50ms以下達成
- ✅ TDD開発手法
- ✅ Agent間Data Bus通信

## 🎯 成功基準

### 機能要件
- [ ] 4K動画→5fpsフレーム変換
- [ ] BBドラッグ作成・16個体管理
- [ ] YOLO形式自動保存
- [ ] IOU追跡・ID継承

### 性能要件
- [ ] **フレーム切り替え50ms以下100%達成**
- [ ] キャッシュヒット率95%以上
- [ ] メモリ使用量20GB以下
- [ ] 4時間連続動作安定性

### 品質要件
- [ ] 単体テスト100%通過
- [ ] 統合テスト100%通過
- [ ] E2Eテスト100%通過
- [ ] Agent並列開発成功

## 📞 サポート

### トラブルシューティング
- フレーム切り替えが遅い → Cache Agent最適化確認
- メモリ不足 → キャッシュサイズ調整・LRU削除確認  
- Agent間通信エラー → Data Bus設定確認
- UI応答性問題 → Presentation Agent最適化確認

### 開発サポート
- Agent仕様: `requirements/layers/[agent_name].md`
- パフォーマンス: `config/performance_targets.yaml`
- インターフェース: `config/layer_interfaces.yaml`
- 統合ガイド: `docs/integration_guide/`

---

**Agent1 Presentationは、ユーザー体験の要です。Cache Agentとの連携によりフレーム切り替え50ms以下を実現し、直感的で高速な動物行動アノテーション作業を可能にします。**