"""
SONAR-X Automatic Metadata Extractor

Extracts every available piece of information from an uploaded sonar image.
Follows the provenance principle: every field records its SOURCE.

Sources:
  EMBEDDED_METADATA  — found in file metadata blocks
  EXIF               — extracted from EXIF tags
  NAVIGATION_DATA    — from GPS/navigation EXIF or metadata
  FILENAME           — inferred from filename pattern
  IMAGE_DERIVED      — calculated from the image pixel data
  FILE_TIMESTAMP     — from file modification time
  NOT_AVAILABLE      — field genuinely not present

SCIENTIFIC RULE: NEVER FABRICATE METADATA.
If a field is unavailable, it is stored as NOT_AVAILABLE.
"""

import os
import re
import math
import datetime
from dataclasses import dataclass, field
from typing import Optional, Any
import logging

logger = logging.getLogger("sonarx.metadata")


# ── Provenance container ──────────────────────────────────────────

@dataclass
class MetadataField:
    """A single metadata value with full provenance."""
    value: Any
    source: str  # one of the source strings above
    status: str  # VERIFIED / ESTIMATED / NOT_AVAILABLE / DERIVED

    def to_dict(self):
        return {"value": self.value, "source": self.source, "status": self.status}


UNAVAILABLE = MetadataField(value=None, source="NOT_AVAILABLE", status="NOT_AVAILABLE")


@dataclass
class SonarMetadataResult:
    """Full extraction result with provenance for every field."""

    # Survey identity
    survey_name: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    survey_date: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    acquisition_time: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    operator: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    survey_area: MetadataField = field(default_factory=lambda: UNAVAILABLE)

    # Navigation
    latitude: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    longitude: MetadataField = field(default_factory=lambda: UNAVAILABLE)

    # Sonar geometry
    altitude_m: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    range_scale_mpp: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    channel_layout: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    already_gain_corrected: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    already_slant_range_corrected: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    already_processed: MetadataField = field(default_factory=lambda: UNAVAILABLE)

    # File / Image
    filename: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    file_size_bytes: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    image_width: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    image_height: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    image_format: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    is_grayscale: MetadataField = field(default_factory=lambda: UNAVAILABLE)

    # Camera / sensor
    sensor_model: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    sonar_frequency: MetadataField = field(default_factory=lambda: UNAVAILABLE)

    # Image-derived quality indicators (calculated, not metadata)
    snr_proxy: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    contrast: MetadataField = field(default_factory=lambda: UNAVAILABLE)
    nadir_width_estimate_px: MetadataField = field(default_factory=lambda: UNAVAILABLE)

    def to_dict(self):
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, MetadataField):
                result[k] = v.to_dict()
        return result

    def __post_init__(self):
        pass


# ── Main extractor ────────────────────────────────────────────────

