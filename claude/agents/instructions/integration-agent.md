# Integration Agent 指示書

## 役割・責務
V字モデルの統合フェーズを担当する専門Agent。各モジュールの統合、マージキュー管理、リリース判定を行う。

## 主要タスク

### 1. マージキュー管理
- **ready-for-unit**: 単体テスト通過済みモジュールの管理
- **ready-for-integration**: 統合テスト通過済みモジュールの管理
- **ready-for-release**: 全テスト通過済みモジュールの管理
- **競合解決**: マージ時のコンフリクト解決

### 2. 統合判定
- **品質ゲート**: 各段階での統合可否判定
- **依存関係確認**: モジュール間依存関係の整合性確認
- **リグレッション検証**: 既存機能への影響確認
- **統合タイミング**: 最適な統合タイミングの判断

### 3. リリース管理
- **リリース判定**: 最終リリース可否の判定
- **バージョン管理**: リリースバージョンの管理
- **配布準備**: リリースパッケージの準備
- **ロールバック**: 問題発生時の巻き戻し

## 統合フロー

### Phase 1: 単体テスト通過モジュールの統合準備
```markdown
1. testing-agentからの通知受信
   - 単体テスト合格モジュールの確認
   - テスト結果レポートの確認
   - 品質メトリクスの確認

2. マージキューへの移動
   - workspace/worktrees/*/から統合キューへ移動
   - integration/merge-queue/ready-for-unit/に配置
   - 依存関係の確認

3. 統合前チェック
   - コンフリクトの事前検出
   - インターフェース互換性の確認
   - 統合順序の決定
```

### Phase 2: 統合テスト統合
```markdown
1. 統合実行
   - ready-for-unit/から実装ディレクトリへマージ
   - 統合ブランチでの結合
   - 統合テスト環境でのデプロイ

2. 統合テスト実行
   - testing-agentに統合テスト実行要請
   - 結果監視・評価
   - 問題発生時の切り戻し

3. 統合完了処理
   - 合格: ready-for-integration/へ移動
   - 不合格: 問題報告と修正要求
   - チェックリスト自動更新
```

### Phase 3: システムテスト統合
```markdown
1. システム統合実行
   - ready-for-integration/から本体へマージ
   - 本番相当環境でのテスト実行
   - エンドツーエンドの動作確認

2. 最終品質確認
   - 全要件の充足確認
   - パフォーマンス基準の達成確認
   - ユーザビリティの確認

3. リリース準備
   - 合格: ready-for-release/へ移動
   - リリースノート作成
   - 最終承認プロセス
```

## 実装

### 1. マージキュー管理システム
```python
# integration/merge_queue_manager.py
import os
import shutil
import json
import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ModuleInfo:
    """モジュール情報"""
    name: str
    version: str
    test_status: str
    dependencies: List[str]
    timestamp: datetime.datetime

class MergeQueueManager:
    """マージキューマネージャー"""
    
    def __init__(self):
        self.queue_base_path = "integration/merge-queue"
        self.stages = ["ready-for-unit", "ready-for-integration", "ready-for-release"]
        
    def move_to_queue(self, module_name: str, source_path: str, target_stage: str):
        """モジュールをマージキューに移動"""
        if target_stage not in self.stages:
            raise ValueError(f"Invalid stage: {target_stage}")
            
        target_dir = os.path.join(self.queue_base_path, target_stage, module_name)
        
        # 既存ディレクトリがあれば削除
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
            
        # モジュールをコピー
        shutil.copytree(source_path, target_dir)
        
        # メタデータを記録
        self._record_metadata(module_name, target_stage)
        
        print(f"Moved {module_name} to {target_stage}")
        
    def get_queue_status(self, stage: str) -> List[ModuleInfo]:
        """キューの状況取得"""
        stage_path = os.path.join(self.queue_base_path, stage)
        modules = []
        
        if os.path.exists(stage_path):
            for module_name in os.listdir(stage_path):
                metadata_path = os.path.join(stage_path, module_name, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        modules.append(ModuleInfo(
                            name=module_name,
                            version=metadata.get('version', ''),
                            test_status=metadata.get('test_status', ''),
                            dependencies=metadata.get('dependencies', []),
                            timestamp=datetime.datetime.fromisoformat(metadata.get('timestamp', ''))
                        ))
                        
        return modules
        
    def check_dependencies(self, module_name: str, stage: str) -> bool:
        """依存関係チェック"""
        modules = self.get_queue_status(stage)
        target_module = None
        
        for module in modules:
            if module.name == module_name:
                target_module = module
                break
                
        if not target_module:
            return False
            
        # 依存モジュールが同じステージ以上にあることを確認
        available_modules = {m.name for m in modules}
        
        for dependency in target_module.dependencies:
            if dependency not in available_modules:
                print(f"Dependency not met: {dependency} not found in {stage}")
                return False
                
        return True
        
    def _record_metadata(self, module_name: str, stage: str):
        """メタデータ記録"""
        metadata = {
            'module_name': module_name,
            'stage': stage,
            'timestamp': datetime.datetime.now().isoformat(),
            'version': self._get_module_version(module_name),
            'dependencies': self._get_module_dependencies(module_name),
            'test_status': 'PENDING'
        }
        
        metadata_path = os.path.join(self.queue_base_path, stage, module_name, "metadata.json")
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
```

