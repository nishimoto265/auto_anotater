import numpy as np
import cv2
from typing import Tuple, Optional, Dict
from dataclasses import dataclass
from threading import Lock

@dataclass
class TrackingState:
    bbox: np.ndarray  # [x, y, w, h] in YOLO format
    template: np.ndarray
    kalman_filter: cv2.KalmanFilter
    feature_points: np.ndarray
    confidence: float
    lost_count: int

class TrackingSystem:
    def __init__(self, bbox_manager, image_cache, algorithm_utils):
        self.bbox_manager = bbox_manager
        self.image_cache = image_cache
        self.algorithm_utils = algorithm_utils
        self.tracking_states: Dict[int, TrackingState] = {}
        self.lock = Lock()
        
        self.template_size = (64, 64)
        self.max_lost_frames = 10
        self.min_confidence = 0.5
        self.feature_params = dict(
            maxCorners=30,
            qualityLevel=0.3,
            minDistance=7,
            blockSize=7
        )
        
    def start_tracking(self, frame_id: int, individual_id: int) -> bool:
        with self.lock:
            current_frame = self.image_cache.get_frame(frame_id)
            bbox = self.bbox_manager.get_bbox(frame_id, individual_id)
            if current_frame is None or bbox is None:
                return False
                
            x, y, w, h = self._yolo_to_pixel(bbox, current_frame.shape)
            template = current_frame[y:y+h, x:x+w]
            template = cv2.resize(template, self.template_size)
            
            kf = cv2.KalmanFilter(4, 2)
            kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
            kf.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
            
            roi = current_frame[y:y+h, x:x+w]
            features = cv2.goodFeaturesToTrack(
                cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY),
                mask=None,
                **self.feature_params
            )
            
            self.tracking_states[individual_id] = TrackingState(
                bbox=bbox,
                template=template,
                kalman_filter=kf,
                feature_points=features,
                confidence=1.0,
                lost_count=0
            )
            return True
            
    def update(self, prev_frame_id: int, current_frame_id: int) -> None:
        with self.lock:
            prev_frame = self.image_cache.get_frame(prev_frame_id)
            current_frame = self.image_cache.get_frame(current_frame_id)
            if prev_frame is None or current_frame is None:
                return
                
            for individual_id, state in self.tracking_states.items():
                if state.lost_count >= self.max_lost_frames:
                    continue
                    
                predicted_bbox = self._predict_bbox(state, prev_frame, current_frame)
                matched_bbox = self._template_matching(state, current_frame, predicted_bbox)
                refined_bbox = self._optical_flow_refinement(
                    state, prev_frame, current_frame, matched_bbox
                )
                
                confidence = self._calculate_confidence(
                    state, current_frame, refined_bbox
                )
                
                if confidence > self.min_confidence:
                    state.bbox = refined_bbox
                    state.confidence = confidence
                    state.lost_count = 0
                    self.bbox_manager.update_bbox(
                        current_frame_id, individual_id, refined_bbox
                    )
                else:
                    state.lost_count += 1
                    
    def stop_tracking(self, individual_id: int) -> None:
        with self.lock:
            if individual_id in self.tracking_states:
                del self.tracking_states[individual_id]
                
    def _predict_bbox(
        self, state: TrackingState, prev_frame: np.ndarray, current_frame: np.ndarray
    ) -> np.ndarray:
        prediction = state.kalman_filter.predict()
        dx = prediction[2, 0]
        dy = prediction[3, 0]
        
        bbox = state.bbox.copy()
        bbox[0] += dx / prev_frame.shape[1]
        bbox[1] += dy / prev_frame.shape[0]
        return bbox
        
    def _template_matching(
        self, state: TrackingState, frame: np.ndarray, predicted_bbox: np.ndarray
    ) -> np.ndarray:
        x, y, w, h = self._yolo_to_pixel(predicted_bbox, frame.shape)
        search_area = frame[max(0, y-20):min(frame.shape[0], y+h+20),
                          max(0, x-20):min(frame.shape[1], x+w+20)]
        
        if search_area.size == 0:
            return predicted_bbox
            
        result = cv2.matchTemplate(search_area, state.template, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(result)
        
        new_x = x - 20 + max_loc[0]
        new_y = y - 20 + max_loc[1]
        return self._pixel_to_yolo([new_x, new_y, w, h], frame.shape)
        
    def _optical_flow_refinement(
        self, state: TrackingState, prev_frame: np.ndarray, current_frame: np.ndarray,
        bbox: np.ndarray
    ) -> np.ndarray:
        if state.feature_points is None:
            return bbox
            
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        
        new_points, status, _ = cv2.calcOpticalFlowPyrLK(
            prev_gray, current_gray, state.feature_points, None
        )
        
        if new_points is None:
            return bbox
            
        good_new = new_points[status == 1]
        good_old = state.feature_points[status == 1]
        
        if len(good_new) > 0 and len(good_old) > 0:
            median_flow = np.median(good_new - good_old, axis=0)
            bbox = bbox.copy()
            bbox[0] += median_flow[0] / current_frame.shape[1]
            bbox[1] += median_flow[1] / current_frame.shape[0]
            
        state.feature_points = good_new
        return bbox
        
    def _calculate_confidence(
        self, state: TrackingState, frame: np.ndarray, bbox: np.ndarray
    ) -> float:
        x, y, w, h = self._yolo_to_pixel(bbox, frame.shape)
        current_template = frame[y:y+h, x:x+w]
        if current_template.size == 0:
            return 0.0
            
        current_template = cv2.resize(current_template, self.template_size)
        correlation = cv2.matchTemplate(
            current_template, state.template, cv2.TM_CCOEFF_NORMED
        )
        return float(correlation[0, 0])
        
    def _yolo_to_pixel(
        self, bbox: np.ndarray, shape: Tuple[int, int]
    ) -> Tuple[int, int, int, int]:
        x = int((bbox[0] - bbox[2]/2) * shape[1])
        y = int((bbox[1] - bbox[3]/2) * shape[0])
        w = int(bbox[2] * shape[1])
        h = int(bbox[3] * shape[0])
        return x, y, w, h
        
    def _pixel_to_yolo(
        self, bbox: Tuple[int, int, int, int], shape: Tuple[int, int]
    ) -> np.ndarray:
        x, y, w, h = bbox
        return np.array([
            (x + w/2) / shape[1],
            (y + h/2) / shape[0],
            w / shape[1],
            h / shape[0]
        ])