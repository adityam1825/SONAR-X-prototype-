"""
SONAR-X Sonar Preprocessing Engine
Implements: nadir handling, gain correction, slant-range correction,
noise reduction, contrast enhancement, quality assessment.

Scientific notes:
- Side-scan sonar does NOT directly provide water temperature.
- Slant-range correction requires altitude + range scale metadata.
- If metadata is unavailable, correction is SKIPPED and clearly labelled.
- The nadir region is the water-column gap; seabed information cannot be
  fabricated inside it.
"""

import numpy as np
import cv2
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger('sonarx.preprocessing')


@dataclass
class PreprocessingResult:
    """Result container for the preprocessing pipeline."""
    original: np.ndarray
    processed: np.ndarray

    # Step statuses
    nadir_status: str = 'SKIPPED'
    gain_status: str = 'SKIPPED'
    slant_range_status: str = 'SKIPPED'
    noise_status: str = 'SKIPPED'
    contrast_status: str = 'SKIPPED'
    quality_status: str = 'SKIPPED'

    # Reasons for skip/estimate
    nadir_reason: str = ''
    gain_reason: str = ''
    slant_range_reason: str = ''

    # Nadir
    nadir_start: Optional[int] = None
    nadir_end: Optional[int] = None
    nadir_method: str = ''

    # Quality
    quality_score: float = 0.0
    quality_level: str = 'UNKNOWN'
    saturation_ratio: float = 0.0
    dropout_ratio: float = 0.0
    snr_proxy: float = 0.0
    nadir_width_px: int = 0
    image_contrast: float = 0.0
    usable_area_ratio: float = 0.0
    quality_flags: list = field(default_factory=list)

    # Intensity profile
    across_track_profile: Optional[np.ndarray] = None

    # Pixel scale after correction
    pixel_scale_gpp: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'nadir': {
                'status': self.nadir_status,
                'reason': self.nadir_reason,
                'start_px': self.nadir_start,
                'end_px': self.nadir_end,
                'method': self.nadir_method,
                'width_px': self.nadir_width_px,
            },
            'gain': {
                'status': self.gain_status,
                'reason': self.gain_reason,
            },
            'slant_range': {
                'status': self.slant_range_status,
                'reason': self.slant_range_reason,
                'pixel_scale_gpp': self.pixel_scale_gpp,
            },
            'noise': {'status': self.noise_status},
            'contrast': {'status': self.contrast_status},
            'quality': {
                'status': self.quality_status,
                'score': round(self.quality_score, 1),
                'level': self.quality_level,
                'saturation_ratio': round(self.saturation_ratio, 4),
                'dropout_ratio': round(self.dropout_ratio, 4),
                'snr_proxy': round(self.snr_proxy, 2),
                'image_contrast': round(self.image_contrast, 2),
                'usable_area_ratio': round(self.usable_area_ratio, 4),
                'flags': self.quality_flags,
            },
        }


