# Agent8: Monitoring Layer 詳細仕様書（監視・デバッグAgent）

## 🎯 Agent8 Monitoring の使命
**パフォーマンス監視・ログ・デバッグ・システム健全性** - 品質保証の番人

## 📋 Agent8開始時の必須確認項目

### 開発開始前チェックリスト
- [ ] CLAUDE.md読了（Agent8責任範囲確認）
- [ ] requirement.yaml確認（監視要件理解）
- [ ] config/performance_targets.yaml確認（監視目標・閾値）
- [ ] config/layer_interfaces.yaml確認（全Agent監視対象）
- [ ] tests/requirements/unit/monitoring-unit-tests.md確認（テスト要件）

### Agent8専門領域
```
責任範囲: パフォーマンス監視・ログ管理・デバッグ支援・システム健全性
技術領域: メトリクス収集、ログ分析、アラート、プロファイリング
実装場所: src/monitoring/
テスト場所: tests/unit/test_monitoring/
監視対象: 全8Agent（特にCache Agent重点監視）
```

## 🏗️ 実装すべきコンポーネント詳細

### 1. performance/ - パフォーマンス監視
```
src/monitoring/performance/
├── __init__.py
├── frame_timer.py         # フレーム切り替え時間測定
├── memory_profiler.py     # メモリ使用量監視
└── performance_logger.py  # パフォーマンスログ記録
```

#### frame_timer.py 仕様
```python
class FrameTimer:
    """
    フレーム切り替え時間測定（最重要監視）
    
    監視項目:
    - フレーム切り替え時間（50ms以下監視）
    - Cache層応答時間
    - UI更新時間
    - 全体レスポンス時間
    """
    
    def __init__(self):
        self.frame_switch_times = deque(maxlen=1000)  # 直近1000回記録
        self.performance_threshold = 50.0  # 50ms閾値
        self.warning_threshold = 45.0      # 45ms警告
        
    def start_frame_switch_measurement(self, frame_id: str) -> str:
        """
        フレーム切り替え測定開始
        
        Args:
            frame_id: 切り替え先フレームID
            
        Returns:
            str: 測定セッションID
        """
        session_id = str(uuid.uuid4())
        measurement = FrameSwitchMeasurement(
            session_id=session_id,
            frame_id=frame_id,
            start_time=time.perf_counter(),
            cache_start_time=None,
            cache_end_time=None,
            ui_start_time=None,
            ui_end_time=None,
            end_time=None
        )
        
        self.active_measurements[session_id] = measurement
        return session_id
        
    def record_cache_timing(self, session_id: str, cache_start: bool = True):
        """Cache層タイミング記録"""
        if session_id in self.active_measurements:
            measurement = self.active_measurements[session_id]
            if cache_start:
                measurement.cache_start_time = time.perf_counter()
            else:
                measurement.cache_end_time = time.perf_counter()
                
    def record_ui_timing(self, session_id: str, ui_start: bool = True):
        """UI層タイミング記録"""
        if session_id in self.active_measurements:
            measurement = self.active_measurements[session_id]
            if ui_start:
                measurement.ui_start_time = time.perf_counter()
            else:
                measurement.ui_end_time = time.perf_counter()
                
    def end_frame_switch_measurement(self, session_id: str) -> FrameSwitchResult:
        """
        フレーム切り替え測定終了
        
        Returns:
            FrameSwitchResult: 測定結果
        """
        if session_id not in self.active_measurements:
            raise MonitoringError(f"Measurement session not found: {session_id}")
            
        measurement = self.active_measurements[session_id]
        measurement.end_time = time.perf_counter()
        
        # 時間計算
        total_time = (measurement.end_time - measurement.start_time) * 1000  # ms
        cache_time = None
        ui_time = None
        
        if measurement.cache_start_time and measurement.cache_end_time:
            cache_time = (measurement.cache_end_time - measurement.cache_start_time) * 1000
            
        if measurement.ui_start_time and measurement.ui_end_time:
            ui_time = (measurement.ui_end_time - measurement.ui_start_time) * 1000
            
        # 結果記録
        result = FrameSwitchResult(
            frame_id=measurement.frame_id,
            total_time=total_time,
            cache_time=cache_time,
            ui_time=ui_time,
            success=total_time <= self.performance_threshold
        )
        
        self.frame_switch_times.append(result)
        
        # 警告チェック
        if total_time > self.warning_threshold:
            self._emit_performance_warning(result)
            
        # クリーンアップ
        del self.active_measurements[session_id]
        
        return result
        
    def get_performance_statistics(self) -> FramePerformanceStats:
        """フレーム切り替え性能統計"""
        if not self.frame_switch_times:
            return FramePerformanceStats()
            
        times = [result.total_time for result in self.frame_switch_times]
        
        return FramePerformanceStats(
            total_measurements=len(times),
            average_time=statistics.mean(times),
            median_time=statistics.median(times),
            min_time=min(times),
            max_time=max(times),
            std_deviation=statistics.stdev(times) if len(times) > 1 else 0.0,
            success_rate=sum(1 for result in self.frame_switch_times if result.success) / len(times),
            under_50ms_rate=sum(1 for time in times if time <= 50.0) / len(times)
        )
        
    def _emit_performance_warning(self, result: FrameSwitchResult):
        """性能警告発信"""
        warning_data = {
            "metric_name": "frame_switching_time",
            "value": result.total_time,
            "threshold": self.performance_threshold,
            "frame_id": result.frame_id,
            "severity": "error" if result.total_time > self.performance_threshold else "warning"
        }
        
        # Data Bus経由で警告発信
        self.data_bus.publish("performance_warning", warning_data)
```

