# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

ANTHROPIC_MODEL=sonnet 4

# 🎯 8並列Agent開発プロジェクト
高速オートアノテーションシステム（Fast Auto-Annotation System）- レイヤー別Agent並列開発

## 📋 必須確認事項 (すべてのAgentが最初に確認)

### プロジェクト概要
- **目的**: 個人用動物行動解析向け半自動アノテーションツール (PyQt6デスクトップアプリ)
- **技術スタック**: Python 3.8+ + PyQt6 + OpenCV + NumPy + LRU Cache
- **個体数上限**: 16個体 (ID: 0-15)
- **最重要要件**: フレーム切り替え速度50ms以下（64GBメモリ活用）
- **開発方針**: Claude Agent 8並列開発による高速実装

### 🤖 Agent開発指示書 (Claude Code用)

#### 📖 Agent開発開始時の必須読み込みフロー
**「Agent○○として」と指示された場合、以下順序で必ずファイルを読み込んでください：**

```bash
# ステップ1: 共通基盤ファイル読み込み（全Agent必須）
Read: CLAUDE.md                           # このファイル（全体概要・Agent役割）
Read: requirement.yaml                    # システム全体要件
Read: config/performance_targets.yaml    # 性能目標・Agent別目標
Read: config/layer_interfaces.yaml       # Agent間通信プロトコル

# ステップ2: Agent専門ファイル読み込み（Agent別）
Read: requirements/layers/[担当Agent].md  # Agent専門詳細仕様書
Read: worktrees/agent○_[layer]/README.md # Agent作業環境ガイド

# ステップ3: テスト要件読み込み（実装前必須）
Read: tests/requirements/unit/[agent]-unit-tests.md  # 単体テスト要件

# ステップ4: 実装・テストファイル確認
LS: src/[layer]/                         # 実装ディレクトリ構造確認
LS: tests/unit/test_[layer]/             # テストディレクトリ構造確認
```

#### 🎯 Agent別専門指示（Claude Code実行用）

**Agent1 Presentationとして開発する場合：**
```bash
Read: requirements/layers/presentation.md     # PyQt6 UI・BB描画・ショートカット専門
Read: worktrees/agent1_presentation/README.md # 開発ガイド・優先順序
```

**Agent2 Applicationとして開発する場合：**
```bash
Read: requirements/layers/application.md      # ワークフロー・ビジネスロジック統合専門
Read: worktrees/agent2_application/README.md # 開発ガイド・優先順序
```

**Agent3 Domainとして開発する場合：**
```bash
Read: requirements/layers/domain.md           # BBエンティティ・IOU計算・ビジネスルール専門
Read: worktrees/agent3_domain/README.md      # 開発ガイド・優先順序
```

**Agent4 Infrastructureとして開発する場合：**
```bash
Read: requirements/layers/infrastructure.md   # OpenCV動画処理・技術基盤専門
Read: worktrees/agent4_infrastructure/README.md # 開発ガイド・優先順序
```

**Agent5 Data Busとして開発する場合：**
```bash
Read: requirements/layers/data_bus.md         # Agent間通信・イベント配信専門
Read: worktrees/agent5_data_bus/README.md    # 開発ガイド・優先順序
```

**Agent6 Cache（最重要）として開発する場合：**
```bash
Read: requirements/layers/cache_layer.md      # 高速キャッシュ・50ms達成・最重要Agent
Read: worktrees/agent6_cache_layer/README.md # 開発ガイド・緊急時対応
```

**Agent7 Persistenceとして開発する場合：**
```bash
Read: requirements/layers/persistence.md      # ファイルI/O・自動保存・バックアップ専門
Read: worktrees/agent7_persistence/README.md # 開発ガイド・優先順序
```

**Agent8 Monitoringとして開発する場合：**
```bash
Read: requirements/layers/monitoring.md       # パフォーマンス監視・ログ・デバッグ専門
Read: worktrees/agent8_monitoring/README.md  # 開発ガイド・優先順序
```

#### 📂 実装・テスト配置場所
- **実装コード**: `src/[layer]/` (例: src/cache_layer/, src/presentation/)
- **単体テスト**: `tests/unit/test_[layer]/` (例: tests/unit/test_cache_layer/)
- **統合テスト**: `tests/integration/test_[layer]_integration/`
- **E2Eテスト**: `tests/e2e/test_[機能名]/`