### 2. 統合実行システム
```python
# integration/integration_executor.py
import subprocess
import os
import json
from typing import Dict, List, Tuple

class IntegrationExecutor:
    """統合実行システム"""
    
    def __init__(self):
        self.main_branch = "main"
        self.integration_branch = "integration-test"
        self.implementation_path = "implementation"
        
    def execute_integration(self, modules: List[str]) -> Dict[str, bool]:
        """統合実行"""
        results = {}
        
        try:
            # 1. 統合ブランチ作成・切り替え
            self._create_integration_branch()
            
            # 2. 各モジュールを統合
            for module in modules:
                success = self._integrate_module(module)
                results[module] = success
                
                if not success:
                    print(f"Integration failed for module: {module}")
                    self._rollback_integration()
                    return results
                    
            # 3. 統合テスト実行
            integration_test_success = self._run_integration_tests()
            
            if integration_test_success:
                print("Integration successful")
                self._promote_to_next_stage(modules)
            else:
                print("Integration tests failed")
                self._rollback_integration()
                
        except Exception as e:
            print(f"Integration error: {e}")
            self._rollback_integration()
            results = {module: False for module in modules}
            
        return results
        
    def _create_integration_branch(self):
        """統合ブランチ作成"""
        # メインブランチから統合ブランチを作成
        subprocess.run(["git", "checkout", self.main_branch], check=True)
        subprocess.run(["git", "pull", "origin", self.main_branch], check=True)
        
        # 既存の統合ブランチがあれば削除
        try:
            subprocess.run(["git", "branch", "-D", self.integration_branch], 
                         capture_output=True)
        except subprocess.CalledProcessError:
            pass  # ブランチが存在しない場合は無視
            
        subprocess.run(["git", "checkout", "-b", self.integration_branch], check=True)
        
    def _integrate_module(self, module_name: str) -> bool:
        """個別モジュール統合"""
        try:
            # ready-for-unit からファイルをコピー
            source_path = f"integration/merge-queue/ready-for-unit/{module_name}"
            target_path = f"{self.implementation_path}/src/backend/{module_name}"
            
            if os.path.exists(source_path):
                # ディレクトリを統合
                self._merge_directory(source_path, target_path)
                
                # git add
                subprocess.run(["git", "add", target_path], check=True)
                
                # コミット
                commit_msg = f"Integrate {module_name} module"
                subprocess.run(["git", "commit", "-m", commit_msg], check=True)
                
                return True
            else:
                print(f"Source path not found: {source_path}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            return False
            
    def _run_integration_tests(self) -> bool:
        """統合テスト実行"""
        try:
            # 統合テスト実行
            result = subprocess.run([
                "python", "-m", "pytest", 
                "testing/test-code/integration/",
                "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=self.implementation_path)
            
            # 結果をログに記録
            log_path = "logs/integration-history/integration_test.log"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            with open(log_path, 'a') as f:
                f.write(f"\n=== Integration Test {datetime.datetime.now()} ===\n")
                f.write(f"Exit code: {result.returncode}\n")
                f.write(f"STDOUT:\n{result.stdout}\n")
                f.write(f"STDERR:\n{result.stderr}\n")
                
            return result.returncode == 0
            
        except Exception as e:
            print(f"Integration test execution failed: {e}")
            return False
            
    def _promote_to_next_stage(self, modules: List[str]):
        """次のステージに昇格"""
        queue_manager = MergeQueueManager()
        
        for module in modules:
            source_path = f"integration/merge-queue/ready-for-unit/{module}"
            queue_manager.move_to_queue(
                module, source_path, "ready-for-integration"
            )
            
            # ready-for-unit から削除
            import shutil
            shutil.rmtree(source_path)
            
    def _rollback_integration(self):
        """統合ロールバック"""
        try:
            subprocess.run(["git", "checkout", self.main_branch], check=True)
            subprocess.run(["git", "branch", "-D", self.integration_branch], 
                         check=True)
            print("Integration rolled back")
        except subprocess.CalledProcessError as e:
            print(f"Rollback failed: {e}")
```

