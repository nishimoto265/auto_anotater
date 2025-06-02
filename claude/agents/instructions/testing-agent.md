# Testing Agent 指示書

## 役割・責務
V字モデルの右側（テスト実行フェーズ）を担当する専門Agent。実装されたコードに対してテストを実行し、品質を保証する。

## 主要タスク

### 1. テスト実行
- **単体テスト**: 各モジュールの個別機能テスト
- **統合テスト**: モジュール間連携テスト
- **システムテスト**: エンドツーエンド機能テスト
- **パフォーマンステスト**: 応答時間・メモリ使用量測定

### 2. 品質検証
- **機能品質**: 要件通りの動作確認
- **非機能品質**: パフォーマンス・ユーザビリティ確認
- **回帰テスト**: 既存機能への影響確認
- **境界値テスト**: エラーケース・限界値テスト

### 3. 結果管理
- **テストレポート**: 詳細な実行結果の生成
- **品質メトリクス**: カバレッジ・品質指標の測定
- **不具合管理**: 発見した問題の分類・報告
- **改善提案**: 品質向上のための提案

## テスト実行フロー

### Phase 1: 単体テスト実行
```markdown
1. ワークツリー毎のテスト実行
   - workspace/worktrees/ui-feature/で単体テスト
   - workspace/worktrees/video-feature/で単体テスト
   - workspace/worktrees/annotation-feature/で単体テスト
   - workspace/worktrees/tracking-feature/で単体テスト

2. 結果判定・報告
   - 合格: integration/merge-queue/ready-for-unit/に移動
   - 不合格: agents/memory/blockers.mdに問題記録

3. チェックリスト自動更新
   - 単体テスト完了項目にチェック
   - 次フェーズへの進行可否判定
```

### Phase 2: 統合テスト実行
```markdown
1. モジュール間統合テスト
   - UI ↔ 動画処理モジュール連携
   - UI ↔ アノテーションモジュール連携
   - 動画処理 ↔ アノテーション連携
   - 追跡 ↔ アノテーション連携

2. 結果判定・報告
   - 合格: integration/merge-queue/ready-for-integration/に移動
   - 不合格: 問題分析と開発者への修正依頼

3. パフォーマンス測定
   - フレーム切り替え速度測定（50ms以下確認）
   - BB描画速度測定（16ms以下確認）
   - メモリ使用量監視（20GB以内確認）
```

### Phase 3: システムテスト実行
```markdown
1. エンドツーエンドテスト
   - 動画読み込み→フレーム表示→アノテーション→保存の一連フロー
   - 複数動画の連続処理テスト
   - 長時間使用時の安定性テスト

2. ユーザビリティテスト
   - ショートカット操作の確認
   - マウス操作の精度確認
   - UI応答性の確認

3. 最終品質判定
   - 全要件の充足確認
   - パフォーマンス基準の達成確認
   - integration/merge-queue/ready-for-release/への移動
```

## テスト実装

### 1. 単体テスト実行
```python
# tests/unit/test_video_processor.py
import pytest
import time
import numpy as np
from backend.video_processing_module.video_processor import VideoProcessor
from backend.video_processing_module.frame_cache import FrameCache

class TestVideoProcessor:
    """動画処理モジュール単体テスト"""
    
    def test_load_video_success(self):
        """動画読み込み成功テスト"""
        processor = VideoProcessor()
        video_info = processor.load_video("tests/data/sample.mp4")
        
        assert video_info.frame_count > 0
        assert video_info.fps > 0
        assert video_info.width > 0
        assert video_info.height > 0
        
    def test_frame_extraction_performance(self):
        """フレーム抽出性能テスト"""
        processor = VideoProcessor()
        processor.load_video("tests/data/sample.mp4")
        
        start_time = time.time()
        frame = processor.get_frame(100)
        elapsed = (time.time() - start_time) * 1000
        
        assert frame is not None
        assert elapsed < 10  # 10ms以下での取得
        
    def test_fps_conversion(self):
        """FPS変換テスト（30fps → 5fps）"""
        processor = VideoProcessor()
        processor.load_video("tests/data/sample_30fps.mp4")
        
        # 5fps抽出テスト
        extracted_frames = processor.extract_frames_for_test(target_fps=5.0)
        expected_interval = 30 / 5  # 6フレーム間隔
        
        # フレーム間隔の確認
        for i in range(1, len(extracted_frames)):
            interval = extracted_frames[i] - extracted_frames[i-1]
            assert abs(interval - expected_interval) <= 1

class TestFrameCache:
    """フレームキャッシュ単体テスト"""
    
    def test_cache_performance(self):
        """キャッシュ性能テスト"""
        cache = FrameCache(size_mb=100)
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        # キャッシュ保存
        cache.store_frame(100, test_frame)
        
        # キャッシュ取得性能測定
        start_time = time.time()
        cached_frame = cache.get_frame(100)
        elapsed = (time.time() - start_time) * 1000
        
        assert cached_frame is not None
        assert elapsed < 1  # 1ms以下でのキャッシュ取得
        
    def test_lru_eviction(self):
        """LRU削除テスト"""
        cache = FrameCache(size_mb=1)  # 小さなキャッシュ
        
        # キャッシュ満杯まで追加
        for i in range(10):
            frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            cache.store_frame(i, frame)
            
        # 最初のフレームが削除されていることを確認
        assert cache.get_frame(0) is None
        assert cache.get_frame(9) is not None
```

