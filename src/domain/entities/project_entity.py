"""
プロジェクトエンティティ - Agent3専用
プロジェクト単位での設定・メタデータ管理
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .id_entity import IndividualManager
from ..exceptions import ValidationError, BusinessRuleViolationError


@dataclass
class ProjectEntity:
    """
    プロジェクトエンティティ
    
    プロジェクト単位での設定・メタデータ・個体管理
    """
    
    # 基本情報
    id: str                                      # プロジェクトID
    name: str                                    # プロジェクト名
    description: str = ""                        # プロジェクト説明
    
    # ファイルパス
    video_path: str = ""                         # 元動画ファイルパス
    frames_directory: str = ""                   # フレーム画像ディレクトリ
    annotations_directory: str = ""              # アノテーションディレクトリ
    
    # 動画・フレーム設定
    original_fps: float = 30.0                   # 元動画FPS
    target_fps: float = 5.0                      # 変換後FPS
    frame_width: int = 3840                      # フレーム幅（4K）
    frame_height: int = 2160                     # フレーム高さ（4K）
    total_frames: int = 0                        # 総フレーム数
    
    # アノテーション設定
    iou_threshold: float = 0.5                   # 追跡用IOU閾値
    confidence_threshold: float = 0.3            # 信頼度閾値
    auto_save_enabled: bool = True               # 自動保存有効
    backup_enabled: bool = True                  # バックアップ有効
    
    # 個体管理
    individual_manager: IndividualManager = field(default_factory=IndividualManager)
    
    # メタデータ
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_frame_id: str = "000000"               # 最後に開いたフレームID
    
    def __post_init__(self):
        """プロジェクト検証"""
        self._validate_required_fields()
        self._validate_fps_settings()
        self._validate_threshold_settings()
        self._validate_directories()
    
    def _validate_required_fields(self):
        """必須フィールド検証"""
        if not self.id:
            raise ValidationError("project_id", self.id, "non-empty string")
        
        if not self.name:
            raise ValidationError("project_name", self.name, "non-empty string")
    
    def _validate_fps_settings(self):
        """FPS設定検証"""
        if self.original_fps <= 0:
            raise ValidationError("original_fps", self.original_fps, "> 0")
        
        if self.target_fps <= 0:
            raise ValidationError("target_fps", self.target_fps, "> 0")
        
        if self.target_fps > self.original_fps:
            raise BusinessRuleViolationError(
                "fps_conversion",
                f"Target FPS ({self.target_fps}) cannot exceed original FPS ({self.original_fps})"
            )
    
    def _validate_threshold_settings(self):
        """閾値設定検証"""
        if not 0.0 <= self.iou_threshold <= 1.0:
            raise ValidationError("iou_threshold", self.iou_threshold, "0.0-1.0")
        
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValidationError("confidence_threshold", self.confidence_threshold, "0.0-1.0")
    
    def _validate_directories(self):
        """ディレクトリ検証"""
        # パスが指定されている場合のみ検証
        if self.frames_directory and not Path(self.frames_directory).exists():
            # 存在しない場合は作成可能かチェック（実際の作成はInfrastructure層）
            pass
        
        if self.annotations_directory and not Path(self.annotations_directory).exists():
            # 存在しない場合は作成可能かチェック（実際の作成はInfrastructure層）
            pass
    
    def get_frame_interval(self) -> float:
        """フレーム間隔取得（秒）"""
        return 1.0 / self.target_fps
    
    def get_total_duration(self) -> float:
        """総再生時間取得（秒）"""
        if self.target_fps <= 0:
            return 0.0
        return self.total_frames / self.target_fps
    
    def get_frame_id_at_time(self, time_seconds: float) -> str:
        """指定時刻のフレームID取得"""
        frame_number = int(time_seconds * self.target_fps)
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        return f"{frame_number:06d}"
    
    def get_time_at_frame(self, frame_id: str) -> float:
        """指定フレームの時刻取得"""
        try:
            frame_number = int(frame_id)
            return frame_number / self.target_fps
        except ValueError:
            raise ValidationError("frame_id", frame_id, "numeric string")
    
    def assign_individual_id(self, preferred_id: int = None) -> int:
        """個体ID割り当て"""
        individual_id = self.individual_manager.assign_id(preferred_id)
        self._update_timestamp()
        return individual_id.value
    
    def release_individual_id(self, individual_id: int) -> bool:
        """個体ID解放"""
        from .id_entity import IndividualID
        result = self.individual_manager.release_id(IndividualID(individual_id))
        if result:
            self._update_timestamp()
        return result
    
    def get_used_individual_ids(self) -> List[int]:
        """使用中個体ID一覧取得"""
        return [id_obj.value for id_obj in self.individual_manager.get_used_ids()]
    
    def get_available_individual_ids(self) -> List[int]:
        """利用可能個体ID一覧取得"""
        return [id_obj.value for id_obj in self.individual_manager.get_available_ids()]
    
    def is_individual_id_available(self, individual_id: int) -> bool:
        """個体ID利用可能性確認"""
        return self.individual_manager.is_id_available(individual_id)
    
    def get_individual_count(self) -> int:
        """使用中個体数取得"""
        return self.individual_manager.get_usage_count()
    
    def is_at_individual_capacity(self) -> bool:
        """16個体上限到達確認"""
        return self.individual_manager.is_at_capacity()
    
    def update_last_frame(self, frame_id: str) -> None:
        """最後のフレームID更新"""
        # フレームID形式検証
        if not frame_id or len(frame_id) != 6 or not frame_id.isdigit():
            raise ValidationError("frame_id", frame_id, "6-digit zero-padded string")
        
        self.last_frame_id = frame_id
        self._update_timestamp()
    
    def get_settings_dict(self) -> Dict:
        """設定辞書取得"""
        return {
            "iou_threshold": self.iou_threshold,
            "confidence_threshold": self.confidence_threshold,
            "auto_save_enabled": self.auto_save_enabled,
            "backup_enabled": self.backup_enabled,
            "original_fps": self.original_fps,
            "target_fps": self.target_fps,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height
        }
    
    def update_settings(self, settings: Dict) -> None:
        """設定更新"""
        if "iou_threshold" in settings:
            self.iou_threshold = settings["iou_threshold"]
        
        if "confidence_threshold" in settings:
            self.confidence_threshold = settings["confidence_threshold"]
        
        if "auto_save_enabled" in settings:
            self.auto_save_enabled = settings["auto_save_enabled"]
        
        if "backup_enabled" in settings:
            self.backup_enabled = settings["backup_enabled"]
        
        # 更新後に再検証
        self._validate_threshold_settings()
        self._update_timestamp()
    
    def get_project_info(self) -> Dict:
        """プロジェクト情報辞書取得"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "video_path": self.video_path,
            "total_frames": self.total_frames,
            "individual_count": self.get_individual_count(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_frame_id": self.last_frame_id
        }
    
    def _update_timestamp(self) -> None:
        """更新日時更新"""
        self.updated_at = datetime.now()