### 8Agent専門分割システム
```
Agent1: Presentation層   ← PyQt6 UI・BB描画・ショートカット専門
Agent2: Application層    ← ワークフロー・ビジネスロジック統合専門  
Agent3: Domain層         ← BBエンティティ・IOU計算・ビジネスルール専門
Agent4: Infrastructure層 ← OpenCV動画処理・フレーム変換専門
Agent5: Data Bus層       ← Agent間通信・イベント配信専門
Agent6: Cache層          ← 高速キャッシュ・パフォーマンス最適化専門（最重要）
Agent7: Persistence層    ← ファイルI/O・自動保存・データ永続化専門
Agent8: Monitoring層     ← パフォーマンス監視・ログ・デバッグ専門
```

### Agent別パフォーマンス目標
- **Agent6 Cache**: フレーム切り替え50ms以下（絶対達成）、キャッシュヒット率95%以上
- **Agent1 Presentation**: BB描画16ms以下、キーボード応答1ms以下
- **Agent2 Application**: ビジネスロジック処理10ms以下
- **Agent3 Domain**: IOU計算1ms以下、座標変換0.5ms以下
- **Agent4 Infrastructure**: 動画変換実速度、4K画像処理50ms以下
- **Agent5 Data Bus**: イベント配信1ms以下、通信オーバーヘッド5%以下
- **Agent7 Persistence**: ファイル保存100ms以下、自動保存非同期
- **Agent8 Monitoring**: 監視オーバーヘッド10ms以下

### 禁止事項 (必須遵守)
- ❌ React/Web技術の使用 (PyQt6デスクトップアプリのみ)
- ❌ 動画再生機能の追加 (4K→5fps静的フレーム表示のみ)
- ❌ Agent責任範囲外の実装（レイヤー越境禁止）
- ❌ フレーム切り替え50ms目標の妥協（絶対達成）
- ❌ 16個体上限・座標系・ファイル形式の独断変更

## Project Overview

高速オートアノテーションシステム（Fast Auto-Annotation System）- 個人用動物行動解析向けの半自動アノテーションツール。4K動画から5fpsフレームを生成し、個体識別・行動識別のバウンディングボックス（BB）アノテーションを高速で実行。フレーム切り替え速度50ms以下を最優先とし、64GBメモリを活用した高速処理をClaude Agent 8並列開発で実現。

## Directory Structure - Agent並列開発用（V字モデル対応）