### 2. 統合テスト実行
```python
# tests/integration/test_ui_video_integration.py
import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from frontend.components.main_window import MainWindow
from backend.video_processing_module.video_processor import VideoProcessor

class TestUIVideoIntegration:
    """UI-動画処理統合テスト"""
    
    def test_frame_display_integration(self, qtbot):
        """フレーム表示統合テスト"""
        main_window = MainWindow()
        qtbot.addWidget(main_window)
        
        # 動画読み込み
        main_window.load_video("tests/data/sample.mp4")
        
        # フレーム表示性能測定
        start_time = time.time()
        main_window.display_frame(100)
        elapsed = (time.time() - start_time) * 1000
        
        assert elapsed < 50  # 50ms以下での表示
        
    def test_bbox_creation_integration(self, qtbot):
        """BB作成統合テスト"""
        main_window = MainWindow()
        qtbot.addWidget(main_window)
        
        main_window.load_video("tests/data/sample.mp4")
        main_window.display_frame(100)
        
        # BB作成操作
        frame_viewer = main_window.frame_viewer
        qtbot.mousePress(frame_viewer, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
        qtbot.mouseMove(frame_viewer, QPoint(200, 200))
        qtbot.mouseRelease(frame_viewer, Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
        
        # アノテーションマネージャーにBBが追加されていることを確認
        bboxes = main_window.annotation_manager.get_bboxes(100)
        assert len(bboxes) == 1
        
    def test_navigation_integration(self, qtbot):
        """ナビゲーション統合テスト"""
        main_window = MainWindow()
        qtbot.addWidget(main_window)
        
        main_window.load_video("tests/data/sample.mp4")
        
        # フレーム移動テスト
        navigation = main_window.navigation
        initial_frame = navigation.current_frame
        
        # 次フレームボタン
        qtbot.mouseClick(navigation.next_btn, Qt.MouseButton.LeftButton)
        assert navigation.current_frame == initial_frame + 1
        
        # 前フレームボタン
        qtbot.mouseClick(navigation.prev_btn, Qt.MouseButton.LeftButton)
        assert navigation.current_frame == initial_frame
```

### 3. パフォーマンステスト実行
```python
# tests/performance/test_performance_requirements.py
import pytest
import time
import psutil
import numpy as np
from backend.video_processing_module.video_processor import VideoProcessor
from frontend.components.frame_viewer import FrameViewer

class TestPerformanceRequirements:
    """パフォーマンス要件テスト"""
    
    def test_frame_switching_speed(self, qtbot):
        """フレーム切り替え速度テスト（50ms以下）"""
        viewer = FrameViewer()
        qtbot.addWidget(viewer)
        
        # テスト用フレームデータ
        test_frames = []
        for i in range(10):
            frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            test_frames.append(frame)
            
        # フレーム切り替え速度測定
        times = []
        for frame in test_frames:
            start_time = time.time()
            viewer.display_frame(frame, 0)
            elapsed = (time.time() - start_time) * 1000
            times.append(elapsed)
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 50, f"平均フレーム切り替え時間: {avg_time:.1f}ms"
        assert max_time < 100, f"最大フレーム切り替え時間: {max_time:.1f}ms"
        
    def test_bbox_drawing_speed(self, qtbot):
        """BB描画速度テスト（16ms以下）"""
        viewer = FrameViewer()
        qtbot.addWidget(viewer)
        
        # 多数のBBを作成
        bboxes = []
        for i in range(50):  # 50個のBB
            bbox = BoundingBox(
                x=np.random.random(),
                y=np.random.random(), 
                w=0.1,
                h=0.1
            )
            bbox.individual_id = i % 16
            bbox.action_id = i % 5
            bboxes.append(bbox)
            
        viewer.bboxes = bboxes
        
        # BB描画速度測定
        start_time = time.time()
        viewer.redraw_bboxes()
        elapsed = (time.time() - start_time) * 1000
        
        assert elapsed < 16, f"BB描画時間: {elapsed:.1f}ms"
        
    def test_memory_usage(self):
        """メモリ使用量テスト（20GB以内）"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 大量データ処理のシミュレーション
        processor = VideoProcessor()
        cache = FrameCache(size_mb=20480)  # 20GB
        
        # 大量フレームをキャッシュに追加
        for i in range(1000):
            frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            cache.store_frame(i, frame)
            
        final_memory = process.memory_info().rss
        memory_usage = (final_memory - initial_memory) / (1024 * 1024 * 1024)  # GB
        
        assert memory_usage < 20, f"メモリ使用量: {memory_usage:.1f}GB"
```

