# Agent7: Persistence Layer 詳細仕様書（データ永続化Agent）

## 🎯 Agent7 Persistence の使命
**データ保存・ファイル管理・永続化・バックアップ** - データ整合性保証

## 📋 Agent7開始時の必須確認項目

### 開発開始前チェックリスト
- [ ] CLAUDE.md読了（Agent7責任範囲確認）
- [ ] requirement.yaml確認（データ要件理解）
- [ ] config/performance_targets.yaml確認（保存性能目標100ms）
- [ ] config/layer_interfaces.yaml確認（Domain層連携）
- [ ] tests/requirements/unit/persistence-unit-tests.md確認（テスト要件）

### Agent7専門領域
```
責任範囲: データ保存・ファイル管理・永続化・バックアップ・設定管理
技術領域: ファイルI/O、YOLO形式、JSON、自動保存、ディレクトリ監視
実装場所: src/persistence/
テスト場所: tests/unit/test_persistence/
```

## 🏗️ 実装すべきコンポーネント詳細

### 1. file_io/ - ファイル入出力
```
src/persistence/file_io/
├── __init__.py
├── txt_handler.py         # YOLO txtファイル処理
├── yolo_converter.py      # YOLO形式変換
├── json_handler.py        # JSON設定ファイル処理
└── batch_writer.py        # 一括書き込み最適化
```

#### txt_handler.py 仕様
```python
class YOLOTxtHandler:
    """
    YOLO形式txtファイル処理
    
    性能要件:
    - ファイル保存: 100ms以下
    - ファイル読み込み: 50ms以下
    - データ検証: 完全性保証
    - エンコーディング: UTF-8統一
    """
    
    def __init__(self):
        self.encoding = 'utf-8'
        self.line_ending = '\n'  # Unix形式
        
    def save_annotations(self, frame_id: str, bb_entities: List[BBEntity],
                        output_dir: str) -> bool:
        """
        アノテーション保存（100ms以下必達）
        
        フォーマット例:
        0 0.5123 0.3456 0.1234 0.0987 2 0.9512
        1 0.2345 0.7890 0.0876 0.1234 0 0.8743
        
        Args:
            frame_id: フレームID（000000形式）
            bb_entities: BBエンティティリスト
            output_dir: 出力ディレクトリ
            
        Returns:
            bool: 保存成功フラグ
        """
        file_path = os.path.join(output_dir, f"{frame_id}.txt")
        
        try:
            with open(file_path, 'w', encoding=self.encoding) as f:
                for bb in bb_entities:
                    line = self._format_yolo_line(bb)
                    f.write(line + self.line_ending)
            return True
        except Exception as e:
            raise PersistenceError(f"Failed to save annotations: {e}")
            
    def load_annotations(self, frame_id: str, annotations_dir: str) -> List[BBEntity]:
        """
        アノテーション読み込み（50ms以下必達）
        
        Returns:
            List[BBEntity]: BBエンティティリスト
        """
        file_path = os.path.join(annotations_dir, f"{frame_id}.txt")
        
        if not os.path.exists(file_path):
            return []  # アノテーションファイルなし
            
        bb_entities = []
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:  # 空行スキップ
                        continue
                        
                    bb_entity = self._parse_yolo_line(line, frame_id, line_num)
                    bb_entities.append(bb_entity)
                    
        except Exception as e:
            raise PersistenceError(f"Failed to load annotations: {e}")
            
        return bb_entities
        
    def _format_yolo_line(self, bb: BBEntity) -> str:
        """BBエンティティ→YOLO行変換"""
        return f"{bb.individual_id} {bb.coordinates.x:.4f} {bb.coordinates.y:.4f} " \
               f"{bb.coordinates.w:.4f} {bb.coordinates.h:.4f} " \
               f"{bb.action_id} {bb.confidence:.4f}"
               
    def _parse_yolo_line(self, line: str, frame_id: str, line_num: int) -> BBEntity:
        """YOLO行→BBエンティティ変換"""
        parts = line.split()
        if len(parts) != 7:
            raise PersistenceError(f"Invalid YOLO format at line {line_num}: {line}")
            
        try:
            individual_id = int(parts[0])
            x, y, w, h = map(float, parts[1:5])
            action_id = int(parts[5])
            confidence = float(parts[6])
            
            # データ検証
            self._validate_yolo_data(individual_id, x, y, w, h, action_id, confidence, line_num)
            
            return BBEntity(
                id=str(uuid.uuid4()),
                frame_id=frame_id,
                individual_id=individual_id,
                action_id=action_id,
                coordinates=Coordinates(x, y, w, h),
                confidence=confidence,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
        except ValueError as e:
            raise PersistenceError(f"Invalid data format at line {line_num}: {e}")
            
    def _validate_yolo_data(self, individual_id: int, x: float, y: float, w: float, h: float,
                          action_id: int, confidence: float, line_num: int):
        """YOLOデータ検証"""
        if not 0 <= individual_id <= 15:
            raise PersistenceError(f"Invalid individual_id at line {line_num}: {individual_id}")
        if not all(0.0 <= coord <= 1.0 for coord in [x, y, w, h]):
            raise PersistenceError(f"Invalid coordinates at line {line_num}: {x},{y},{w},{h}")
        if not 0 <= action_id <= 4:
            raise PersistenceError(f"Invalid action_id at line {line_num}: {action_id}")
        if not 0.0 <= confidence <= 1.0:
            raise PersistenceError(f"Invalid confidence at line {line_num}: {confidence}")
```

