# 🤖 Claude Code間接的連携システム - 完全ガイド

## 📋 システム概要

**Boss01のClaude Code → 各AgentのClaude Code** へエンター付きで直接指示を送信する間接的連携システム。8Agent並列開発での効率的なコミュニケーションを実現。

## 🎯 特徴

- ✅ **Claude Code実行中でもエンター付き送信**
- ✅ **tmux 4x4グリッド対応**
- ✅ **8Agent並列開発サポート**
- ✅ **自動プロンプトクリア機能**
- ✅ **確実な指示伝達**

---

## 🚀 基本セットアップ

### 1. tmuxマルチAgentセッション起動
```bash
./create_multiagent_tmux.sh
```

### 2. ペイン構成確認
```
boss01(0)  a01(1)   b01(2)   c01(3)
boss02(4)  a02(5)   b02(6)   c02(7) 
boss03(8)  a03(9)   b03(10)  c03(11)
boss04(12) a04(13)  b04(14)  c04(15)
```

---

## 🎯 メイン送信コマンド

### クイック送信 (推奨方法)
```bash
./scripts/quick_send.sh [ペイン名] [メッセージ]
```

**基本例:**
```bash
# A01にhello送信
./scripts/quick_send.sh a01 "hello"

# Agent1として開発開始指示
./scripts/quick_send.sh a01 "Agent1 Presentationとして、PyQt6による高速UI実装を開始してください"
```

---

## 🎯 Agent別ペイン指定

### Agent1-4 (Core Development)
| ペイン名 | 番号 | Agent | 専門領域 |
|----------|------|-------|----------|
| `a01` | 1 | **Agent1 Presentation** | PyQt6 UI・BB描画・ショートカット |
| `a02` | 5 | **Agent2 Application** | ビジネスロジック統合・ワークフロー |
| `a03` | 9 | **Agent3 Domain** | BBエンティティ・IOU計算・ビジネスルール |
| `a04` | 13 | **Agent4 Infrastructure** | OpenCV動画処理・フレーム変換 |

### Agent5-8 (System & Performance)
| ペイン名 | 番号 | Agent | 専門領域 |
|----------|------|-------|----------|
| `b01` | 2 | **Agent5 DataBus** | Agent間通信・イベント配信 |
| `b02` | 6 | **🔥Agent6 Cache (最重要)** | **フレーム切り替え50ms以下絶対達成** |
| `b03` | 10 | **Agent7 Persistence** | ファイルI/O・自動保存・バックアップ |
| `b04` | 14 | **Agent8 Monitoring** | パフォーマンス監視・ログ・デバッグ |

### その他
| ペイン名 | 番号 | 用途 |
|----------|------|------|
| `c01-c04` | 3,7,11,15 | 予備・テスト・統合作業用 |
| `boss01-04` | 0,4,8,12 | Boss管理・指示出し専用 |

---

## 🧪 8Agent並列開発ワークフロー

### Phase 1: 基盤Agent起動 (最優先)
```bash
# データ通信基盤
./scripts/quick_send.sh b01 "Agent5 DataBusとして、Agent間通信基盤を実装してください"

# 🔥 最重要：パフォーマンス基盤
./scripts/quick_send.sh b02 "Agent6 Cacheとして、フレーム切り替え50ms以下絶対達成をお願いします"
```

### Phase 2: コアAgent起動
```bash
# ドメインロジック
./scripts/quick_send.sh a03 "Agent3 Domainとして、BBエンティティ・IOU計算を実装してください"

# 技術基盤
./scripts/quick_send.sh a04 "Agent4 Infrastructureとして、OpenCV動画処理を実装してください"

# ビジネスロジック統合
./scripts/quick_send.sh a02 "Agent2 Applicationとして、ビジネスロジック統合を実装してください"
```

### Phase 3: 統合Agent起動
```bash
# UI統合
./scripts/quick_send.sh a01 "Agent1 Presentationとして、PyQt6による高速UI実装を開始してください"

# データ永続化
./scripts/quick_send.sh b03 "Agent7 Persistenceとして、ファイルI/O・自動保存を実装してください"

# システム監視
./scripts/quick_send.sh b04 "Agent8 Monitoringとして、パフォーマンス監視を実装してください"
```

### Phase 4: パフォーマンステスト・統合テスト
```bash
# 最重要目標確認
./scripts/quick_send.sh b02 "フレーム切り替え50ms以下の達成確認テストを実行してください"

# UI性能確認
./scripts/quick_send.sh a01 "UI応答性能テスト（BB描画16ms以下）を実行してください"

# 統合テスト
./scripts/quick_send.sh a02 "全Agent統合テストを実行してください"

# システム監視確認
./scripts/quick_send.sh b04 "パフォーマンス監視結果の報告をお願いします"
```

---

## 🛡️ Claude Code対応技術詳細

### 自動実行ステップ
1. **`C-c`** - Claude Codeの現在入力をキャンセル
2. **`sleep 0.3`** - Claude Code準備時間確保
3. **メッセージ入力** - 指示内容を入力
4. **`sleep 0.1`** - 入力完了待機
5. **`C-m`** - エンター押下で実行開始

