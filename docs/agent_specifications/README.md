# 📋 Agent仕様書

このディレクトリには、8つの並列開発Agentの詳細仕様書を配置します。

## 🤖 Agent一覧

### Agent1: Presentation層
- **担当**: PyQt6 UI、BB描画、ショートカット処理
- **仕様書**: `agent1_presentation_spec.md`

### Agent2: Application層
- **担当**: ワークフロー制御、ビジネスロジック統合
- **仕様書**: `agent2_application_spec.md`

### Agent3: Domain層
- **担当**: BBエンティティ、IOU計算、ビジネスルール
- **仕様書**: `agent3_domain_spec.md`

### Agent4: Infrastructure層
- **担当**: OpenCV動画処理、フレーム変換
- **仕様書**: `agent4_infrastructure_spec.md`

### Agent5: Data Bus層
- **担当**: Agent間通信、イベント配信
- **仕様書**: `agent5_data_bus_spec.md`

### Agent6: Cache層（最重要）
- **担当**: 高速キャッシュ、50ms達成
- **仕様書**: `agent6_cache_layer_spec.md`

### Agent7: Persistence層
- **担当**: ファイルI/O、自動保存、バックアップ
- **仕様書**: `agent7_persistence_spec.md`

### Agent8: Monitoring層
- **担当**: パフォーマンス監視、ログ、デバッグ
- **仕様書**: `agent8_monitoring_spec.md`

## 📝 仕様書テンプレート

各Agent仕様書は以下の構成で作成：

1. **概要**
   - 役割と責任
   - 主要機能

2. **技術要件**
   - 使用技術
   - 依存関係

3. **インターフェース**
   - 提供API
   - イベント定義

4. **パフォーマンス目標**
   - 処理時間目標
   - リソース使用制限

5. **実装ガイドライン**
   - コーディング規約
   - テスト要件