#### memory_profiler.py 仕様
```python
class MemoryProfiler:
    """
    メモリ使用量監視・プロファイラー
    
    監視項目:
    - 総メモリ使用量（20GB上限監視）
    - Agent別メモリ使用量
    - メモリリーク検知
    - ガベージコレクション効率
    """
    
    def __init__(self):
        self.memory_limit = 20 * 1024 ** 3  # 20GB
        self.warning_threshold = 18 * 1024 ** 3  # 18GB
        self.monitoring_interval = 1.0  # 1秒間隔
        self.memory_history = deque(maxlen=3600)  # 1時間分記録
        
    def start_monitoring(self):
        """メモリ監視開始"""
        self.monitoring_thread = threading.Thread(target=self._monitoring_worker)
        self.monitoring_thread.daemon = True
        self.is_monitoring = True
        self.monitoring_thread.start()
        
    def stop_monitoring(self):
        """メモリ監視停止"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
            
    def get_current_memory_usage(self) -> MemoryUsage:
        """現在メモリ使用量取得"""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return MemoryUsage(
            rss=memory_info.rss,  # 実使用メモリ
            vms=memory_info.vms,  # 仮想メモリ
            percent=process.memory_percent(),
            system_total=system_memory.total,
            system_available=system_memory.available,
            system_used=system_memory.used,
            timestamp=datetime.now()
        )
        
    def detect_memory_leak(self, window_size: int = 300) -> MemoryLeakResult:
        """
        メモリリーク検知（5分間ウィンドウ）
        
        Args:
            window_size: 検知ウィンドウサイズ（秒）
            
        Returns:
            MemoryLeakResult: リーク検知結果
        """
        if len(self.memory_history) < window_size:
            return MemoryLeakResult(leak_detected=False, reason="Insufficient data")
            
        # 最近の記録を分析
        recent_usage = list(self.memory_history)[-window_size:]
        memory_values = [usage.rss for usage in recent_usage]
        
        # 線形回帰で傾向分析
        x = list(range(len(memory_values)))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, memory_values)
        
        # リーク判定基準
        # 1. 正の傾き（メモリ増加傾向）
        # 2. 相関係数が高い（一貫した増加）
        # 3. 増加率が閾値以上
        leak_detected = (
            slope > 1024 * 1024 and  # 1MB/秒以上の増加
            r_value > 0.7 and        # 高い相関
            p_value < 0.05           # 統計的有意性
        )
        
        return MemoryLeakResult(
            leak_detected=leak_detected,
            slope=slope,
            correlation=r_value,
            p_value=p_value,
            growth_rate_mb_per_sec=slope / (1024 * 1024),
            estimated_time_to_limit=self._estimate_time_to_limit(slope, memory_values[-1])
        )
        
    def _monitoring_worker(self):
        """メモリ監視ワーカー"""
        while self.is_monitoring:
            try:
                # メモリ使用量記録
                memory_usage = self.get_current_memory_usage()
                self.memory_history.append(memory_usage)
                
                # 警告チェック
                if memory_usage.rss > self.warning_threshold:
                    self._emit_memory_warning(memory_usage)
                    
                # リークチェック（5分毎）
                if len(self.memory_history) % 300 == 0:
                    leak_result = self.detect_memory_leak()
                    if leak_result.leak_detected:
                        self._emit_memory_leak_alert(leak_result)
                        
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self._log_monitoring_error(e)
                
    def _emit_memory_warning(self, memory_usage: MemoryUsage):
        """メモリ警告発信"""
        warning_data = {
            "metric_name": "memory_usage",
            "value": memory_usage.rss,
            "threshold": self.memory_limit,
            "usage_gb": memory_usage.rss / (1024 ** 3),
            "severity": "error" if memory_usage.rss > self.memory_limit else "warning"
        }
        
        self.data_bus.publish("performance_warning", warning_data)
```

