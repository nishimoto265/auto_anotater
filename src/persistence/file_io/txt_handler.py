"""
YOLO形式txtファイル処理
100ms以下保存・50ms以下読み込み目標達成
"""

import os
import time
import uuid
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from ..exceptions import FileIOError, ValidationError, PerformanceError


@dataclass
class Coordinates:
    """YOLO座標（正規化済み）"""
    x: float  # 中心X座標 (0.0-1.0)
    y: float  # 中心Y座標 (0.0-1.0)
    w: float  # 幅 (0.0-1.0)
    h: float  # 高さ (0.0-1.0)


@dataclass
class BBEntity:
    """バウンディングボックスエンティティ"""
    id: str
    frame_id: str
    individual_id: int  # 個体ID (0-15)
    action_id: int     # 行動ID (0-4: sit/stand/milk/water/food)
    coordinates: Coordinates
    confidence: float  # 信頼度 (0.0-1.0)
    created_at: datetime
    updated_at: datetime


class YOLOTxtHandler:
    """
    YOLO形式txtファイル処理
    
    性能要件:
    - ファイル保存: 100ms以下
    - ファイル読み込み: 50ms以下
    - データ検証: 完全性保証
    - エンコーディング: UTF-8統一
    
    YOLO形式:
    個体ID YOLO_X YOLO_Y YOLO_W YOLO_H 行動ID 信頼度
    例: 0 0.5123 0.3456 0.1234 0.0987 2 0.9512
    """
    
    def __init__(self):
        self.encoding = 'utf-8'
        self.line_ending = '\n'  # Unix形式
        self.save_timeout = 100  # ms
        self.load_timeout = 50   # ms
        
    def save_annotations(self, frame_id: str, bb_entities: List[BBEntity],
                        output_dir: str) -> bool:
        """
        アノテーション保存（100ms以下必達）
        
        Args:
            frame_id: フレームID（000000形式）
            bb_entities: BBエンティティリスト
            output_dir: 出力ディレクトリ
            
        Returns:
            bool: 保存成功フラグ
            
        Raises:
            FileIOError: ファイル保存失敗
            PerformanceError: 100ms超過
        """
        start_time = time.perf_counter()
        
        # フレームIDフォーマット検証
        if not self._validate_frame_id(frame_id):
            raise ValidationError(f"Invalid frame_id format: {frame_id}")
            
        # 出力ディレクトリ確認・作成
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = os.path.join(output_dir, f"{frame_id}.txt")
        
        try:
            # YOLO形式文字列生成
            yolo_lines = []
            for bb in bb_entities:
                line = self._format_yolo_line(bb)
                yolo_lines.append(line)
            
            # 一括書き込み（I/O最適化）
            content = self.line_ending.join(yolo_lines)
            if content:  # 空でない場合のみファイル作成
                content += self.line_ending
                
                with open(file_path, 'w', encoding=self.encoding, buffering=8192) as f:
                    f.write(content)
                    f.flush()  # バッファ強制書き込み
                    os.fsync(f.fileno())  # OS同期
            else:
                # 空ファイル作成（アノテーションなし）
                with open(file_path, 'w', encoding=self.encoding) as f:
                    pass
                    
            # 性能確認
            elapsed_time = (time.perf_counter() - start_time) * 1000
            if elapsed_time > self.save_timeout:
                raise PerformanceError(
                    f"Save timeout: {elapsed_time:.2f}ms > {self.save_timeout}ms"
                )
                
            return True
            
        except OSError as e:
            raise FileIOError(f"Failed to save annotations to {file_path}: {e}")
        except Exception as e:
            raise FileIOError(f"Unexpected error during save: {e}")
            
    def load_annotations(self, frame_id: str, annotations_dir: str) -> List[BBEntity]:
        """
        アノテーション読み込み（50ms以下必達）
        
        Args:
            frame_id: フレームID
            annotations_dir: アノテーションディレクトリ
            
        Returns:
            List[BBEntity]: BBエンティティリスト
            
        Raises:
            FileIOError: ファイル読み込み失敗
            PerformanceError: 50ms超過
        """
        start_time = time.perf_counter()
        
        file_path = os.path.join(annotations_dir, f"{frame_id}.txt")
        
        if not os.path.exists(file_path):
            return []  # アノテーションファイルなし
            
        bb_entities = []
        
        try:
            # 一括読み込み（I/O最適化）
            with open(file_path, 'r', encoding=self.encoding, buffering=8192) as f:
                content = f.read()
                
            # 行分割・解析
            lines = content.strip().split(self.line_ending)
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:  # 空行スキップ
                    continue
                    
                bb_entity = self._parse_yolo_line(line, frame_id, line_num)
                bb_entities.append(bb_entity)
                
            # 性能確認
            elapsed_time = (time.perf_counter() - start_time) * 1000
            if elapsed_time > self.load_timeout:
                raise PerformanceError(
                    f"Load timeout: {elapsed_time:.2f}ms > {self.load_timeout}ms"
                )
                
        except OSError as e:
            raise FileIOError(f"Failed to load annotations from {file_path}: {e}")
        except (ValidationError, PerformanceError):
            raise  # 再発生
        except Exception as e:
            raise FileIOError(f"Unexpected error during load: {e}")
            
        return bb_entities
        
    def _format_yolo_line(self, bb: BBEntity) -> str:
        """BBエンティティ→YOLO行変換"""
        return (f"{bb.individual_id} {bb.coordinates.x:.4f} {bb.coordinates.y:.4f} "
                f"{bb.coordinates.w:.4f} {bb.coordinates.h:.4f} "
                f"{bb.action_id} {bb.confidence:.4f}")
               
    def _parse_yolo_line(self, line: str, frame_id: str, line_num: int) -> BBEntity:
        """YOLO行→BBエンティティ変換"""
        parts = line.split()
        if len(parts) != 7:
            raise ValidationError(f"Invalid YOLO format at line {line_num}: expected 7 fields, got {len(parts)}")
            
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
            raise ValidationError(f"Invalid data format at line {line_num}: {e}")
            
    def _validate_yolo_data(self, individual_id: int, x: float, y: float, w: float, h: float,
                          action_id: int, confidence: float, line_num: int):
        """YOLOデータ検証"""
        if not 0 <= individual_id <= 15:
            raise ValidationError(f"Invalid individual_id at line {line_num}: {individual_id} (must be 0-15)")
            
        if not all(0.0 <= coord <= 1.0 for coord in [x, y, w, h]):
            raise ValidationError(f"Invalid coordinates at line {line_num}: x={x}, y={y}, w={w}, h={h} (must be 0.0-1.0)")
            
        if not 0 <= action_id <= 4:
            raise ValidationError(f"Invalid action_id at line {line_num}: {action_id} (must be 0-4)")
            
        if not 0.0 <= confidence <= 1.0:
            raise ValidationError(f"Invalid confidence at line {line_num}: {confidence} (must be 0.0-1.0)")
            
    def _validate_frame_id(self, frame_id: str) -> bool:
        """フレームID検証（000000形式）"""
        if not isinstance(frame_id, str):
            return False
        if len(frame_id) != 6:
            return False
        if not frame_id.isdigit():
            return False
        return True
        
    def get_file_stats(self, file_path: str) -> dict:
        """ファイル統計情報取得"""
        if not os.path.exists(file_path):
            return {"exists": False}
            
        stat = os.stat(file_path)
        return {
            "exists": True,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "created": datetime.fromtimestamp(stat.st_ctime)
        }