class SonarPreprocessor:
    """
    Sonar-specific preprocessing pipeline.

    Parameters
    ----------
    altitude_m : float or None
        Sensor altitude above seabed. Required for slant-range correction.
    range_scale_mpp : float or None
        Slant-range scale (metres per pixel). Required for slant-range correction.
    already_gain_corrected : bool
        If True, skip gain correction.
    already_slant_range_corrected : bool
        If True, skip slant-range correction.
    nadir_override : tuple or None
        (start_px, end_px) override for nadir region.
    median_filter_size : int
        Kernel size for median noise filter (must be odd).
    clahe_clip_limit : float
        Clip limit for CLAHE contrast enhancement.
    clahe_tile_size : int
        Tile grid size for CLAHE.
    """

    def __init__(
        self,
        altitude_m: Optional[float] = None,
        range_scale_mpp: Optional[float] = None,
        already_gain_corrected: bool = False,
        already_slant_range_corrected: bool = False,
        nadir_override: Optional[Tuple[int, int]] = None,
        median_filter_size: int = 3,
        clahe_clip_limit: float = 2.0,
        clahe_tile_size: int = 8,
    ):
        self.altitude_m = altitude_m
        self.range_scale_mpp = range_scale_mpp
        self.already_gain_corrected = already_gain_corrected
        self.already_slant_range_corrected = already_slant_range_corrected
        self.nadir_override = nadir_override
        self.median_filter_size = median_filter_size if median_filter_size % 2 == 1 else median_filter_size + 1
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_size = clahe_tile_size

    def run(self, image: np.ndarray) -> PreprocessingResult:
        """Execute the full preprocessing pipeline."""
        if image is None or image.size == 0:
            raise ValueError("Invalid input image.")

        # Ensure grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        result = PreprocessingResult(
            original=gray.copy(),
            processed=gray.copy(),
        )

        # Step 1: Nadir gap handling
        self._handle_nadir(result)

        # Step 2: Gain correction
        self._gain_correction(result)

        # Step 3: Slant-range correction
        self._slant_range_correction(result)

        # Step 4: Noise reduction
        self._noise_reduction(result)

        # Step 5: Contrast enhancement
        self._contrast_enhancement(result)

        # Step 6: Quality assessment
        self._quality_assessment(result)

        # Compute across-track intensity profile
        result.across_track_profile = self._compute_across_track_profile(result.processed)

        return result

    # ---------------------------------------------------------------
    # Step 1 – Nadir gap handling
    # ---------------------------------------------------------------

    def _handle_nadir(self, result: PreprocessingResult):
        img = result.processed
        h, w = img.shape

        if self.nadir_override is not None:
            start, end = self.nadir_override
            result.nadir_start = max(0, int(start))
            result.nadir_end = min(w - 1, int(end))
            result.nadir_method = 'OVERRIDE'
            result.nadir_status = 'APPLIED'
            result.nadir_reason = 'Operator-provided nadir region used.'
        else:
            start, end = self._estimate_nadir(img)
            result.nadir_start = start
            result.nadir_end = end
            result.nadir_method = 'ESTIMATED'
            result.nadir_status = 'ESTIMATED'
            result.nadir_reason = (
                'Nadir estimated from across-track intensity profile. '
                'No metadata available. Operator should verify.'
            )

        result.nadir_width_px = max(0, result.nadir_end - result.nadir_start)

        # Mask the nadir region with a constant (do NOT interpolate/invent seabed)
        nadir_value = int(np.median(img[:, :max(1, result.nadir_start)]) * 0.2)
        img[:, result.nadir_start:result.nadir_end] = nadir_value
        result.processed = img

    def _estimate_nadir(self, img: np.ndarray) -> Tuple[int, int]:
        """
        Estimate nadir region from the across-track intensity profile.
        The nadir is typically a dark low-return zone near the image centre.
        """
        h, w = img.shape
        profile = np.mean(img, axis=0).astype(float)

        # Find the minimum-intensity region in the central 40% of the image
        centre = w // 2
        search_start = int(w * 0.3)
        search_end = int(w * 0.7)
        centre_profile = profile[search_start:search_end]

        threshold = np.percentile(centre_profile, 15)
        dark_mask = centre_profile < threshold

        # Find contiguous dark region closest to centre
        nadir_start = search_start
        nadir_end = search_end

        # Simple approach: grow from centre until intensity rises
        left = centre - search_start
        right = centre - search_start

        while left > 0 and dark_mask[left]:
            left -= 1
        while right < len(dark_mask) - 1 and dark_mask[right]:
            right += 1

        nadir_start = search_start + left
        nadir_end = search_start + right

        # Enforce minimum 5 px nadir width
        if nadir_end - nadir_start < 5:
            nadir_start = max(0, centre - 10)
            nadir_end = min(w, centre + 10)

        return nadir_start, nadir_end

    # ---------------------------------------------------------------
    # Step 2 – Range-dependent gain correction
    # ---------------------------------------------------------------

    def _gain_correction(self, result: PreprocessingResult):
        if self.already_gain_corrected:
            result.gain_status = 'SKIPPED'
            result.gain_reason = 'Image already gain-corrected (survey metadata flag).'
            return

        img = result.processed.astype(float)
        h, w = img.shape

        # Compute robust median across-track profile
        profile = np.median(img, axis=0).astype(float)

        # Smooth profile to avoid over-correcting small targets
        kernel_size = max(21, w // 10)
        if kernel_size % 2 == 0:
            kernel_size += 1
        smoothed = cv2.GaussianBlur(profile.reshape(1, -1), (kernel_size, 1), 0).flatten()

        # Avoid divide-by-zero
        smoothed = np.where(smoothed < 1.0, 1.0, smoothed)
        global_median = np.median(smoothed[smoothed > 5.0])
        if global_median < 1.0:
            global_median = 128.0

        gain_map = global_median / smoothed
        # Clip gain to reasonable range to avoid amplifying noise
        gain_map = np.clip(gain_map, 0.1, 5.0)

        corrected = img * gain_map[np.newaxis, :]
        corrected = np.clip(corrected, 0, 255).astype(np.uint8)

        # Preserve nadir mask
        if result.nadir_start is not None:
            corrected[:, result.nadir_start:result.nadir_end] = \
                result.processed[:, result.nadir_start:result.nadir_end]

        result.processed = corrected
        result.gain_status = 'APPLIED'
        result.gain_reason = 'Range-dependent gain correction using robust median profile.'

    # ---------------------------------------------------------------
    # Step 3 – Slant-range correction
    # ---------------------------------------------------------------

    def _slant_range_correction(self, result: PreprocessingResult):
        if self.already_slant_range_corrected:
            result.slant_range_status = 'SKIPPED'
            result.slant_range_reason = 'Image already slant-range corrected (survey metadata flag).'
            return

        if self.altitude_m is None or self.range_scale_mpp is None:
            result.slant_range_status = 'NOT_APPLIED'
            result.slant_range_reason = (
                'Slant-range correction skipped — altitude and/or range scale unavailable. '
                'Geometry is approximate because required sonar metadata is unavailable.'
            )
            return

        img = result.processed.astype(float)
        h, w = img.shape
        centre = w // 2

        # Build ground-range lookup table for each column
        # ground_range = sqrt(slant_range^2 - altitude^2)
        col_indices = np.arange(w, dtype=float)
        slant_ranges = np.abs(col_indices - centre) * self.range_scale_mpp

        # Columns within nadir (slant range < altitude) are invalid
        valid = slant_ranges >= self.altitude_m
        ground_ranges = np.where(
            valid,
            np.sqrt(np.maximum(slant_ranges ** 2 - self.altitude_m ** 2, 0.0)),
            0.0,
        )

        if ground_ranges.max() < 1.0:
            result.slant_range_status = 'NOT_APPLIED'
            result.slant_range_reason = 'Metadata values produced invalid geometry. Correction skipped.'
            return

        # Compute pixel scale (ground-range per pixel after correction)
        max_ground_range = ground_ranges.max()
        result.pixel_scale_gpp = max_ground_range / (w / 2.0) if w > 0 else None

        # Resample: for each output column compute source column via inverse mapping
        output = np.zeros_like(img)
        port_output = np.linspace(0, max_ground_range, centre)
        stbd_output = np.linspace(0, max_ground_range, w - centre)

        def _gr_to_col(gr_arr, side_offset, sign):
            sl = np.sqrt(np.maximum(gr_arr ** 2 + self.altitude_m ** 2, 0.0))
            src_col = (sl / self.range_scale_mpp * sign + centre).astype(int)
            return np.clip(src_col, 0, w - 1)

        port_src = _gr_to_col(port_output[::-1], 0, -1)
        stbd_src = _gr_to_col(stbd_output, 0, 1)

        output[:, :centre] = img[:, port_src]
        output[:, centre:] = img[:, stbd_src]

        # Preserve nadir mask
        if result.nadir_start is not None:
            output[:, result.nadir_start:result.nadir_end] = \
                result.processed[:, result.nadir_start:result.nadir_end]

        result.processed = np.clip(output, 0, 255).astype(np.uint8)
        result.slant_range_status = 'APPLIED'
        result.slant_range_reason = (
            f'Slant-range corrected using altitude={self.altitude_m}m, '
            f'range_scale={self.range_scale_mpp}m/px.'
        )

    # ---------------------------------------------------------------
    # Step 4 – Noise reduction
    # ---------------------------------------------------------------

    def _noise_reduction(self, result: PreprocessingResult):
        img = result.processed
        denoised = cv2.medianBlur(img, self.median_filter_size)

        # Preserve nadir mask
        if result.nadir_start is not None:
            denoised[:, result.nadir_start:result.nadir_end] = \
                img[:, result.nadir_start:result.nadir_end]

        result.processed = denoised
        result.noise_status = 'APPLIED'

    # ---------------------------------------------------------------
    # Step 5 – Contrast enhancement (CLAHE)
    # ---------------------------------------------------------------

    def _contrast_enhancement(self, result: PreprocessingResult):
        img = result.processed
        tile = (self.clahe_tile_size, self.clahe_tile_size)
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, tileGridSize=tile)
        enhanced = clahe.apply(img)

        # Preserve nadir mask
        if result.nadir_start is not None:
            enhanced[:, result.nadir_start:result.nadir_end] = \
                img[:, result.nadir_start:result.nadir_end]

        result.processed = enhanced
        result.contrast_status = 'APPLIED'

    # ---------------------------------------------------------------
    # Step 6 – Quality assessment
    # ---------------------------------------------------------------

    def _quality_assessment(self, result: PreprocessingResult):
        img = result.processed.astype(float)
        h, w = img.shape
        total_px = h * w

        # Saturation ratio (near 0 or 255)
        saturated = np.sum((img <= 2) | (img >= 253))
        result.saturation_ratio = float(saturated) / total_px

        # Dropout ratio (rows where more than 80% of pixels are black)
        row_means = np.mean(img, axis=1)
        dropout_rows = np.sum(row_means < 5)
        result.dropout_ratio = float(dropout_rows) / h

        # SNR proxy: ratio of signal std to noise floor estimate
        signal_std = float(np.std(img))
        noise_floor = float(np.percentile(np.abs(np.diff(img, axis=1)), 10))
        result.snr_proxy = signal_std / max(noise_floor, 0.1)

        # Image contrast (inter-quartile range)
        p25, p75 = np.percentile(img, [25, 75])
        result.image_contrast = float(p75 - p25)

        # Usable area (excluding nadir + saturated)
        nadir_px = 0
        if result.nadir_start is not None and result.nadir_end is not None:
            nadir_px = h * (result.nadir_end - result.nadir_start)
        result.usable_area_ratio = max(0.0, 1.0 - (nadir_px + saturated) / max(total_px, 1))
        result.nadir_width_px = result.nadir_end - result.nadir_start if result.nadir_start is not None else 0

        # Composite quality score (0–100)
        score = 100.0
        flags = []

        if result.saturation_ratio > 0.3:
            score -= 20
            flags.append('HIGH_SATURATION')
        elif result.saturation_ratio > 0.1:
            score -= 10
            flags.append('MODERATE_SATURATION')

        if result.dropout_ratio > 0.2:
            score -= 25
            flags.append('HIGH_DROPOUT')
        elif result.dropout_ratio > 0.05:
            score -= 10
            flags.append('MODERATE_DROPOUT')

        if result.image_contrast < 20:
            score -= 15
            flags.append('LOW_CONTRAST')
        elif result.image_contrast < 40:
            score -= 5

        if result.snr_proxy < 3:
            score -= 15
            flags.append('LOW_SNR')

        result.quality_score = max(0.0, min(100.0, score))

        if result.quality_score >= 75:
            result.quality_level = 'GOOD'
        elif result.quality_score >= 45:
            result.quality_level = 'MODERATE'
        else:
            result.quality_level = 'POOR'
            flags.append('LOW_QUALITY')

        result.quality_flags = flags
        result.quality_status = 'COMPLETE'

    # ---------------------------------------------------------------
    # Utility
    # ---------------------------------------------------------------

    def _compute_across_track_profile(self, img: np.ndarray) -> np.ndarray:
        """Compute mean intensity profile across-track (column-wise)."""
        return np.mean(img, axis=0).tolist()