#### json_handler.py 仕様
```python
class JSONHandler:
    """
    JSON設定ファイル処理
    
    性能要件:
    - JSON保存: 30ms以下
    - JSON読み込み: 20ms以下
    - データ検証: スキーマ検証
    - エラー処理: 詳細エラー情報
    """
    
    def save_project_config(self, project: ProjectEntity, config_path: str) -> bool:
        """
        プロジェクト設定保存（30ms以下必達）
        
        Args:
            project: プロジェクトエンティティ
            config_path: 設定ファイルパス
            
        Returns:
            bool: 保存成功フラグ
        """
        config_data = {
            "project_info": {
                "name": project.name,
                "version": project.version,
                "created": project.created_at.isoformat(),
                "last_modified": datetime.now().isoformat(),
                "video_source": project.video_source,
                "frame_output": project.frame_output,
                "annotation_output": project.annotation_output,
                "backup_path": project.backup_path,
                "total_frames": project.total_frames,
                "annotated_frames": project.annotated_frames,
                "frame_rate_original": project.frame_rate_original,
                "frame_rate_target": project.frame_rate_target,
                "resolution": {
                    "width": project.resolution_width,
                    "height": project.resolution_height
                }
            },
            "annotation_config": project.annotation_config,
            "tracking_config": project.tracking_config,
            "performance_config": project.performance_config,
            "ui_config": project.ui_config,
            "export_config": project.export_config
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            raise PersistenceError(f"Failed to save project config: {e}")
            
    def load_project_config(self, config_path: str) -> ProjectEntity:
        """
        プロジェクト設定読み込み（20ms以下必達）
        
        Returns:
            ProjectEntity: プロジェクトエンティティ
        """
        if not os.path.exists(config_path):
            raise PersistenceError(f"Project config not found: {config_path}")
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # スキーマ検証
            self._validate_project_config_schema(config_data)
            
            # ProjectEntity生成
            return self._create_project_entity_from_config(config_data)
            
        except json.JSONDecodeError as e:
            raise PersistenceError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise PersistenceError(f"Failed to load project config: {e}")
```

### 2. backup/ - バックアップ・復旧
```
src/persistence/backup/
├── __init__.py
├── auto_saver.py          # 自動保存
├── backup_manager.py      # バックアップ管理
└── recovery_system.py     # 復旧システム
```