### 2. health/ - システム健全性監視
```
src/monitoring/health/
├── __init__.py
├── system_health.py       # システム健全性チェック
└── error_tracker.py       # エラー追跡・分析
```

#### system_health.py 仕様
```python
class SystemHealthMonitor:
    """
    システム健全性監視
    
    監視項目:
    - CPU使用率
    - ディスク使用量・I/O
    - ネットワーク状態
    - Agent間通信健全性
    """
    
    def __init__(self):
        self.health_checks = {
            'cpu_usage': self._check_cpu_usage,
            'disk_usage': self._check_disk_usage,
            'memory_usage': self._check_memory_usage,
            'agent_communication': self._check_agent_communication,
            'file_system': self._check_file_system,
            'cache_performance': self._check_cache_performance
        }
        
    def perform_health_check(self) -> SystemHealthResult:
        """総合健全性チェック"""
        health_results = {}
        overall_status = "healthy"
        
        for check_name, check_func in self.health_checks.items():
            try:
                result = check_func()
                health_results[check_name] = result
                
                if result.status == "critical":
                    overall_status = "critical"
                elif result.status == "warning" and overall_status == "healthy":
                    overall_status = "warning"
                    
            except Exception as e:
                health_results[check_name] = HealthCheckResult(
                    status="error",
                    message=f"Health check failed: {e}",
                    details={"error": str(e)}
                )
                overall_status = "critical"
                
        return SystemHealthResult(
            overall_status=overall_status,
            check_results=health_results,
            timestamp=datetime.now()
        )
        
    def _check_cpu_usage(self) -> HealthCheckResult:
        """CPU使用率チェック"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 90:
            return HealthCheckResult("critical", f"High CPU usage: {cpu_percent}%")
        elif cpu_percent > 70:
            return HealthCheckResult("warning", f"Moderate CPU usage: {cpu_percent}%")
        else:
            return HealthCheckResult("healthy", f"Normal CPU usage: {cpu_percent}%")
            
    def _check_cache_performance(self) -> HealthCheckResult:
        """Cache性能チェック（最重要）"""
        # Cache層から統計取得
        cache_stats = self._get_cache_statistics()
        
        if cache_stats.hit_rate < 0.90:
            return HealthCheckResult("critical", 
                f"Low cache hit rate: {cache_stats.hit_rate:.2%}")
        elif cache_stats.hit_rate < 0.95:
            return HealthCheckResult("warning",
                f"Moderate cache hit rate: {cache_stats.hit_rate:.2%}")
        else:
            return HealthCheckResult("healthy",
                f"Good cache hit rate: {cache_stats.hit_rate:.2%}")
```

### 3. debugging/ - デバッグ支援
```
src/monitoring/debugging/
├── __init__.py
├── debug_logger.py        # デバッグログ記録
└── trace_collector.py     # トレース情報収集
```