```
annotation_app/
├── CLAUDE.md                    # Agent共通開発指示書
├── requirement.yaml             # Phase 1: システム要件 + E2Eテスト要件
├── requirements/                # Phase 2: レイヤー要件 + 統合テスト要件
│   └── layers/
│       ├── presentation.md     # Agent1: UI要件 + UI統合テスト要件
│       ├── application.md      # Agent2: アプリケーション要件 + 統合テスト要件
│       ├── domain.md           # Agent3: ドメイン要件 + 統合テスト要件
│       ├── infrastructure.md   # Agent4: インフラ要件 + 統合テスト要件
│       ├── data_bus.md         # Agent5: 通信要件 + 統合テスト要件
│       ├── cache_layer.md      # Agent6: キャッシュ要件 + 統合テスト要件（最重要）
│       ├── persistence.md      # Agent7: 永続化要件 + 統合テスト要件
│       └── monitoring.md       # Agent8: 監視要件 + 統合テスト要件
├── tests/                      # Phase 3 & 4: 詳細テスト設計 + 実装
│   ├── requirements/
│   │   └── unit/               # Phase 3: 単体テスト要件（詳細設計）
│   │       ├── presentation-unit-tests.md
│   │       ├── application-unit-tests.md
│   │       ├── domain-unit-tests.md
│   │       ├── infrastructure-unit-tests.md
│   │       ├── data-bus-unit-tests.md
│   │       ├── cache-layer-unit-tests.md    # 最重要テスト
│   │       ├── persistence-unit-tests.md
│   │       └── monitoring-unit-tests.md
│   ├── unit/                   # Phase 4: 単体テストコード
│   │   ├── test_presentation/
│   │   ├── test_application/
│   │   ├── test_domain/
│   │   ├── test_infrastructure/
│   │   ├── test_data_bus/
│   │   ├── test_cache_layer/      # フレーム切り替え50msテスト
│   │   ├── test_persistence/
│   │   └── test_monitoring/
│   ├── integration/            # Phase 4: 統合テストコード
│   │   ├── test_ui_integration/
│   │   ├── test_business_integration/
│   │   ├── test_data_integration/
│   │   └── test_performance_integration/  # 性能統合テスト
│   └── e2e/                    # Phase 4: E2Eテストコード
│       ├── test_video_to_annotation_flow/
│       ├── test_frame_switching_performance/  # 50ms達成テスト
│       └── test_full_workflow/
├── src/                        # Phase 4: 実装コード
│   ├── presentation/           # Agent1: UI層
│   │   ├── main_window/
│   │   ├── bb_canvas/
│   │   ├── control_panels/
│   │   └── shortcuts/
│   ├── application/            # Agent2: アプリケーション層
│   │   ├── services/
│   │   ├── controllers/
│   │   └── validators/
│   ├── domain/                 # Agent3: ドメイン層
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── repositories/
│   │   └── algorithms/
│   ├── infrastructure/         # Agent4: インフラ層
│   │   ├── video/
│   │   ├── image/
│   │   └── system/
│   ├── data_bus/               # Agent5: データバス層
│   │   ├── event_bus/
│   │   ├── message_queue/
│   │   └── interfaces/
│   ├── cache_layer/            # Agent6: キャッシュ層（最重要）
│   │   ├── frame_cache/
│   │   ├── image_cache/
│   │   └── strategies/
│   ├── persistence/            # Agent7: 永続化層
│   │   ├── file_io/
│   │   ├── project/
│   │   ├── backup/
│   │   └── directory/
│   └── monitoring/             # Agent8: 監視層
│       ├── performance/
│       ├── health/
│       └── debugging/
├── config/                     # 設定・モデル管理
│   ├── default_config.json
│   ├── layer_interfaces.yaml
│   ├── performance_targets.yaml
│   └── models/                 # 自動アノテーション用モデル
├── data/                       # プロジェクトデータ
│   ├── videos/                 # 入力動画
│   ├── frames/                 # 変換済みフレーム
│   ├── annotations/            # アノテーションファイル
│   └── backup/                 # バックアップ
├── scripts/                    # 開発・運用スクリプト
│   ├── setup_agent_env.py      # Agent開発環境セットアップ
│   ├── run_integration_tests.py
│   ├── performance_benchmark.py
│   └── deploy_package.py
├── docs/                       # Agent開発用ドキュメント
│   ├── agent_specifications/   # Agent別仕様書
│   ├── interface_docs/         # レイヤー間インターフェース
│   ├── performance_targets/    # パフォーマンス目標
│   └── integration_guide/      # 統合ガイド
└── worktrees/                  # Agent並列開発用
    ├── agent1_presentation/
    ├── agent2_application/
    ├── agent3_domain/
    ├── agent4_infrastructure/
    ├── agent5_data_bus/
    ├── agent6_cache_layer/     # 最重要Agent
    ├── agent7_persistence/
    └── agent8_monitoring/
```

## V字モデル Agent並列開発フロー

### Phase 1: システム要件定義（1日）
**担当**: システム設計者（人間）
- 全体システム要件定義
- Agent間インターフェース基本設計
- パフォーマンス目標設定（フレーム切り替え50ms以下等）
- E2Eテストシナリオ作成

### Phase 2: Agent別仕様定義（1日・8並列）
**8つのTerminalで並列実行**
- Agent1: PyQt6 UI・BB描画・ショートカット処理の詳細仕様とテスト要件
- Agent2: ビジネスロジック統合・ワークフロー制御の詳細仕様とテスト要件
- Agent3: BBエンティティ・IOU計算・ビジネスルールの詳細仕様とテスト要件
- Agent4: OpenCV動画処理・フレーム変換の詳細仕様とテスト要件
- Agent5: イベント配信・Agent間通信の詳細仕様とテスト要件
- **Agent6**: フレーム切り替え50ms以下絶対達成のLRUキャッシュ詳細仕様（最重要）
- Agent7: ファイルI/O・自動保存・バックアップの詳細仕様とテスト要件
- Agent8: パフォーマンス監視・ログ管理の詳細仕様とテスト要件

### Phase 3: Agent詳細設計（1日・8並列）
各Agentが詳細設計・単体テスト要件作成

### Phase 4: Agent並列実装（2-4日・8並列）
**Day 1-2**: 基盤Agent優先実装（Cache・Data Bus）
**Day 2-3**: コアAgent実装（Domain・Infrastructure・Application）
**Day 3-4**: 統合Agent実装（Presentation・Persistence・Monitoring）

