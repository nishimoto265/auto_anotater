"""
一括書き込み最適化
複数ファイル・大量データの効率的処理
"""

import os
import time
import threading
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from .txt_handler import YOLOTxtHandler, BBEntity
from .json_handler import JSONHandler
from ..exceptions import FileIOError, PerformanceError


@dataclass
class WriteTask:
    """書き込みタスク"""
    task_id: str
    file_path: str
    data: Any
    write_function: Callable
    priority: int = 0  # 高い値が高優先度
    created_at: float = 0.0


class BatchWriter:
    """
    一括書き込み最適化
    
    機能:
    - 複数ファイル同時書き込み
    - ディレクトリ単位最適化
    - 優先度制御
    - エラー回復
    """
    
    def __init__(self, max_workers: int = 4, chunk_size: int = 10):
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.txt_handler = YOLOTxtHandler()
        self.json_handler = JSONHandler()
        
    def batch_save_annotations(self, frame_bb_pairs: List[tuple], 
                              output_dir: str) -> Dict[str, bool]:
        """
        アノテーション一括保存
        
        Args:
            frame_bb_pairs: (frame_id, bb_entities) のリスト
            output_dir: 出力ディレクトリ
            
        Returns:
            Dict[str, bool]: フレームID→保存成功フラグ
        """
        start_time = time.perf_counter()
        results = {}
        
        # 並列処理でファイル保存
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # タスクサブミット
            future_to_frame = {}
            for frame_id, bb_entities in frame_bb_pairs:
                future = executor.submit(
                    self._save_single_annotation,
                    frame_id, bb_entities, output_dir
                )
                future_to_frame[future] = frame_id
                
            # 結果収集
            for future in as_completed(future_to_frame):
                frame_id = future_to_frame[future]
                try:
                    success = future.result()
                    results[frame_id] = success
                except Exception as e:
                    results[frame_id] = False
                    # エラーログ記録
                    print(f"Failed to save frame {frame_id}: {e}")
                    
        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"Batch save completed in {elapsed_time:.2f}ms for {len(frame_bb_pairs)} frames")
        
        return results
        
    def batch_load_annotations(self, frame_ids: List[str],
                              annotations_dir: str) -> Dict[str, List[BBEntity]]:
        """
        アノテーション一括読み込み
        
        Args:
            frame_ids: フレームIDリスト
            annotations_dir: アノテーションディレクトリ
            
        Returns:
            Dict[str, List[BBEntity]]: フレームID→BBエンティティリスト
        """
        start_time = time.perf_counter()
        results = {}
        
        # 並列処理でファイル読み込み
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # タスクサブミット
            future_to_frame = {}
            for frame_id in frame_ids:
                future = executor.submit(
                    self._load_single_annotation,
                    frame_id, annotations_dir
                )
                future_to_frame[future] = frame_id
                
            # 結果収集
            for future in as_completed(future_to_frame):
                frame_id = future_to_frame[future]
                try:
                    bb_entities = future.result()
                    results[frame_id] = bb_entities
                except Exception as e:
                    results[frame_id] = []
                    # エラーログ記録
                    print(f"Failed to load frame {frame_id}: {e}")
                    
        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"Batch load completed in {elapsed_time:.2f}ms for {len(frame_ids)} frames")
        
        return results
        
    def optimized_directory_write(self, write_tasks: List[WriteTask]) -> Dict[str, bool]:
        """
        ディレクトリ最適化書き込み
        同一ディレクトリのタスクをグループ化して効率化
        
        Args:
            write_tasks: 書き込みタスクリスト
            
        Returns:
            Dict[str, bool]: タスクID→成功フラグ
        """
        # ディレクトリ別グループ化
        dir_groups = defaultdict(list)
        for task in write_tasks:
            directory = os.path.dirname(task.file_path)
            dir_groups[directory].append(task)
            
        results = {}
        
        # ディレクトリ単位で並列処理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tasks = {}
            
            for directory, tasks in dir_groups.items():
                # 優先度順ソート
                tasks.sort(key=lambda t: (-t.priority, t.created_at))
                
                future = executor.submit(
                    self._process_directory_tasks,
                    directory, tasks
                )
                future_to_tasks[future] = tasks
                
            # 結果収集
            for future in as_completed(future_to_tasks):
                tasks = future_to_tasks[future]
                try:
                    task_results = future.result()
                    results.update(task_results)
                except Exception as e:
                    # 失敗時は全タスクを失敗扱い
                    for task in tasks:
                        results[task.task_id] = False
                        
        return results
        
    def _save_single_annotation(self, frame_id: str, bb_entities: List[BBEntity],
                               output_dir: str) -> bool:
        """単一アノテーション保存"""
        try:
            return self.txt_handler.save_annotations(frame_id, bb_entities, output_dir)
        except Exception:
            return False
            
    def _load_single_annotation(self, frame_id: str, annotations_dir: str) -> List[BBEntity]:
        """単一アノテーション読み込み"""
        return self.txt_handler.load_annotations(frame_id, annotations_dir)
        
    def _process_directory_tasks(self, directory: str, tasks: List[WriteTask]) -> Dict[str, bool]:
        """ディレクトリタスク処理（同一ディレクトリ最適化）"""
        results = {}
        
        # ディレクトリ作成
        os.makedirs(directory, exist_ok=True)
        
        # ディレクトリキャッシュ活用
        with os.scandir(directory):
            for task in tasks:
                try:
                    start_time = time.perf_counter()
                    success = task.write_function(task.data, task.file_path)
                    elapsed_time = (time.perf_counter() - start_time) * 1000
                    
                    results[task.task_id] = success
                    
                    # 性能監視
                    if elapsed_time > 100:  # 100ms超過警告
                        print(f"Slow write detected: {task.file_path} took {elapsed_time:.2f}ms")
                        
                except Exception as e:
                    results[task.task_id] = False
                    print(f"Write task failed: {task.task_id}, {e}")
                    
        return results
        
    def create_write_task(self, task_id: str, file_path: str, data: Any,
                         write_function: Callable, priority: int = 0) -> WriteTask:
        """書き込みタスク作成"""
        return WriteTask(
            task_id=task_id,
            file_path=file_path,
            data=data,
            write_function=write_function,
            priority=priority,
            created_at=time.time()
        )
        
    def get_write_statistics(self) -> Dict[str, Any]:
        """書き込み統計情報"""
        return {
            "max_workers": self.max_workers,
            "chunk_size": self.chunk_size,
            "txt_handler": self.txt_handler.__class__.__name__,
            "json_handler": self.json_handler.__class__.__name__
        }