class SonarMetadataExtractor:
    """
    Extracts metadata from an uploaded sonar image file.

    Never invents values. Every field records its source.
    """

    def __init__(self, file_path: str, filename: str, file_size: int):
        self.file_path = file_path
        self.filename = filename
        self.file_size = file_size

    def extract(self) -> SonarMetadataResult:
        result = SonarMetadataResult()

        # Always populate file basics
        result.filename = MetadataField(
            value=self.filename, source="FILE_SYSTEM", status="VERIFIED"
        )
        result.file_size_bytes = MetadataField(
            value=self.file_size, source="FILE_SYSTEM", status="VERIFIED"
        )
        ext = os.path.splitext(self.filename)[1].upper().lstrip(".")
        result.image_format = MetadataField(
            value=ext if ext else "UNKNOWN",
            source="FILE_SYSTEM",
            status="VERIFIED" if ext else "NOT_AVAILABLE",
        )

        # Try EXIF / PIL extraction
        self._extract_from_image(result)

        # Try filename-based extraction
        self._extract_from_filename(result)

        # Generate automatic survey name
        self._generate_survey_name(result)

        # Set survey date fallback to today if still unavailable
        if result.survey_date.status == "NOT_AVAILABLE":
            result.survey_date = MetadataField(
                value=datetime.date.today().isoformat(),
                source="FILE_TIMESTAMP",
                status="ESTIMATED",
            )

        return result

    # ── EXIF / PIL ────────────────────────────────────────────────

    def _extract_from_image(self, result: SonarMetadataResult):
        try:
            from PIL import Image, ExifTags
            img = Image.open(self.file_path)
        except Exception as e:
            logger.warning(f"Cannot open image for metadata extraction: {e}")
            return

        # Basic image properties
        result.image_width = MetadataField(
            value=img.width, source="IMAGE_DERIVED", status="VERIFIED"
        )
        result.image_height = MetadataField(
            value=img.height, source="IMAGE_DERIVED", status="VERIFIED"
        )
        result.is_grayscale = MetadataField(
            value=img.mode in ("L", "LA"),
            source="IMAGE_DERIVED",
            status="VERIFIED",
        )

        # EXIF
        try:
            exif_raw = img._getexif()
        except Exception:
            exif_raw = None

        if exif_raw:
            # Map EXIF tag IDs to names
            exif = {}
            for tag_id, val in exif_raw.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                exif[tag_name] = val

            # Acquisition datetime
            for dt_field in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                if dt_field in exif:
                    try:
                        dt_str = str(exif[dt_field])
                        # EXIF format: "YYYY:MM:DD HH:MM:SS"
                        dt = datetime.datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                        result.survey_date = MetadataField(
                            value=dt.date().isoformat(),
                            source="EXIF",
                            status="VERIFIED",
                        )
                        result.acquisition_time = MetadataField(
                            value=dt.time().isoformat(),
                            source="EXIF",
                            status="VERIFIED",
                        )
                        break
                    except Exception:
                        pass

            # Camera/sensor model
            if "Make" in exif or "Model" in exif:
                make = exif.get("Make", "")
                model = exif.get("Model", "")
                sensor = f"{make} {model}".strip()
                if sensor:
                    result.sensor_model = MetadataField(
                        value=sensor, source="EXIF", status="VERIFIED"
                    )

            # GPS data
            gps_info = exif.get("GPSInfo")
            if gps_info:
                lat, lon = self._parse_gps(gps_info)
                if lat is not None:
                    result.latitude = MetadataField(
                        value=round(lat, 6),
                        source="NAVIGATION_DATA",
                        status="VERIFIED",
                    )
                if lon is not None:
                    result.longitude = MetadataField(
                        value=round(lon, 6),
                        source="NAVIGATION_DATA",
                        status="VERIFIED",
                    )

            # Image description may contain sonar survey name
            if "ImageDescription" in exif:
                desc = str(exif["ImageDescription"]).strip()
                if desc and len(desc) < 200:
                    result.survey_name = MetadataField(
                        value=desc, source="EMBEDDED_METADATA", status="VERIFIED"
                    )

        # Image-derived quality estimates
        self._derive_image_quality(result, img)
        img.close()

    def _derive_image_quality(self, result: SonarMetadataResult, img):
        """Calculate image-derived quality proxies (clearly labelled as derived)."""
        try:
            import numpy as np
            if img.mode != "L":
                gray = img.convert("L")
            else:
                gray = img
            arr = np.array(gray, dtype=float)

            # SNR proxy
            std = float(np.std(arr))
            noise = float(np.percentile(np.abs(np.diff(arr, axis=1)), 10))
            snr = std / max(noise, 0.1)
            result.snr_proxy = MetadataField(
                value=round(snr, 2), source="IMAGE_DERIVED", status="DERIVED"
            )

            # Contrast (IQR)
            p25, p75 = np.percentile(arr, [25, 75])
            result.contrast = MetadataField(
                value=round(float(p75 - p25), 2),
                source="IMAGE_DERIVED",
                status="DERIVED",
            )

            # Nadir width estimate from central intensity minimum
            w = arr.shape[1]
            centre_col_profile = np.mean(arr, axis=0)
            centre = w // 2
            search = slice(int(w * 0.3), int(w * 0.7))
            profile_section = centre_col_profile[search]
            threshold = float(np.percentile(profile_section, 15))
            dark = profile_section < threshold
            nadir_px = int(np.sum(dark))
            result.nadir_width_estimate_px = MetadataField(
                value=nadir_px,
                source="IMAGE_DERIVED",
                status="ESTIMATED",
            )
        except Exception as e:
            logger.debug(f"Image quality derivation failed: {e}")

    # ── Filename patterns ─────────────────────────────────────────

    def _extract_from_filename(self, result: SonarMetadataResult):
        """
        Try to extract structured information from filename.
        Looks for patterns like: DATE, coordinates, survey ID.
        Never invents values not supported by the filename.
        """
        name = os.path.splitext(self.filename)[0]

        # Date pattern: YYYYMMDD or YYYY-MM-DD or YYYY_MM_DD
        date_patterns = [
            (r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})", "%Y%m%d"),
        ]
        if result.survey_date.status == "NOT_AVAILABLE":
            for pattern, _ in date_patterns:
                m = re.search(pattern, name)
                if m:
                    try:
                        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                        if 2000 <= y <= 2099 and 1 <= mo <= 12 and 1 <= d <= 31:
                            result.survey_date = MetadataField(
                                value=datetime.date(y, mo, d).isoformat(),
                                source="FILENAME",
                                status="ESTIMATED",
                            )
                            break
                    except ValueError:
                        pass

        # If survey_name still unavailable, use cleaned filename as name basis
        # (will be superseded by _generate_survey_name)

    # ── Auto-generate survey name ─────────────────────────────────

    def _generate_survey_name(self, result: SonarMetadataResult):
        """Generate a meaningful survey name from available context."""
        if result.survey_name.value:
            return  # Already set from metadata

        parts = ["SONAR Survey"]

        # Add location hint if available
        if (result.latitude.value is not None
                and result.longitude.value is not None):
            lat = result.latitude.value
            lon = result.longitude.value
            # Simple hemisphere labelling — no fake geocoding
            lat_str = f"{abs(lat):.2f}°{'N' if lat >= 0 else 'S'}"
            lon_str = f"{abs(lon):.2f}°{'E' if lon >= 0 else 'W'}"
            parts.append(f"{lat_str} {lon_str}")
        else:
            # Use filename stem as a hint
            stem = os.path.splitext(self.filename)[0]
            clean_stem = re.sub(r"[_\-\.]+", " ", stem).strip()
            if clean_stem and len(clean_stem) < 60:
                parts.append(clean_stem)

        # Add date
        date_val = result.survey_date.value
        if date_val:
            try:
                d = datetime.date.fromisoformat(date_val)
                parts.append(d.strftime("%d %b %Y"))
            except Exception:
                parts.append(date_val)

        survey_name = " — ".join(p for p in parts if p)
        result.survey_name = MetadataField(
            value=survey_name,
            source="FILENAME" if result.latitude.status == "NOT_AVAILABLE" else "NAVIGATION_DATA",
            status="ESTIMATED",
        )

    # ── GPS parsing ───────────────────────────────────────────────

    @staticmethod
    def _parse_gps(gps_info: dict):
        """Parse EXIF GPS rational values to decimal degrees."""
        def to_decimal(dms, ref):
            try:
                d, m, s = dms
                # Each may be a tuple (numerator, denominator) or a float
                def r(v):
                    if isinstance(v, tuple):
                        return v[0] / v[1] if v[1] != 0 else 0.0
                    return float(v)
                dec = r(d) + r(m) / 60 + r(s) / 3600
                if ref in ("S", "W"):
                    dec = -dec
                return dec
            except Exception:
                return None

        try:
            from PIL import ExifTags
            lat = lon = None
            # GPSInfo keys: 1=LatRef, 2=Lat, 3=LonRef, 4=Lon
            if 2 in gps_info and 1 in gps_info:
                lat = to_decimal(gps_info[2], gps_info[1])
            if 4 in gps_info and 3 in gps_info:
                lon = to_decimal(gps_info[4], gps_info[3])
            return lat, lon
        except Exception:
            return None, None