#### auto_saver.py 仕様
```python
class AutoSaver:
    """
    自動保存システム
    
    機能:
    - フレーム切り替え時自動保存
    - 差分保存（変更検知）
    - 非同期保存（UIブロックなし）
    - 保存失敗時リトライ
    """
    
    def __init__(self, save_interval: int = 30):
        self.save_interval = save_interval  # 秒
        self.pending_saves = queue.Queue()
        self.auto_save_thread = None
        self.is_running = False
        
    def start_auto_save(self):
        """自動保存開始"""
        self.is_running = True
        self.auto_save_thread = threading.Thread(target=self._auto_save_worker)
        self.auto_save_thread.daemon = True
        self.auto_save_thread.start()
        
    def stop_auto_save(self):
        """自動保存停止"""
        self.is_running = False
        if self.auto_save_thread:
            self.auto_save_thread.join()
            
    def schedule_save(self, frame_id: str, bb_entities: List[BBEntity],
                     priority: str = "normal"):
        """
        保存スケジュール（非同期）
        
        Args:
            frame_id: フレームID
            bb_entities: BBエンティティリスト
            priority: high/normal/low
        """
        save_task = SaveTask(
            frame_id=frame_id,
            bb_entities=bb_entities,
            priority=priority,
            timestamp=time.time()
        )
        self.pending_saves.put(save_task)
        
    def _auto_save_worker(self):
        """自動保存ワーカー（バックグラウンド実行）"""
        while self.is_running:
            try:
                # 高優先度タスク処理
                save_task = self.pending_saves.get(timeout=self.save_interval)
                self._execute_save_task(save_task)
                
            except queue.Empty:
                # 定期保存実行
                self._execute_periodic_save()
                
            except Exception as e:
                # エラーログ記録（Monitoring層に通知）
                self._report_save_error(e)
                
    def _execute_save_task(self, save_task: SaveTask):
        """保存タスク実行"""
        try:
            txt_handler = YOLOTxtHandler()
            success = txt_handler.save_annotations(
                save_task.frame_id,
                save_task.bb_entities,
                self.annotation_output_dir
            )
            
            if success:
                self._report_save_success(save_task)
            else:
                self._retry_save_task(save_task)
                
        except Exception as e:
            self._retry_save_task(save_task, error=e)
```

#### backup_manager.py 仕様
```python
class BackupManager:
    """
    バックアップ管理システム
    
    機能:
    - 5分毎自動バックアップ
    - 差分バックアップ（変更ファイルのみ）
    - 圧縮バックアップ
    - 世代管理（古いバックアップ自動削除）
    """
    
    def __init__(self, backup_interval: int = 300):  # 5分
        self.backup_interval = backup_interval
        self.max_backup_generations = 10
        self.compression_enabled = True
        
    def create_backup(self, source_dir: str, backup_name: str = None) -> str:
        """
        バックアップ作成
        
        Args:
            source_dir: バックアップ元ディレクトリ
            backup_name: バックアップ名（None時は自動生成）
            
        Returns:
            str: バックアップパス
        """
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        backup_path = os.path.join(self.backup_root_dir, backup_name)
        
        try:
            if self.compression_enabled:
                backup_path += ".zip"
                self._create_compressed_backup(source_dir, backup_path)
            else:
                self._create_directory_backup(source_dir, backup_path)
                
            # 古いバックアップ削除
            self._cleanup_old_backups()
            
            return backup_path
            
        except Exception as e:
            raise PersistenceError(f"Backup creation failed: {e}")
            
    def restore_backup(self, backup_path: str, restore_dir: str) -> bool:
        """
        バックアップ復旧
        
        Args:
            backup_path: バックアップファイルパス
            restore_dir: 復旧先ディレクトリ
            
        Returns:
            bool: 復旧成功フラグ
        """
        
    def list_available_backups(self) -> List[BackupInfo]:
        """利用可能バックアップ一覧"""
        
    def _create_compressed_backup(self, source_dir: str, backup_path: str):
        """圧縮バックアップ作成"""
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
```

### 3. directory/ - ディレクトリ監視
```
src/persistence/directory/
├── __init__.py
├── directory_watcher.py   # ディレクトリ監視
├── file_monitor.py        # ファイル変更監視
└── sync_manager.py        # 同期管理
```