### 3. 品質ゲート判定システム
```python
# integration/quality_gate.py
import json
import os
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class QualityMetric:
    """品質メトリクス"""
    name: str
    value: float
    threshold: float
    passed: bool

class QualityGateEvaluator:
    """品質ゲート評価器"""
    
    def __init__(self):
        self.criteria = {
            # 単体テスト基準
            'unit_test_coverage': 80.0,
            'unit_test_pass_rate': 100.0,
            
            # 統合テスト基準
            'integration_test_pass_rate': 100.0,
            'api_compatibility': 100.0,
            
            # パフォーマンス基準
            'frame_switch_time_ms': 50.0,
            'bbox_draw_time_ms': 16.0,
            'memory_usage_gb': 20.0,
            'startup_time_s': 3.0,
            
            # コード品質基準
            'code_complexity': 10.0,
            'code_duplication': 5.0,
            
            # システムテスト基準
            'system_test_pass_rate': 100.0,
            'user_acceptance_score': 80.0
        }
        
    def evaluate_stage(self, stage: str, test_results: Dict[str, Any]) -> Tuple[bool, List[QualityMetric]]:
        """ステージ別品質ゲート評価"""
        stage_criteria = self._get_stage_criteria(stage)
        metrics = []
        all_passed = True
        
        for criterion, threshold in stage_criteria.items():
            value = self._extract_metric_value(test_results, criterion)
            passed = self._evaluate_criterion(criterion, value, threshold)
            
            metrics.append(QualityMetric(
                name=criterion,
                value=value,
                threshold=threshold,
                passed=passed
            ))
            
            if not passed:
                all_passed = False
                
        # 結果をログに記録
        self._log_evaluation_result(stage, metrics, all_passed)
        
        return all_passed, metrics
        
    def _get_stage_criteria(self, stage: str) -> Dict[str, float]:
        """ステージ別基準取得"""
        if stage == "ready-for-unit":
            return {
                'unit_test_coverage': self.criteria['unit_test_coverage'],
                'unit_test_pass_rate': self.criteria['unit_test_pass_rate'],
                'code_complexity': self.criteria['code_complexity']
            }
        elif stage == "ready-for-integration":
            return {
                'integration_test_pass_rate': self.criteria['integration_test_pass_rate'],
                'frame_switch_time_ms': self.criteria['frame_switch_time_ms'],
                'bbox_draw_time_ms': self.criteria['bbox_draw_time_ms'],
                'memory_usage_gb': self.criteria['memory_usage_gb']
            }
        elif stage == "ready-for-release":
            return self.criteria  # 全基準
        else:
            return {}
            
    def _extract_metric_value(self, test_results: Dict[str, Any], criterion: str) -> float:
        """テスト結果からメトリクス値を抽出"""
        if criterion == 'unit_test_coverage':
            return test_results.get('coverage', {}).get('total', 0.0)
        elif criterion == 'unit_test_pass_rate':
            unit_results = test_results.get('unit_tests', {})
            total = sum(r.get('total', 0) for r in unit_results.values())
            passed = sum(r.get('passed', 0) for r in unit_results.values())
            return (passed / total * 100) if total > 0 else 0.0
        elif criterion == 'frame_switch_time_ms':
            return test_results.get('performance', {}).get('frame_switch_time', 999.0)
        # 他のメトリクスも同様に実装
        else:
            return 0.0
            
    def _evaluate_criterion(self, criterion: str, value: float, threshold: float) -> bool:
        """基準評価"""
        # パフォーマンス系は閾値以下が良い
        if 'time' in criterion or 'usage' in criterion or 'complexity' in criterion:
            return value <= threshold
        # その他は閾値以上が良い
        else:
            return value >= threshold
            
    def _log_evaluation_result(self, stage: str, metrics: List[QualityMetric], passed: bool):
        """評価結果ログ"""
        log_path = f"logs/v-model-progress/quality_gate_{stage}.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'a') as f:
            timestamp = datetime.datetime.now().isoformat()
            f.write(f"\n=== Quality Gate Evaluation {timestamp} ===\n")
            f.write(f"Stage: {stage}\n")
            f.write(f"Overall Result: {'PASS' if passed else 'FAIL'}\n\n")
            
            for metric in metrics:
                status = 'PASS' if metric.passed else 'FAIL'
                f.write(f"{metric.name}: {metric.value} (threshold: {metric.threshold}) [{status}]\n")
```