### 4. システムテスト実行
```python
# tests/system/test_end_to_end.py
import pytest
import os
import tempfile
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from frontend.components.main_window import MainWindow

class TestEndToEndWorkflow:
    """エンドツーエンドワークフローテスト"""
    
    def test_complete_annotation_workflow(self, qtbot):
        """完全なアノテーションワークフローテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            main_window = MainWindow()
            qtbot.addWidget(main_window)
            
            # 1. 動画読み込み
            video_path = "tests/data/sample.mp4"
            main_window.load_video(video_path)
            
            # 2. フレーム表示
            main_window.display_frame(100)
            
            # 3. BB作成
            frame_viewer = main_window.frame_viewer
            qtbot.mousePress(frame_viewer, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
            qtbot.mouseMove(frame_viewer, QPoint(200, 200))
            qtbot.mouseRelease(frame_viewer, Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
            
            # 4. ID・行動設定
            control_panel = main_window.control_panel
            qtbot.mouseClick(control_panel.individual_buttons.button(2), Qt.MouseButton.LeftButton)  # ID:2
            qtbot.mouseClick(control_panel.action_buttons.button(0), Qt.MouseButton.LeftButton)      # sit
            
            # 5. 次フレーム移動
            qtbot.mouseClick(main_window.navigation.next_btn, Qt.MouseButton.LeftButton)
            
            # 6. 自動保存確認
            annotation_file = os.path.join(temp_dir, "000100.txt")
            assert os.path.exists(annotation_file)
            
            # 7. 保存内容確認
            with open(annotation_file, 'r') as f:
                content = f.read().strip()
                assert "2" in content  # 個体ID
                assert "0" in content  # 行動ID
                
    def test_long_session_stability(self, qtbot):
        """長時間セッション安定性テスト"""
        main_window = MainWindow()
        qtbot.addWidget(main_window)
        
        main_window.load_video("tests/data/long_video.mp4")
        
        # 1000フレーム連続処理
        for i in range(1000):
            main_window.display_frame(i)
            
            # 10フレーム毎にBB作成
            if i % 10 == 0:
                frame_viewer = main_window.frame_viewer
                qtbot.mousePress(frame_viewer, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
                qtbot.mouseRelease(frame_viewer, Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
                
        # メモリリーク確認
        process = psutil.Process()
        memory_usage = process.memory_info().rss / (1024 * 1024 * 1024)
        assert memory_usage < 25  # 25GB以下
```

## テスト結果管理

### 1. テストレポート生成
```python
# testing/report_generator.py
import json
import datetime
from typing import Dict, List

class TestReportGenerator:
    """テスト結果レポート生成"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'unit_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'system_tests': {}
        }
        
    def add_unit_test_result(self, module: str, passed: int, failed: int, coverage: float):
        """単体テスト結果追加"""
        self.results['unit_tests'][module] = {
            'passed': passed,
            'failed': failed,
            'coverage': coverage,
            'status': 'PASS' if failed == 0 else 'FAIL'
        }
        
    def add_performance_result(self, test_name: str, measured_value: float, 
                              threshold: float, unit: str):
        """パフォーマンステスト結果追加"""
        self.results['performance_tests'][test_name] = {
            'measured': measured_value,
            'threshold': threshold,
            'unit': unit,
            'status': 'PASS' if measured_value <= threshold else 'FAIL'
        }
        
    def generate_report(self, output_path: str):
        """レポート生成"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
            
    def generate_summary(self) -> str:
        """サマリー生成"""
        total_tests = 0
        failed_tests = 0
        
        for category in ['unit_tests', 'integration_tests', 'performance_tests', 'system_tests']:
            for test_name, result in self.results[category].items():
                total_tests += 1
                if result.get('status') == 'FAIL':
                    failed_tests += 1
                    
        success_rate = ((total_tests - failed_tests) / total_tests * 100) if total_tests > 0 else 0
        
        return f"""
テスト実行サマリー
================
実行日時: {self.results['timestamp']}
総テスト数: {total_tests}
成功: {total_tests - failed_tests}
失敗: {failed_tests}
成功率: {success_rate:.1f}%
"""
```

