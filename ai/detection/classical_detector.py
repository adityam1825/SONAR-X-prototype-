"""
SONAR-X Classical CV Detection Fallback

Used when no trained YOLO model is available.
This is EXPLICITLY labelled as CLASSICAL CV — NOT a trained AI model.

Approach:
- Adaptive thresholding
- Connected components
- Contour detection
- Local contrast analysis
- Shadow-aware heuristics
- Nadir exclusion
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger('sonarx.detection.classical')


class ClassicalDetector:
    """
    Classical CV candidate detection for side-scan sonar images.

    IMPORTANT: This is NOT a trained AI model. It uses classical image
    processing heuristics. Results should be treated as high-recall
    candidates for downstream fingerprint analysis and evidence fusion.

    Clearly labelled as: CLASSICAL CV FALLBACK
    """

    INFERENCE_MODE = 'CLASSICAL_CV'

    def __init__(
        self,
        min_area: int = 50,
        max_area: int = 80000,
        min_aspect_ratio: float = 0.1,
        max_aspect_ratio: float = 20.0,
        intensity_threshold_percentile: float = 85.0,
        nadir_start: Optional[int] = None,
        nadir_end: Optional[int] = None,
    ):
        self.min_area = min_area
        self.max_area = max_area
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.intensity_threshold_percentile = intensity_threshold_percentile
        self.nadir_start = nadir_start
        self.nadir_end = nadir_end

    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect candidate anomalies in a preprocessed sonar image.

        Parameters
        ----------
        image : np.ndarray
            Preprocessed grayscale sonar image.

        Returns
        -------
        list of dicts with keys: bbox, score, method
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy().astype(np.uint8)

        candidates = []

        # Method 1: Adaptive thresholding
        candidates.extend(self._adaptive_threshold_detect(gray))

        # Method 2: Local contrast detection
        candidates.extend(self._local_contrast_detect(gray))

        # Merge overlapping detections
        candidates = self._nms(candidates)

        # Filter by nadir
        candidates = self._filter_nadir(candidates, gray.shape[1])

        # Filter by geometry
        candidates = self._filter_geometry(candidates)

        return candidates

    def _adaptive_threshold_detect(self, gray: np.ndarray) -> List[Dict]:
        """Use adaptive thresholding to find high-backscatter regions."""
        # Global intensity threshold at high percentile
        threshold = np.percentile(gray[gray > 5], self.intensity_threshold_percentile)

        binary = np.zeros_like(gray, dtype=np.uint8)
        binary[gray > threshold] = 255

        # Morphological cleaning
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        results = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_area <= area <= self.max_area:
                x, y, w, h = cv2.boundingRect(cnt)
                score = min(100.0, float(area) / self.max_area * 80 + 20)
                results.append({
                    'bbox': (x, y, w, h),
                    'score': round(score, 1),
                    'method': 'adaptive_threshold',
                    'contour_area': area,
                })
        return results

    def _local_contrast_detect(self, gray: np.ndarray) -> List[Dict]:
        """Detect high-contrast regions using local variance."""
        # Compute local variance in a window
        kernel_size = 15
        gray_f = gray.astype(float)

        # Local mean and variance using box filter
        local_mean = cv2.boxFilter(gray_f, -1, (kernel_size, kernel_size))
        local_sq_mean = cv2.boxFilter(gray_f ** 2, -1, (kernel_size, kernel_size))
        local_var = np.maximum(local_sq_mean - local_mean ** 2, 0)

        # Threshold high-variance regions
        var_threshold = np.percentile(local_var[local_var > 0], 90)
        high_var = (local_var > var_threshold).astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        high_var = cv2.morphologyEx(high_var, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(high_var, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        results = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_area <= area <= self.max_area:
                x, y, w, h = cv2.boundingRect(cnt)
                results.append({
                    'bbox': (x, y, w, h),
                    'score': 45.0,
                    'method': 'local_contrast',
                    'contour_area': area,
                })
        return results

    def _nms(self, candidates: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
        """Non-maximum suppression to remove duplicate detections."""
        if not candidates:
            return []

        boxes = np.array([c['bbox'] for c in candidates], dtype=float)
        scores = np.array([c['score'] for c in candidates])

        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 0] + boxes[:, 2]
        y2 = boxes[:, 1] + boxes[:, 3]
        areas = boxes[:, 2] * boxes[:, 3]

        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            inter = w * h
            iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]

        return [candidates[i] for i in keep]

    def _filter_nadir(self, candidates: List[Dict], image_width: int) -> List[Dict]:
        """Remove candidates that overlap significantly with the nadir region."""
        if self.nadir_start is None or self.nadir_end is None:
            return candidates

        filtered = []
        for c in candidates:
            x, y, w, h = c['bbox']
            cx = x + w / 2
            # Reject if centre is inside nadir
            if self.nadir_start <= cx <= self.nadir_end:
                continue
            # Reject if mostly inside nadir
            overlap_start = max(x, self.nadir_start)
            overlap_end = min(x + w, self.nadir_end)
            if overlap_end > overlap_start:
                overlap_ratio = (overlap_end - overlap_start) / max(w, 1)
                if overlap_ratio > 0.5:
                    continue
            filtered.append(c)
        return filtered

    def _filter_geometry(self, candidates: List[Dict]) -> List[Dict]:
        """Filter by aspect ratio and size."""
        filtered = []
        for c in candidates:
            x, y, w, h = c['bbox']
            if w <= 0 or h <= 0:
                continue
            aspect = w / h
            if not (self.min_aspect_ratio <= aspect <= self.max_aspect_ratio):
                continue
            filtered.append(c)
        return filtered