#### debug_logger.py 仕様
```python
class DebugLogger:
    """
    デバッグログ記録・分析
    
    機能:
    - 階層化ログ（DEBUG/INFO/WARNING/ERROR）
    - Agent別ログ分離
    - 構造化ログ（JSON形式）
    - リアルタイムログ監視
    """
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = getattr(logging, log_level.upper())
        self.setup_logging()
        
    def setup_logging(self):
        """ログ設定"""
        # 構造化ログフォーマット
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        
        # ファイルハンドラー（Agent別）
        self.file_handlers = {}
        for agent_name in ['cache', 'presentation', 'application', 
                          'domain', 'infrastructure', 'data_bus', 
                          'persistence', 'monitoring']:
            handler = logging.FileHandler(f'logs/{agent_name}_agent.log')
            handler.setFormatter(formatter)
            self.file_handlers[agent_name] = handler
            
        # 統合ログハンドラー
        self.main_handler = logging.FileHandler('logs/system.log')
        self.main_handler.setFormatter(formatter)
        
        # コンソールハンドラー（開発時）
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(formatter)
        
    def log_agent_event(self, agent_name: str, level: str, 
                       message: str, extra_data: dict = None):
        """Agent別イベントログ"""
        logger = logging.getLogger(f"agent.{agent_name}")
        logger.setLevel(self.log_level)
        
        if agent_name in self.file_handlers:
            logger.addHandler(self.file_handlers[agent_name])
            
        # 構造化データ追加
        log_data = {
            "agent": agent_name,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if extra_data:
            log_data.update(extra_data)
            
        log_message = json.dumps(log_data, ensure_ascii=False)
        
        # レベル別ログ出力
        if level.upper() == "DEBUG":
            logger.debug(log_message)
        elif level.upper() == "INFO":
            logger.info(log_message)
        elif level.upper() == "WARNING":
            logger.warning(log_message)
        elif level.upper() == "ERROR":
            logger.error(log_message)
            
    def log_performance_event(self, operation: str, duration: float,
                             agent_name: str, success: bool = True):
        """パフォーマンスイベントログ"""
        perf_data = {
            "operation": operation,
            "duration_ms": duration,
            "agent": agent_name,
            "success": success,
            "performance_category": "timing"
        }
        
        level = "INFO" if success else "WARNING"
        self.log_agent_event(agent_name, level, 
                           f"Performance: {operation}", perf_data)
```

## ⚡ パフォーマンス要件詳細

### 監視性能目標
```yaml
metrics_collection:
  target: "10ms以下"
  frequency: "リアルタイム〜1分毎"
  metrics: ["CPU", "メモリ", "I/O", "フレーム時間"]
  
log_recording:
  target: "5ms以下"
  levels: ["DEBUG", "INFO", "WARNING", "ERROR"]
  output: ["ファイル", "標準出力"]
  
monitoring_overhead:
  target: "全体の2%以下"
  measurement: "監視時間/総処理時間"
  
alert_response:
  target: "1ms以下"
  conditions: ["メモリ上限", "性能劣化", "エラー発生"]
```

## 🧪 テスト要件（TDD必須）

### 単体テスト必須項目
```python
# tests/unit/test_monitoring/test_frame_timer.py
class TestFrameTimer:
    def test_frame_timing_accuracy(self):
        """フレーム時間測定精度確認"""
        
    def test_performance_warning_trigger(self):
        """性能警告発信確認"""
        
    def test_statistics_calculation(self):
        """統計計算正確性確認"""

# tests/unit/test_monitoring/test_memory_profiler.py
class TestMemoryProfiler:
    def test_memory_leak_detection(self):
        """メモリリーク検知確認"""
        
    def test_monitoring_overhead_2_percent(self):
        """監視オーバーヘッド2%以下確認"""
        
    def test_memory_warning_threshold(self):
        """メモリ警告閾値確認"""
```

## ✅ Agent8完了条件

### 機能完了チェック
- [ ] フレーム切り替え時間測定（50ms監視）
- [ ] メモリ使用量監視（20GB上限）
- [ ] システム健全性チェック
- [ ] デバッグログ記録・分析

### 性能完了チェック
- [ ] メトリクス収集10ms以下
- [ ] ログ記録5ms以下
- [ ] 監視オーバーヘッド2%以下
- [ ] アラート応答1ms以下

### テスト完了チェック
- [ ] 単体テスト100%通過
- [ ] 監視精度テスト100%通過
- [ ] オーバーヘッドテスト通過
- [ ] 警告システムテスト通過

---

**Agent8 Monitoringは、システム全体の品質保証を担います。特にCache Agentのフレーム切り替え50ms以下達成を継続監視し、パフォーマンス劣化を早期発見・対処することで、高品質なアノテーション体験を維持します。**