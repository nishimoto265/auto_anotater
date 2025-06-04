"""
自動保存システム
フレーム切り替え時非同期保存・差分検知・リトライ機能
"""

import os
import time
import queue
import threading
import hashlib
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from ..file_io.txt_handler import YOLOTxtHandler, BBEntity
from ..file_io.json_handler import JSONHandler
from ..exceptions import FileIOError, PerformanceError


@dataclass
class SaveTask:
    """保存タスク"""
    task_id: str
    frame_id: str
    bb_entities: List[BBEntity]
    priority: str = "normal"  # high/normal/low
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"save_{self.frame_id}_{int(self.timestamp * 1000)}"


@dataclass 
class SaveResult:
    """保存結果"""
    task_id: str
    success: bool
    elapsed_time: float  # ms
    error_message: Optional[str] = None
    retry_count: int = 0


class AutoSaver:
    """
    自動保存システム
    
    機能:
    - フレーム切り替え時自動保存
    - 差分保存（変更検知）
    - 非同期保存（UIブロックなし）
    - 保存失敗時リトライ
    - 保存統計・監視
    """
    
    def __init__(self, save_interval: int = 30, max_workers: int = 2):
        self.save_interval = save_interval  # 秒
        self.max_workers = max_workers
        
        # キューとワーカー
        self.high_priority_queue = queue.Queue()
        self.normal_priority_queue = queue.Queue()
        self.low_priority_queue = queue.Queue()
        
        # スレッド管理
        self.worker_threads = []
        self.is_running = False
        self.executor = None
        
        # ハンドラー
        self.txt_handler = YOLOTxtHandler()
        self.json_handler = JSONHandler()
        
        # 差分検知用
        self.frame_checksums = {}  # frame_id -> checksum
        
        # 統計情報
        self.save_stats = {
            "total_saves": 0,
            "successful_saves": 0,
            "failed_saves": 0,
            "average_save_time": 0.0,
            "max_save_time": 0.0
        }
        
        # コールバック
        self.on_save_complete: Optional[Callable] = None
        self.on_save_error: Optional[Callable] = None
        
    def start_auto_save(self):
        """自動保存開始"""
        if self.is_running:
            return
            
        self.is_running = True
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # ワーカースレッド起動
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._auto_save_worker, args=(i,))
            worker.daemon = True
            worker.start()
            self.worker_threads.append(worker)
            
        print(f"AutoSaver started with {self.max_workers} workers")
        
    def stop_auto_save(self):
        """自動保存停止"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # 残りタスクの処理完了を待つ
        self._drain_queues()
        
        # ワーカースレッド終了
        for worker in self.worker_threads:
            worker.join(timeout=5.0)
            
        if self.executor:
            self.executor.shutdown(wait=True)
            
        self.worker_threads.clear()
        print("AutoSaver stopped")
        
    def schedule_save(self, frame_id: str, bb_entities: List[BBEntity],
                     priority: str = "normal", force_save: bool = False) -> str:
        """
        保存スケジュール（非同期）
        
        Args:
            frame_id: フレームID
            bb_entities: BBエンティティリスト
            priority: high/normal/low
            force_save: 差分チェック無視
            
        Returns:
            str: タスクID
        """
        # 差分チェック（force_save=Falseの場合）
        if not force_save and not self._has_changes(frame_id, bb_entities):
            return ""  # 変更なし、保存スキップ
            
        save_task = SaveTask(
            task_id="",  # 自動生成
            frame_id=frame_id,
            bb_entities=bb_entities,
            priority=priority
        )
        
        # 優先度別キューに追加
        target_queue = self._get_queue_by_priority(priority)
        target_queue.put(save_task)
        
        return save_task.task_id
        
    def schedule_json_save(self, config_data: Dict[str, Any], config_path: str,
                          priority: str = "low") -> str:
        """JSON設定保存スケジュール"""
        task_id = f"json_{int(time.time() * 1000)}"
        
        # JSONタスクは特別処理
        if self.executor and self.is_running:
            future = self.executor.submit(
                self._save_json_config, task_id, config_data, config_path
            )
            # 完了コールバック設定
            future.add_done_callback(self._handle_json_save_result)
            
        return task_id
        
    def get_pending_saves_count(self) -> Dict[str, int]:
        """待機中保存タスク数"""
        return {
            "high": self.high_priority_queue.qsize(),
            "normal": self.normal_priority_queue.qsize(), 
            "low": self.low_priority_queue.qsize()
        }
        
    def get_save_statistics(self) -> Dict[str, Any]:
        """保存統計情報"""
        stats = self.save_stats.copy()
        stats["pending_saves"] = self.get_pending_saves_count()
        stats["success_rate"] = (
            stats["successful_saves"] / max(1, stats["total_saves"]) * 100
        )
        return stats
        
    def force_save_all_pending(self) -> List[SaveResult]:
        """待機中タスク強制実行"""
        results = []
        
        # 全キューからタスク取得・実行
        all_tasks = []
        for q in [self.high_priority_queue, self.normal_priority_queue, self.low_priority_queue]:
            while not q.empty():
                try:
                    task = q.get_nowait()
                    all_tasks.append(task)
                except queue.Empty:
                    break
                    
        # 並列実行
        if self.executor and all_tasks:
            future_to_task = {}
            for task in all_tasks:
                future = self.executor.submit(self._execute_save_task, task)
                future_to_task[future] = task
                
            # 結果収集
            for future in future_to_task:
                try:
                    result = future.result(timeout=10.0)
                    results.append(result)
                except Exception as e:
                    task = future_to_task[future]
                    results.append(SaveResult(
                        task_id=task.task_id,
                        success=False,
                        elapsed_time=0.0,
                        error_message=str(e)
                    ))
                    
        return results
        
    def _auto_save_worker(self, worker_id: int):
        """自動保存ワーカー（バックグラウンド実行）"""
        print(f"AutoSave worker {worker_id} started")
        
        while self.is_running:
            try:
                # 優先度順でタスク取得
                save_task = self._get_next_task(timeout=self.save_interval)
                
                if save_task:
                    # 保存タスク実行
                    result = self._execute_save_task(save_task)
                    self._handle_save_result(result)
                else:
                    # タイムアウト時の定期処理
                    self._perform_periodic_maintenance()
                    
            except Exception as e:
                print(f"AutoSave worker {worker_id} error: {e}")
                time.sleep(1.0)  # エラー時の待機
                
        print(f"AutoSave worker {worker_id} stopped")
        
    def _get_next_task(self, timeout: float) -> Optional[SaveTask]:
        """次のタスク取得（優先度順）"""
        queues = [
            self.high_priority_queue,
            self.normal_priority_queue,
            self.low_priority_queue
        ]
        
        for q in queues:
            try:
                return q.get(timeout=timeout)
            except queue.Empty:
                continue
                
        return None
        
    def _execute_save_task(self, save_task: SaveTask) -> SaveResult:
        """保存タスク実行"""
        start_time = time.perf_counter()
        
        try:
            # アノテーション保存実行
            success = self.txt_handler.save_annotations(
                save_task.frame_id,
                save_task.bb_entities,
                self._get_annotation_output_dir()
            )
            
            elapsed_time = (time.perf_counter() - start_time) * 1000
            
            return SaveResult(
                task_id=save_task.task_id,
                success=success,
                elapsed_time=elapsed_time
            )
            
        except Exception as e:
            elapsed_time = (time.perf_counter() - start_time) * 1000
            
            # リトライ対象判定
            if save_task.retry_count < save_task.max_retries:
                save_task.retry_count += 1
                # リトライキューに戻す
                time.sleep(0.1 * save_task.retry_count)  # 指数バックオフ
                self.normal_priority_queue.put(save_task)
                
            return SaveResult(
                task_id=save_task.task_id,
                success=False,
                elapsed_time=elapsed_time,
                error_message=str(e),
                retry_count=save_task.retry_count
            )
            
    def _save_json_config(self, task_id: str, config_data: Dict[str, Any], 
                         config_path: str) -> SaveResult:
        """JSON設定保存実行"""
        start_time = time.perf_counter()
        
        try:
            success = self.json_handler.save_generic_config(config_data, config_path)
            elapsed_time = (time.perf_counter() - start_time) * 1000
            
            return SaveResult(
                task_id=task_id,
                success=success,
                elapsed_time=elapsed_time
            )
            
        except Exception as e:
            elapsed_time = (time.perf_counter() - start_time) * 1000
            return SaveResult(
                task_id=task_id,
                success=False,
                elapsed_time=elapsed_time,
                error_message=str(e)
            )
            
    def _handle_save_result(self, result: SaveResult):
        """保存結果処理"""
        # 統計更新
        self.save_stats["total_saves"] += 1
        if result.success:
            self.save_stats["successful_saves"] += 1
        else:
            self.save_stats["failed_saves"] += 1
            
        # 時間統計更新
        self.save_stats["max_save_time"] = max(
            self.save_stats["max_save_time"], result.elapsed_time
        )
        
        # 平均時間更新
        total = self.save_stats["total_saves"]
        current_avg = self.save_stats["average_save_time"]
        self.save_stats["average_save_time"] = (
            (current_avg * (total - 1) + result.elapsed_time) / total
        )
        
        # コールバック実行
        if result.success and self.on_save_complete:
            self.on_save_complete(result)
        elif not result.success and self.on_save_error:
            self.on_save_error(result)
            
    def _handle_json_save_result(self, future):
        """JSON保存結果処理"""
        try:
            result = future.result()
            self._handle_save_result(result)
        except Exception as e:
            print(f"JSON save callback error: {e}")
            
    def _has_changes(self, frame_id: str, bb_entities: List[BBEntity]) -> bool:
        """変更検知（差分チェック）"""
        # BBエンティティのチェックサム計算
        content = ""
        for bb in sorted(bb_entities, key=lambda x: x.individual_id):
            content += f"{bb.individual_id}_{bb.coordinates.x:.4f}_{bb.coordinates.y:.4f}_"
            content += f"{bb.coordinates.w:.4f}_{bb.coordinates.h:.4f}_{bb.action_id}_{bb.confidence:.4f}"
            
        current_checksum = hashlib.md5(content.encode()).hexdigest()
        
        # 前回のチェックサムと比較
        previous_checksum = self.frame_checksums.get(frame_id)
        
        if previous_checksum != current_checksum:
            self.frame_checksums[frame_id] = current_checksum
            return True
            
        return False
        
    def _get_queue_by_priority(self, priority: str) -> queue.Queue:
        """優先度別キュー取得"""
        if priority == "high":
            return self.high_priority_queue
        elif priority == "low":
            return self.low_priority_queue
        else:
            return self.normal_priority_queue
            
    def _get_annotation_output_dir(self) -> str:
        """アノテーション出力ディレクトリ取得"""
        # TODO: 設定から取得
        return "data/annotations"
        
    def _perform_periodic_maintenance(self):
        """定期メンテナンス"""
        # 古いチェックサムクリア（メモリ節約）
        if len(self.frame_checksums) > 10000:
            # 古い半分を削除
            items = list(self.frame_checksums.items())
            items.sort(key=lambda x: x[0])  # frame_id順
            keep_items = items[len(items)//2:]
            self.frame_checksums = dict(keep_items)
            
    def _drain_queues(self):
        """キュー内容をドレイン"""
        total_drained = 0
        for q in [self.high_priority_queue, self.normal_priority_queue, self.low_priority_queue]:
            while not q.empty():
                try:
                    q.get_nowait()
                    total_drained += 1
                except queue.Empty:
                    break
                    
        if total_drained > 0:
            print(f"Drained {total_drained} pending save tasks")