# CLAUDE.md

ANTHROPIC_MODEL=sonnet 4

プロジェクト概要は@READMEを、このプロジェクトで利用可能なnpmコマンドは@package.jsonを参照してください。

# 追加指示
- gitワークフロー @docs/git-instructions.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an auto-annotation project implementing V-model development methodology with parallel development capabilities.

## Directory Structure - V字モデル対応・並列開発用

```
claude/
├── requirements/              # 要件定義階層（V字の左側）
│   ├── global/               # 全体要件定義
│   │   ├── system-requirements.md
│   │   ├── business-requirements.md
│   │   └── quality-requirements.md
│   └── modules/              # モジュール別詳細要件
│       ├── ui-module/
│       │   ├── requirements.md
│       │   ├── acceptance-criteria.md
│       │   └── interfaces.md
│       ├── video-processing-module/
│       ├── annotation-module/
│       └── tracking-module/
├── testing/                  # テスト階層（V字の右側）
│   ├── test-plans/          # テスト計画
│   │   ├── system-test-plan.md
│   │   └── integration-test-plan.md
│   ├── test-cases/          # モジュール別テストケース
│   │   ├── ui-module/
│   │   │   ├── unit-tests/
│   │   │   ├── integration-tests/
│   │   │   └── acceptance-tests/
│   │   ├── video-processing-module/
│   │   ├── annotation-module/
│   │   └── tracking-module/
│   ├── test-code/           # 実行可能テストコード
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   └── reports/             # テスト実行結果
│       ├── unit-test-results/
│       ├── integration-results/
│       └── system-test-results/
├── checklists/              # 進捗管理チェックリスト
│   ├── v-model-checklist.md # V字モデル全体の進捗
│   ├── module-checklists/   # モジュール別チェックリスト
│   │   ├── ui-module-checklist.md
│   │   ├── video-processing-module-checklist.md
│   │   ├── annotation-module-checklist.md
│   │   └── tracking-module-checklist.md
│   └── integration-checklist.md # 統合時のチェックリスト
├── implementation/          # 実装コード（本体）
│   ├── src/                # メインソースコード
│   │   ├── backend/        # バックエンド実装
│   │   │   ├── ui-module/  # UIモジュール実装
│   │   │   ├── video-processing-module/ # 動画処理実装
│   │   │   ├── annotation-module/ # アノテーション実装
│   │   │   └── tracking-module/ # 追跡機能実装
│   │   ├── frontend/       # フロントエンド実装
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   └── services/
│   │   ├── shared/         # 共通モジュール
│   │   └── config/         # 設定ファイル
│   ├── database/          # データベース関連
│   │   ├── migrations/
│   │   ├── seeds/
│   │   └── schemas/
│   └── infrastructure/    # インフラ設定
│       ├── docker/
│       ├── k8s/
│       └── terraform/
├── workspace/             # 並列開発ワークスペース
│   ├── worktrees/        # Git ワークツリー管理
│   │   ├── ui-feature/    # UI機能開発用ワークツリー
│   │   │   └── implementation/ # ↑実装ディレクトリのワークツリー
│   │   ├── video-feature/ # 動画処理機能開発用ワークツリー
│   │   │   └── implementation/ # ↑実装ディレクトリのワークツリー
│   │   ├── annotation-feature/ # アノテーション機能開発用ワークツリー
│   │   │   └── implementation/ # ↑実装ディレクトリのワークツリー
│   │   └── tracking-feature/ # 追跡機能開発用ワークツリー
│   │       └── implementation/ # ↑実装ディレクトリのワークツリー
│   ├── experiments/      # 試行錯誤・PoC
│   ├── contexts/        # Agent用コンテキスト情報
│   │   ├── project-context.md # プロジェクト全体の文脈
│   │   ├── coding-standards.md # コーディング規約
│   │   └── architecture.md    # アーキテクチャ設計
│   └── handoffs/        # ワークツリー間の引き継ぎ
├── agents/
│   ├── instructions/          # Agent別の指示書（V字に対応）
│   │   ├── requirements-agent.md # 要件定義担当
│   │   ├── test-design-agent.md   # テスト設計担当
│   │   ├── backend-agent.md       # バックエンド開発担当
│   │   ├── frontend-agent.md      # フロントエンド開発担当
│   │   ├── testing-agent.md       # テスト実行担当
│   │   └── integration-agent.md   # 統合担当
│   ├── memory/                # Agent間の記憶・状態共有
│   │   ├── requirements-decisions.md # 要件に関する判断履歴
│   │   ├── test-coverage.md      # テストカバレッジ状況
│   │   ├── implementation-status.md # 実装状況
│   │   ├── blockers.md           # 各Agentが抱えている課題
│   │   └── next-actions.md       # 次のアクション項目
│   └── coordination/          # Agent間の調整
│       ├── v-model-sync.md    # V字モデルの同期ポイント
│       ├── test-dependencies.md # テスト依存関係
│       └── integration-gates.md # 統合ゲート条件
├── integration/
│   ├── merge-queue/           # マージ待ちの変更
│   │   ├── ready-for-unit/    # 単体テスト通過済み
│   │   ├── ready-for-integration/ # 統合テスト通過済み
│   │   └── ready-for-release/ # 全テスト通過済み
│   ├── conflicts/             # 競合解決用
│   └── releases/              # リリース準備
├── docs/
│   ├── api/                   # API仕様書
│   ├── architecture/          # 設計ドキュメント
│   └── decisions/             # ADR (Architecture Decision Records)
└── logs/
    ├── agent-sessions/        # Agent別のセッション記録
    ├── test-execution-logs/   # テスト実行ログ
    ├── integration-history/   # 統合作業の履歴
    └── v-model-progress/      # V字モデル進捗ログ
```

## V字モデル開発フロー

### Phase 1: 要件定義 → テスト設計（V字の準備）
1. requirements-agent: 全体要件定義作成
2. requirements-agent: 各モジュールの詳細要件作成
3. test-design-agent: 要件からテストケース作成
4. testing-agent: 実行可能テストコード作成
5. 自動生成: 要件とテストからチェックリスト作成

### Phase 2: 並列開発実行（V字の実装）
1. backend-agent/frontend-agent: ワークツリーで並列実装
2. testing-agent: 単体テスト実行・結果チェック
3. integration-agent: 合格モジュールを統合キューへ移動

### Phase 3: 統合・検証（V字の右側）
1. testing-agent: 統合テスト実行
2. integration-agent: 合格モジュールを次キューへ移動
3. testing-agent: E2Eテスト実行
4. integration-agent: mainブランチへマージ
5. 自動更新: チェックリストにチェック追加

## Agent Role Assignments

- **requirements-agent**: 要件定義担当
- **test-design-agent**: テスト設計担当  
- **backend-agent**: バックエンド開発担当
- **frontend-agent**: フロントエンド開発担当
- **testing-agent**: テスト実行担当
- **integration-agent**: 統合担当

## Development Commands

*To be added when development environment is set up*

## Architecture Notes

- V字モデルによる品質重視開発
- 並列開発による効率化
- Agent間の自動調整・チェックリスト管理
- テスト駆動開発の徹底