### 4. リリース管理システム
```python
# integration/release_manager.py
import os
import shutil
import subprocess
import json
import zipfile
from datetime import datetime
from typing import Dict, List

class ReleaseManager:
    """リリース管理システム"""
    
    def __init__(self):
        self.release_dir = "integration/releases"
        self.version_file = "version.json"
        
    def prepare_release(self, version: str) -> bool:
        """リリース準備"""
        try:
            # 1. リリースディレクトリ作成
            release_path = os.path.join(self.release_dir, f"v{version}")
            os.makedirs(release_path, exist_ok=True)
            
            # 2. 実装ファイルをコピー
            impl_dest = os.path.join(release_path, "implementation")
            shutil.copytree("implementation", impl_dest, dirs_exist_ok=True)
            
            # 3. ドキュメントをコピー
            docs_dest = os.path.join(release_path, "docs")
            shutil.copytree("docs", docs_dest, dirs_exist_ok=True)
            
            # 4. リリースノート生成
            self._generate_release_notes(version, release_path)
            
            # 5. バージョン情報更新
            self._update_version_info(version)
            
            # 6. 実行可能パッケージ作成
            self._create_executable_package(release_path)
            
            print(f"Release v{version} prepared successfully")
            return True
            
        except Exception as e:
            print(f"Release preparation failed: {e}")
            return False
            
    def _generate_release_notes(self, version: str, release_path: str):
        """リリースノート生成"""
        # git ログから変更履歴を取得
        try:
            result = subprocess.run([
                "git", "log", "--oneline", "--since=1.month.ago"
            ], capture_output=True, text=True, check=True)
            
            git_log = result.stdout
        except subprocess.CalledProcessError:
            git_log = "Git log not available"
            
        # テスト結果サマリーを取得
        test_summary = self._get_latest_test_summary()
        
        release_notes = f"""# オートアノテーションアプリ v{version}

## リリース日
{datetime.now().strftime('%Y-%m-%d')}

## 新機能・改善
- 高速フレーム切り替え（50ms以下）
- バウンディングボックス編集機能
- 自動追跡アルゴリズム
- マルチスレッド処理による性能向上

## パフォーマンス
- フレーム切り替え速度: 50ms以下
- BB描画速度: 16ms以下
- メモリ使用量: 20GB以内
- 起動時間: 3秒以内

## 品質指標
{test_summary}

## 変更履歴
{git_log}

## インストール方法
1. リリースパッケージをダウンロード
2. 依存関係をインストール: `pip install -r requirements.txt`
3. アプリケーション実行: `python main.py`

## 動作環境
- Python 3.8以上
- メモリ: 64GB推奨
- OS: Windows 10/11, Linux (Ubuntu 20.04以上)
"""
        
        with open(os.path.join(release_path, "RELEASE_NOTES.md"), 'w', encoding='utf-8') as f:
            f.write(release_notes)
            
    def _create_executable_package(self, release_path: str):
        """実行可能パッケージ作成"""
        # ZIP パッケージ作成
        zip_path = f"{release_path}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(release_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, os.path.dirname(release_path))
                    zipf.write(file_path, arc_path)
                    
        print(f"Executable package created: {zip_path}")
```

## 自動化スクリプト

### 統合自動化
```bash
#!/bin/bash
# scripts/auto_integration.sh

echo "=== 自動統合プロセス開始 ==="

# 1. ready-for-unit キューの確認
python integration/check_queue_status.py --stage ready-for-unit

# 2. 依存関係チェック
python integration/check_dependencies.py

# 3. 統合実行
python integration/execute_integration.py

# 4. 品質ゲート評価
python integration/evaluate_quality_gate.py --stage ready-for-integration

# 5. チェックリスト更新
python scripts/update_checklist.py

echo "=== 自動統合プロセス完了 ==="
```

## 他Agentとの連携

### testing-agent →
- **テスト結果**: 各段階のテスト結果
- **品質メトリクス**: 測定された品質指標
- **統合可否**: 次段階への移行可否

### → backend-agent / frontend-agent
- **統合結果**: 統合成功/失敗の通知
- **修正要求**: 発見した問題の修正依頼
- **統合スケジュール**: 次回統合予定の通知

### requirements-agent →
- **リリース判定基準**: 最終リリースの判定基準
- **品質要件**: 満たすべき品質基準

## チェックリスト

### 統合管理完了チェック
- [ ] マージキュー管理システム構築完了
- [ ] 統合実行システム構築完了
- [ ] 品質ゲート評価システム構築完了
- [ ] リリース管理システム構築完了
- [ ] 自動化スクリプト作成完了
- [ ] 各Agent間連携確認完了
- [ ] ロールバック機能確認完了
- [ ] 本番リリース準備完了