### 対応状況
- ✅ **Claude Code実行中**: エンター付きで確実に送信
- ✅ **Claude Code非実行**: 即座に実行
- ✅ **プロンプト待機中**: 自動クリア後実行

---

## 🔧 実用的な指示例

### Agent別開発指示テンプレート

#### Agent1 Presentation (PyQt6 UI)
```bash
./scripts/quick_send.sh a01 "Agent1 Presentationとして、PyQt6による高速UI（BB描画16ms以下・キー応答1ms以下）をTDD実装してください"
```

#### Agent6 Cache (最重要)
```bash
./scripts/quick_send.sh b02 "Agent6 Cacheとして、フレーム切り替え50ms以下絶対達成のLRUキャッシュシステムをTDD実装してください"
```

#### Agent2 Application (ビジネスロジック)
```bash
./scripts/quick_send.sh a02 "Agent2 Applicationとして、ワークフロー制御・ビジネスロジック統合をTDD実装してください"
```

#### Agent3 Domain (ビジネスルール)
```bash
./scripts/quick_send.sh a03 "Agent3 Domainとして、BBエンティティ・IOU計算・ビジネスルールをTDD実装してください"
```

### 統合・テスト指示例
```bash
# 統合テスト
./scripts/quick_send.sh a02 "Agent統合テストを実行し、レイヤー間通信を確認してください"

# パフォーマンステスト
./scripts/quick_send.sh b02 "フレーム切り替え50ms以下達成のベンチマークを実行してください"

# E2Eテスト
./scripts/quick_send.sh a01 "4K動画→5fpsフレーム→BBアノテーション→YOLO保存のE2Eテストを実行してください"
```

---

## 🔧 追加機能・上級者向け

### 複数ペイン一斉送信
```bash
# Worker-A全体（Agent1-4）に一斉送信
./scripts/tmux_broadcast.sh "git status" "worker-a"

# Worker-B全体（Agent5-8）に一斉送信
./scripts/tmux_broadcast.sh "pytest tests/unit/ -v" "worker-b"

# 全ペインに一斉送信
./scripts/tmux_broadcast.sh "clear" "all"
```

### 直接tmuxコマンド
```bash
# 手動でのきめ細かい制御
tmux send-keys -t "multagent:0.1" C-c        # プロンプトクリア
sleep 0.3
tmux send-keys -t "multagent:0.1" "メッセージ" C-m  # 送信+実行
```

### セッション管理
```bash
# セッション一覧確認
tmux list-sessions

# ペイン一覧確認
tmux list-panes -t multagent:0

# セッション再起動
tmux kill-session -t multagent
./create_multiagent_tmux.sh
```

---

## 📁 ファイル構成

```
scripts/
├── quick_send.sh              # 🎯 メイン送信コマンド（推奨）
├── tmux_broadcast.sh          # 複数ペイン一斉送信
├── file_watcher.sh            # ファイル監視（バグあり・非推奨）
└── create_multiagent_tmux.sh  # tmuxセッション作成

instructions/
├── commands.txt               # ファイル監視用（現在未使用）
├── README.md                  # 詳細ドキュメント
└── test_commands.txt          # テスト用サンプル

docs/
└── CLAUDE_CODE_INDIRECT_COLLABORATION.md  # このファイル
```

---

## 🐛 トラブルシューティング

### tmuxセッションが見つからない
```bash
# セッション確認
tmux list-sessions

# セッション再作成
./create_multiagent_tmux.sh
```

### メッセージが届かない
```bash
# ペイン存在確認
tmux list-panes -t multagent:0

# 直接送信テスト
./scripts/quick_send.sh c01 "テストメッセージ"
```

### Claude Codeが応答しない
```bash
# プロンプトクリア
tmux send-keys -t "multagent:0.1" C-c

# 再送信
./scripts/quick_send.sh a01 "再送信テスト"
```

### エンターが押されない
- **quick_send.sh** を使用（自動でC-c、sleep、C-m処理）
- 手動の場合は `sleep` を挟む

---

## ✅ 成功確認チェックリスト

### 基本動作確認
- [ ] tmuxセッション「multagent」が起動している
- [ ] 4x4ペイン（16個）が正しく表示されている
- [ ] A01ペインでClaude Codeが動作している

### 送信機能確認
- [ ] `./scripts/quick_send.sh a01 "hello"` でメッセージが表示される
- [ ] Claude Code実行中でもエンターが自動で押される
- [ ] Claude Codeが応答を開始する

### Agent開発確認
- [ ] 各Agentが指示を受け取り、開発を開始している
- [ ] Agent6 Cacheがフレーム切り替え50ms以下を目標に作業している
- [ ] Agent間でレイヤー境界を守って開発している

---

## 🎉 最終的な使用方法まとめ

**Boss01からA01への指示送信:**
```bash
./scripts/quick_send.sh a01 "Agent1 Presentationとして開発開始"
```

**Agent6 Cache（最重要）への指示:**
```bash
./scripts/quick_send.sh b02 "Agent6 Cacheとしてフレーム切り替え50ms以下絶対達成"
```

**8Agent並列開発の完全自動化連携システム完成！** 🚀

---

*生成日: 2025-06-06*  
*システム: Claude Code間接的連携システム v1.0*  
*対象: 8Agent並列開発プロジェクト（高速オートアノテーションシステム）*