### 2. 品質ゲート判定
```python
# testing/quality_gate.py
class QualityGate:
    """品質ゲート判定"""
    
    def __init__(self):
        self.criteria = {
            'unit_test_coverage': 80.0,      # 80%以上
            'unit_test_pass_rate': 100.0,    # 100%
            'integration_test_pass_rate': 100.0,  # 100%
            'frame_switch_time': 50.0,        # 50ms以下
            'bbox_draw_time': 16.0,           # 16ms以下
            'memory_usage': 20.0,             # 20GB以下
            'system_test_pass_rate': 100.0    # 100%
        }
        
    def evaluate(self, test_results: Dict) -> bool:
        """品質ゲート評価"""
        failed_criteria = []
        
        # 各基準をチェック
        for criterion, threshold in self.criteria.items():
            if not self._check_criterion(test_results, criterion, threshold):
                failed_criteria.append(criterion)
                
        if failed_criteria:
            self._log_failures(failed_criteria)
            return False
            
        return True
        
    def _check_criterion(self, results: Dict, criterion: str, threshold: float) -> bool:
        """個別基準チェック"""
        if criterion == 'unit_test_coverage':
            avg_coverage = self._calculate_average_coverage(results.get('unit_tests', {}))
            return avg_coverage >= threshold
            
        elif criterion == 'frame_switch_time':
            frame_time = results.get('performance_tests', {}).get('frame_switching', {}).get('measured', 999)
            return frame_time <= threshold
            
        # 他の基準も同様に実装
        return True
        
    def _log_failures(self, failed_criteria: List[str]):
        """失敗基準をログに記録"""
        with open('logs/test-execution-logs/quality_gate_failures.log', 'a') as f:
            timestamp = datetime.datetime.now().isoformat()
            f.write(f"{timestamp}: Failed criteria: {', '.join(failed_criteria)}\n")
```

## 自動化・CI/CD統合

### 1. テスト自動実行
```bash
#!/bin/bash
# scripts/run_all_tests.sh

echo "=== オートアノテーションアプリ テスト実行 ==="

# 1. 単体テスト実行
echo "単体テスト実行中..."
pytest testing/test-code/unit/ --cov=implementation/src/ --cov-report=html
UNIT_EXIT_CODE=$?

# 2. 統合テスト実行
echo "統合テスト実行中..."
pytest testing/test-code/integration/
INTEGRATION_EXIT_CODE=$?

# 3. パフォーマンステスト実行
echo "パフォーマンステスト実行中..."
pytest testing/test-code/performance/ -v
PERFORMANCE_EXIT_CODE=$?

# 4. システムテスト実行
echo "システムテスト実行中..."
pytest testing/test-code/e2e/ -v
SYSTEM_EXIT_CODE=$?

# 5. レポート生成
python testing/generate_report.py

# 6. 品質ゲート判定
python testing/quality_gate_check.py

echo "=== テスト実行完了 ==="
```

## 他Agentとの連携

### test-design-agent →
- **テストコード**: 実行対象のテストスクリプト
- **判定基準**: 合格/不合格の判定基準
- **環境設定**: テスト実行環境の要件

### → integration-agent
- **テスト結果**: 各段階のテスト結果
- **品質判定**: 統合可否の判定結果
- **改善要求**: 発見した問題と修正要求

### ↔ backend-agent / frontend-agent
- **不具合報告**: 発見した問題の詳細報告
- **修正確認**: 修正後の再テスト実行
- **品質フィードバック**: 品質向上のための提案

## チェックリスト

### テスト実行完了チェック
- [ ] 単体テスト全モジュール実行完了
- [ ] 統合テスト全パターン実行完了
- [ ] パフォーマンステスト全項目実行完了
- [ ] システムテスト全シナリオ実行完了
- [ ] 品質ゲート全基準クリア
- [ ] テストレポート生成完了
- [ ] チェックリスト自動更新完了
- [ ] integration-agentへの結果通知完了