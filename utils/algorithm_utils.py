import numpy as np
from typing import Tuple, List, Optional
from numba import jit
import cv2
from scipy import stats
import concurrent.futures

class AlgorithmUtils:
    def __init__(self):
        self.cache = {}

    @staticmethod
    @jit(nopython=True)
    def calculate_iou(box1: np.ndarray, box2: np.ndarray) -> float:
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        return intersection / (box1_area + box2_area - intersection)

    @staticmethod
    def template_matching(image: np.ndarray, template: np.ndarray) -> Tuple[int, int]:
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(result)
        return max_loc

    @staticmethod
    def extract_features(image: np.ndarray) -> np.ndarray:
        orb = cv2.ORB_create()
        keypoints, descriptors = orb.detectAndCompute(image, None)
        return descriptors

    def calculate_histogram_similarity(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        cache_key = (hist1.tobytes(), hist2.tobytes())
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        self.cache[cache_key] = correlation
        return correlation

    @staticmethod
    def detect_edges(image: np.ndarray) -> np.ndarray:
        return cv2.Canny(image, 100, 200)

    @staticmethod
    @jit(nopython=True)
    def calculate_distance(point1: np.ndarray, point2: np.ndarray) -> float:
        return np.sqrt(np.sum((point1 - point2) ** 2))

    @staticmethod
    def calculate_angle(point1: np.ndarray, point2: np.ndarray) -> float:
        return np.arctan2(point2[1] - point1[1], point2[0] - point1[0])

    @staticmethod
    def detect_outliers(data: np.ndarray, threshold: float = 3) -> np.ndarray:
        z_scores = stats.zscore(data)
        return np.abs(z_scores) > threshold

    def parallel_process(self, data: List, func, max_workers: int = 4) -> List:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(func, data))
        return results

    @staticmethod
    def calculate_confidence_interval(data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
        mean = np.mean(data)
        std_err = stats.sem(data)
        interval = stats.t.interval(confidence, len(data)-1, mean, std_err)
        return interval

    @staticmethod
    @jit(nopython=True)
    def predict_next_position(positions: np.ndarray) -> np.ndarray:
        if len(positions) < 2:
            return positions[-1]
        velocity = positions[-1] - positions[-2]
        return positions[-1] + velocity

    def check_collision(self, box1: np.ndarray, box2: np.ndarray) -> bool:
        return self.calculate_iou(box1, box2) > 0

    @staticmethod
    def optimize_array_operations(func):
        def wrapper(*args, **kwargs):
            args = [np.asarray(arg) if isinstance(arg, list) else arg for arg in args]
            return func(*args, **kwargs)
        return wrapper

    def clear_cache(self):
        self.cache.clear()