#### directory_watcher.py 仕様
```python
class DirectoryWatcher:
    """
    ディレクトリ監視システム
    
    機能:
    - ファイル作成・更新・削除監視
    - リアルタイム変更検知
    - 外部変更との同期
    - 競合状態解決
    """
    
    def __init__(self, watch_directories: List[str]):
        self.watch_directories = watch_directories
        self.event_handler = FileSystemEventHandler()
        self.observer = Observer()
        
    def start_watching(self):
        """監視開始"""
        for watch_dir in self.watch_directories:
            self.observer.schedule(
                self.event_handler,
                watch_dir,
                recursive=True
            )
        self.observer.start()
        
    def stop_watching(self):
        """監視停止"""
        self.observer.stop()
        self.observer.join()
        
    def on_file_created(self, file_path: str):
        """ファイル作成イベント処理"""
        
    def on_file_modified(self, file_path: str):
        """ファイル更新イベント処理"""
        
    def on_file_deleted(self, file_path: str):
        """ファイル削除イベント処理"""
```

## ⚡ パフォーマンス要件詳細

### ファイルI/O性能目標
```yaml
file_save:
  target: "100ms以下"
  breakdown:
    txt_write: "50ms以下"
    json_save: "30ms以下"
    file_sync: "20ms以下"
    
auto_save:
  target: "非同期・フレーム切り替え毎"
  frequency: "フレーム切り替え時"
  mode: "バックグラウンド非同期"
  
backup:
  target: "5分毎・非同期"
  scope: "変更ファイルのみ"
  compression: "効率的圧縮"
  
directory_monitoring:
  target: "リアルタイム同期"
  events: ["作成", "更新", "削除"]
```

### I/O最適化戦略
```python
class IOOptimizer:
    """I/O最適化"""
    
    @staticmethod
    def optimize_file_write(file_path: str, data: str):
        """最適化ファイル書き込み"""
        # バッファリング最適化
        with open(file_path, 'w', encoding='utf-8', buffering=8192) as f:
            f.write(data)
            f.flush()  # 即座同期
            os.fsync(f.fileno())  # OS同期
            
    @staticmethod
    def batch_file_operations(operations: List[FileOperation]):
        """一括ファイル操作（効率化）"""
        # 同一ディレクトリ操作をまとめて実行
        grouped_ops = defaultdict(list)
        for op in operations:
            grouped_ops[os.path.dirname(op.file_path)].append(op)
            
        for directory, ops in grouped_ops.items():
            with os.scandir(directory):  # ディレクトリキャッシュ
                for op in ops:
                    op.execute()
```

## 🧪 テスト要件（TDD必須）

### 単体テスト必須項目
```python
# tests/unit/test_persistence/test_txt_handler.py
class TestYOLOTxtHandler:
    def test_save_annotations_100ms(self):
        """アノテーション保存100ms以下確認"""
        
    def test_load_annotations_50ms(self):
        """アノテーション読み込み50ms以下確認"""
        
    def test_yolo_format_accuracy(self):
        """YOLO形式精度確認"""
        
    def test_data_validation(self):
        """データ検証確認"""

# tests/unit/test_persistence/test_auto_saver.py
class TestAutoSaver:
    def test_async_save_non_blocking(self):
        """非同期保存・UIブロックなし確認"""
        
    def test_save_retry_mechanism(self):
        """保存リトライ機能確認"""
        
    def test_differential_save(self):
        """差分保存確認"""

# tests/unit/test_persistence/test_backup_manager.py
class TestBackupManager:
    def test_backup_creation_5min_interval(self):
        """5分毎バックアップ作成確認"""
        
    def test_backup_restoration_accuracy(self):
        """バックアップ復旧精度確認"""
        
    def test_generation_management(self):
        """世代管理確認"""
```

## ✅ Agent7完了条件

### 機能完了チェック
- [ ] YOLO txtファイル読み書き
- [ ] JSON設定ファイル管理
- [ ] 自動保存（フレーム切り替え毎）
- [ ] バックアップ・復旧システム

### 性能完了チェック
- [ ] ファイル保存100ms以下
- [ ] 自動保存非同期実行
- [ ] バックアップ5分毎・非同期
- [ ] ディレクトリ監視リアルタイム

### テスト完了チェック
- [ ] 単体テスト100%通過
- [ ] ファイルI/O性能テスト通過
- [ ] データ整合性テスト100%通過
- [ ] バックアップ・復旧テスト通過

---

**Agent7 Persistenceは、データの永続化と整合性を保証します。高速で信頼性の高いファイルI/Oにより、ユーザーの作業成果を確実に保護し、いつでも復旧可能な状態を維持します。**