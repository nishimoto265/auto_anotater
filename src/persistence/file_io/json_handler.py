"""
JSON設定ファイル処理
30ms保存・20ms読み込み目標達成
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from ..exceptions import FileIOError, ValidationError, PerformanceError


@dataclass
class ProjectEntity:
    """プロジェクトエンティティ"""
    name: str
    version: str
    created_at: datetime
    video_source: str
    frame_output: str
    annotation_output: str
    backup_path: str
    total_frames: int
    annotated_frames: int
    frame_rate_original: float
    frame_rate_target: float
    resolution_width: int
    resolution_height: int
    annotation_config: Dict[str, Any]
    tracking_config: Dict[str, Any]
    performance_config: Dict[str, Any]
    ui_config: Dict[str, Any]
    export_config: Dict[str, Any]


class JSONHandler:
    """
    JSON設定ファイル処理
    
    性能要件:
    - JSON保存: 30ms以下
    - JSON読み込み: 20ms以下
    - データ検証: スキーマ検証
    - エラー処理: 詳細エラー情報
    """
    
    def __init__(self):
        self.encoding = 'utf-8'
        self.save_timeout = 30  # ms
        self.load_timeout = 20  # ms
        self.indent = 2  # 可読性のためのインデント
        
    def save_project_config(self, project: ProjectEntity, config_path: str) -> bool:
        """
        プロジェクト設定保存（30ms以下必達）
        
        Args:
            project: プロジェクトエンティティ
            config_path: 設定ファイルパス
            
        Returns:
            bool: 保存成功フラグ
            
        Raises:
            FileIOError: ファイル保存失敗
            PerformanceError: 30ms超過
        """
        start_time = time.perf_counter()
        
        try:
            # プロジェクトデータ構築
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
            
            # 出力ディレクトリ確認・作成
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # JSON保存（最適化）
            with open(config_path, 'w', encoding=self.encoding, buffering=8192) as f:
                json.dump(config_data, f, 
                         indent=self.indent, 
                         ensure_ascii=False,
                         separators=(',', ': '))  # 圧縮形式
                f.flush()
                
            # 性能確認
            elapsed_time = (time.perf_counter() - start_time) * 1000
            if elapsed_time > self.save_timeout:
                raise PerformanceError(
                    f"JSON save timeout: {elapsed_time:.2f}ms > {self.save_timeout}ms"
                )
                
            return True
            
        except OSError as e:
            raise FileIOError(f"Failed to save project config to {config_path}: {e}")
        except (TypeError, ValueError) as e:
            raise FileIOError(f"JSON encoding error: {e}")
        except Exception as e:
            raise FileIOError(f"Unexpected error during JSON save: {e}")
            
    def load_project_config(self, config_path: str) -> ProjectEntity:
        """
        プロジェクト設定読み込み（20ms以下必達）
        
        Args:
            config_path: 設定ファイルパス
            
        Returns:
            ProjectEntity: プロジェクトエンティティ
            
        Raises:
            FileIOError: ファイル読み込み失敗
            PerformanceError: 20ms超過
        """
        start_time = time.perf_counter()
        
        if not os.path.exists(config_path):
            raise FileIOError(f"Project config not found: {config_path}")
            
        try:
            # JSON読み込み（最適化）
            with open(config_path, 'r', encoding=self.encoding, buffering=8192) as f:
                config_data = json.load(f)
                
            # スキーマ検証
            self._validate_project_config_schema(config_data)
            
            # ProjectEntity生成
            project = self._create_project_entity_from_config(config_data)
            
            # 性能確認
            elapsed_time = (time.perf_counter() - start_time) * 1000
            if elapsed_time > self.load_timeout:
                raise PerformanceError(
                    f"JSON load timeout: {elapsed_time:.2f}ms > {self.load_timeout}ms"
                )
                
            return project
            
        except json.JSONDecodeError as e:
            raise FileIOError(f"Invalid JSON format in {config_path}: {e}")
        except (ValidationError, PerformanceError):
            raise  # 再発生
        except Exception as e:
            raise FileIOError(f"Unexpected error during JSON load: {e}")
            
    def save_generic_config(self, config_data: Dict[str, Any], config_path: str) -> bool:
        """
        汎用設定保存
        
        Args:
            config_data: 設定データ
            config_path: 設定ファイルパス
            
        Returns:
            bool: 保存成功フラグ
        """
        start_time = time.perf_counter()
        
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding=self.encoding, buffering=8192) as f:
                json.dump(config_data, f, 
                         indent=self.indent, 
                         ensure_ascii=False,
                         default=self._json_serializer)
                f.flush()
                os.fsync(f.fileno())
                
            elapsed_time = (time.perf_counter() - start_time) * 1000
            if elapsed_time > self.save_timeout:
                raise PerformanceError(
                    f"Generic JSON save timeout: {elapsed_time:.2f}ms > {self.save_timeout}ms"
                )
                
            return True
            
        except Exception as e:
            raise FileIOError(f"Failed to save generic config: {e}")
            
    def load_generic_config(self, config_path: str) -> Dict[str, Any]:
        """
        汎用設定読み込み
        
        Args:
            config_path: 設定ファイルパス
            
        Returns:
            Dict[str, Any]: 設定データ
        """
        start_time = time.perf_counter()
        
        if not os.path.exists(config_path):
            return {}  # 設定ファイルなし
            
        try:
            with open(config_path, 'r', encoding=self.encoding, buffering=8192) as f:
                config_data = json.load(f)
                
            elapsed_time = (time.perf_counter() - start_time) * 1000
            if elapsed_time > self.load_timeout:
                raise PerformanceError(
                    f"Generic JSON load timeout: {elapsed_time:.2f}ms > {self.load_timeout}ms"
                )
                
            return config_data
            
        except json.JSONDecodeError as e:
            raise FileIOError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise FileIOError(f"Failed to load generic config: {e}")
            
    def _validate_project_config_schema(self, config_data: Dict[str, Any]):
        """プロジェクト設定スキーマ検証"""
        required_sections = ['project_info', 'annotation_config', 'tracking_config']
        
        for section in required_sections:
            if section not in config_data:
                raise ValidationError(f"Missing required section: {section}")
                
        project_info = config_data['project_info']
        required_fields = ['name', 'version', 'created', 'video_source']
        
        for field in required_fields:
            if field not in project_info:
                raise ValidationError(f"Missing required field in project_info: {field}")
                
        # 解像度検証
        if 'resolution' in project_info:
            resolution = project_info['resolution']
            if 'width' not in resolution or 'height' not in resolution:
                raise ValidationError("Missing width or height in resolution")
                
    def _create_project_entity_from_config(self, config_data: Dict[str, Any]) -> ProjectEntity:
        """設定データからProjectEntity生成"""
        project_info = config_data['project_info']
        resolution = project_info.get('resolution', {'width': 1920, 'height': 1080})
        
        return ProjectEntity(
            name=project_info['name'],
            version=project_info['version'],
            created_at=datetime.fromisoformat(project_info['created']),
            video_source=project_info['video_source'],
            frame_output=project_info.get('frame_output', ''),
            annotation_output=project_info.get('annotation_output', ''),
            backup_path=project_info.get('backup_path', ''),
            total_frames=project_info.get('total_frames', 0),
            annotated_frames=project_info.get('annotated_frames', 0),
            frame_rate_original=project_info.get('frame_rate_original', 30.0),
            frame_rate_target=project_info.get('frame_rate_target', 5.0),
            resolution_width=resolution['width'],
            resolution_height=resolution['height'],
            annotation_config=config_data.get('annotation_config', {}),
            tracking_config=config_data.get('tracking_config', {}),
            performance_config=config_data.get('performance_config', {}),
            ui_config=config_data.get('ui_config', {}),
            export_config=config_data.get('export_config', {})
        )
        
    def _json_serializer(self, obj):
        """JSONシリアライザー（datetime対応）"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
    def validate_json_file(self, file_path: str) -> bool:
        """JSONファイル有効性検証"""
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, OSError):
            return False