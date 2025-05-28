import os
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class ProgressTracker:
    def __init__(self, total_frames: int):
        self.total_frames = total_frames
        self.completed_frames = 0
        self.start_time = time.time()
        self.last_save_time = time.time()
        
        self.bb_stats = {
            'total': 0,
            'by_id': {},
            'by_action': {}
        }
        
        self.operation_stats = {
            'create': 0,
            'edit': 0,
            'delete': 0,
            'errors': 0
        }
        
        self.performance_metrics = {
            'frame_switch_times': [],
            'bb_update_times': [],
            'memory_usage': []
        }

    def update_progress(self, frame_num: int, annotations: List[Dict]) -> None:
        self.completed_frames = frame_num
        self._update_bb_stats(annotations)
        self._update_performance_metrics()

    def _update_bb_stats(self, annotations: List[Dict]) -> None:
        self.bb_stats['total'] = len(annotations)
        
        id_counts = {}
        action_counts = {}
        for ann in annotations:
            id_counts[ann['id']] = id_counts.get(ann['id'], 0) + 1
            action_counts[ann['action']] = action_counts.get(ann['action'], 0) + 1
            
        self.bb_stats['by_id'] = id_counts
        self.bb_stats['by_action'] = action_counts

    def _update_performance_metrics(self) -> None:
        import psutil
        self.performance_metrics['memory_usage'].append(
            psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        )

    def get_completion_rate(self) -> float:
        return (self.completed_frames / self.total_frames) * 100 if self.total_frames > 0 else 0

    def get_estimated_completion_time(self) -> Optional[datetime]:
        if self.completed_frames == 0:
            return None
            
        elapsed_time = time.time() - self.start_time
        frames_per_second = self.completed_frames / elapsed_time
        remaining_frames = self.total_frames - self.completed_frames
        
        if frames_per_second > 0:
            remaining_seconds = remaining_frames / frames_per_second
            return datetime.now() + timedelta(seconds=remaining_seconds)
        return None

    def get_efficiency_metrics(self) -> Dict:
        elapsed_hours = (time.time() - self.start_time) / 3600
        return {
            'frames_per_hour': self.completed_frames / elapsed_hours if elapsed_hours > 0 else 0,
            'bbs_per_hour': self.bb_stats['total'] / elapsed_hours if elapsed_hours > 0 else 0,
            'error_rate': (self.operation_stats['errors'] / 
                          sum(self.operation_stats.values())) * 100 if sum(self.operation_stats.values()) > 0 else 0
        }

    def record_operation(self, operation_type: str) -> None:
        if operation_type in self.operation_stats:
            self.operation_stats[operation_type] += 1

    def record_frame_switch_time(self, duration_ms: float) -> None:
        self.performance_metrics['frame_switch_times'].append(duration_ms)

    def record_bb_update_time(self, duration_ms: float) -> None:
        self.performance_metrics['bb_update_times'].append(duration_ms)

    def generate_report(self) -> Dict:
        return {
            'completion': {
                'rate': self.get_completion_rate(),
                'frames_done': self.completed_frames,
                'total_frames': self.total_frames,
                'estimated_completion': self.get_estimated_completion_time()
            },
            'statistics': {
                'bounding_boxes': self.bb_stats,
                'operations': self.operation_stats,
                'efficiency': self.get_efficiency_metrics()
            },
            'performance': {
                'avg_frame_switch_ms': np.mean(self.performance_metrics['frame_switch_times']) if self.performance_metrics['frame_switch_times'] else 0,
                'avg_bb_update_ms': np.mean(self.performance_metrics['bb_update_times']) if self.performance_metrics['bb_update_times'] else 0,
                'avg_memory_mb': np.mean(self.performance_metrics['memory_usage']) if self.performance_metrics['memory_usage'] else 0
            }
        }

    def export_report(self, format: str = 'json', filepath: str = None) -> None:
        report = self.generate_report()
        
        if format.lower() == 'json':
            output = json.dumps(report, indent=2, default=str)
            if filepath:
                with open(filepath, 'w') as f:
                    f.write(output)
            return output
            
        elif format.lower() == 'csv':
            import csv
            if filepath:
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    for section, data in report.items():
                        writer.writerow([section])
                        if isinstance(data, dict):
                            for key, value in data.items():
                                writer.writerow([key, value])
                        else:
                            writer.writerow([data])
                        writer.writerow([])

    def save_checkpoint(self) -> None:
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'progress': self.generate_report()
        }
        
        with open(f'progress_checkpoint_{int(time.time())}.json', 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
        self.last_save_time = time.time()