### Phase 5: 統合・テスト（1日）
**段階的統合戦略**
- Step 1: 基盤統合（Data Bus ↔ Cache）
- Step 2: コア統合（Domain ↔ Application ↔ Infrastructure）
- Step 3: 全体統合（8Agent統合・フレーム切り替え50ms確認）


## 🚀 Agent開発実行例

### Claude Code使用例（Agent並列開発）

```bash
# Agent6 Cache（最重要）開発例
claude "Agent6 Cacheとして、フレーム切り替え50ms以下絶対達成のLRUキャッシュシステムをTDD実装してください"

# Agent1 Presentation開発例  
claude "Agent1 Presentationとして、PyQt6による高速UI（BB描画16ms以下・キー応答1ms以下）をTDD実装してください"

# Agent5 Data Bus開発例
claude "Agent5 Data Busとして、Agent間通信基盤（イベント配信1ms以下）をTDD実装してください"
```

## Development Commands

### Python Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (when requirements.txt is created)
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-qt black flake8 mypy
```

### Testing Commands
```bash
# Run all tests
pytest

# Run specific test file
pytest claude/testing/test-code/unit/test_ui_module.py

# Run tests with coverage
pytest --cov=claude/implementation/src

# Run PyQt6 GUI tests
pytest -v claude/testing/test-code/integration/
```

### Code Quality
```bash
# Format code
black claude/implementation/src/

# Lint code
flake8 claude/implementation/src/

# Type checking
mypy claude/implementation/src/
```

### Application Commands
```bash
# Run the annotation application (when implemented)
python src/main.py

# Run in debug mode
python src/main.py --debug

# Run with specific video file
python src/main.py --video /path/to/video.mp4

# Performance benchmark (フレーム切り替え50ms確認)
python scripts/performance_benchmark.py

# Agent development environment setup
python scripts/setup_agent_env.py
```

### Agent Development Commands
```bash
# Agent別並列開発用ワークツリー作成
git worktree add worktrees/agent1_presentation agent1_presentation
git worktree add worktrees/agent6_cache_layer agent6_cache_layer

# Agent別テスト実行
pytest tests/unit/test_cache_layer/ -v  # Cache Agent（最重要）
pytest tests/unit/test_presentation/ -v  # Presentation Agent

# Agent間統合テスト
python scripts/run_integration_tests.py

# フレーム切り替え50ms確認テスト
pytest tests/e2e/test_frame_switching_performance/ -v
```

## Architecture Notes

### Core Application Architecture
- **Main Application**: PyQt6-based desktop application for animal behavior annotation
- **Data Flow**: 4K動画 → 5fpsフレーム変換 → BBアノテーション → YOLO形式保存
- **Coordinate Systems**: Pixel coordinates (UI) ↔ YOLO normalized coordinates (0-1 range)
- **Individual Limit**: Maximum 16 animals per video (IDs 0-15)
- **Performance Target**: フレーム切り替え50ms以下（絶対達成目標）

### Agent Layer Architecture
```
Presentation層 (Agent1) ← PyQt6 UI・BB描画・ショートカット
    ↕ Data Bus (Agent5)
Application層 (Agent2)  ← ワークフロー制御・ビジネスロジック統合
    ↕ Data Bus (Agent5)
Domain層 (Agent3)       ← BBエンティティ・IOU計算・ビジネスルール
    ↕ Data Bus (Agent5)
Infrastructure層 (Agent4) ← OpenCV動画処理・フレーム変換
    ↕ Data Bus (Agent5)
Cache層 (Agent6)        ← 高速キャッシュ・パフォーマンス最適化（最重要）
    ↕ Data Bus (Agent5)
Persistence層 (Agent7)  ← ファイルI/O・自動保存・データ永続化
    ↕ Data Bus (Agent5)
Monitoring層 (Agent8)   ← パフォーマンス監視・ログ・デバッグ
```

### Agent Coordination System
- **8Agent並列開発**: 各レイヤー専門Agent独立実装
- **Data Bus**: Agent間通信・イベント配信の統一ハブ
- **Cache Layer**: フレーム切り替え50ms以下の要となる最重要Agent
- **V字モデル**: 要件定義→詳細設計→実装→統合の品質保証

### Key Design Principles
- **Performance First**: フレーム切り替え50ms以下を最優先
- **Agent Specialization**: 各Agent専門領域に特化
- **Desktop-Only**: PyQt6デスクトップアプリ（Web技術禁止）
- **64GB Memory Utilization**: Cache層で20GB上限活用
- **Test-Driven Development**: TDD・Agent別単体テスト100%通過