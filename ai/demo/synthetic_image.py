"""
SONAR-X Synthetic Sonar Image Generator

Generates sonar-like demonstration images for demo/testing.

IMPORTANT:
- These are SYNTHETIC images, NOT real sonar data.
- Every generated image is clearly labelled DEMO / SYNTHETIC.
- Do NOT use for field performance claims.
"""

import numpy as np
import cv2
from typing import Optional
import logging

logger = logging.getLogger('sonarx.demo.synthetic')

IMAGE_WIDTH = 512
IMAGE_HEIGHT = 256


def _base_sonar_image(rng: np.random.Generator) -> np.ndarray:
    """Generate a base sonar-like seabed texture."""
    img = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH), dtype=np.float32)

    # Background seabed — speckled texture
    noise = rng.normal(35, 12, (IMAGE_HEIGHT, IMAGE_WIDTH)).astype(np.float32)
    img += noise

    # Sonar-like striping (across-track variation)
    col_gradient = np.abs(np.arange(IMAGE_WIDTH) - IMAGE_WIDTH // 2).astype(float)
    col_gradient = col_gradient / col_gradient.max()
    col_gradient = (1 - col_gradient * 0.6) * 40
    img += col_gradient[np.newaxis, :]

    # Add horizontal scan lines
    for row in rng.integers(0, IMAGE_HEIGHT, size=15):
        img[row:row + 1, :] += rng.normal(0, 5, (1, IMAGE_WIDTH))

    # Nadir (central dark region)
    nadir_width = 40
    centre = IMAGE_WIDTH // 2
    img[:, centre - nadir_width // 2:centre + nadir_width // 2] *= 0.1

    return img


def _add_target(img: np.ndarray, x: int, y: int, w: int, h: int,
                intensity: float, shadow_len: int, rng: np.random.Generator) -> np.ndarray:
    """Add a bright target with acoustic shadow."""
    # Target body
    cv2.ellipse(img, (x + w // 2, y + h // 2), (w // 2, h // 2), 0, 0, 360,
                intensity, -1)

    # Gaussian smoothing for natural look
    img[max(0, y - 2):min(img.shape[0], y + h + 2),
        max(0, x - 2):min(img.shape[1], x + w + 2)] = cv2.GaussianBlur(
        img[max(0, y - 2):min(img.shape[0], y + h + 2),
            max(0, x - 2):min(img.shape[1], x + w + 2)],
        (5, 5), 1.0
    )

    # Acoustic shadow (dark region on far-range side)
    shadow_x = x + w
    shadow_x_end = min(img.shape[1], shadow_x + shadow_len)
    shadow_region = img[y:y + h, shadow_x:shadow_x_end].copy()
    shadow_region *= 0.1
    img[y:y + h, shadow_x:shadow_x_end] = shadow_region

    return img


def generate_synthetic_sonar(image_key: str) -> np.ndarray:
    """
    Generate a synthetic sonar-like image for the given demo image key.

    Returns a grayscale numpy array (uint8, 256x512).
    """
    seed_map = {
        'marine_debris_01': 42,
        'natural_formation_01': 43,
        'sonar_artifact_01': 44,
        'unknown_anomaly_01': 45,
        'potential_hazard_01': 46,
        'marine_debris_relocated': 47,
    }
    seed = seed_map.get(image_key, 99)
    rng = np.random.default_rng(seed)

    img = _base_sonar_image(rng)

    if image_key == 'marine_debris_01':
        # Compact medium-size target with clear shadow
        img = _add_target(img, x=120, y=80, w=45, h=30, intensity=220, shadow_len=60, rng=rng)
        # Add some surface texture on target
        noise = rng.normal(0, 8, (30, 45)).astype(np.float32)
        img[80:110, 120:165] += noise

    elif image_key == 'natural_formation_01':
        # Diffuse elongated ridge — irregular outline
        for i in range(6):
            ox = rng.integers(-10, 10)
            oy = rng.integers(-8, 8)
            cv2.ellipse(img, (280 + ox, 120 + oy), (50, 25), 15, 0, 360, 90, -1)
        # Weak shadow
        img[100:145, 330:370] *= 0.5

    elif image_key == 'sonar_artifact_01':
        # Horizontal dropout line spanning the full width
        img[195:198, :] = 5  # near black
        # Another partial stripe
        img[120:121, 100:400] = 250  # saturated stripe

    elif image_key == 'unknown_anomaly_01':
        # Ambiguous target — partial shadow, irregular geometry
        img = _add_target(img, x=195, y=140, w=35, h=28, intensity=160, shadow_len=25, rng=rng)
        # Add irregular shape
        noise = rng.normal(0, 15, (28, 35)).astype(np.float32)
        img[140:168, 195:230] += noise

    elif image_key in ('potential_hazard_01',):
        # Large, structured target with very strong backscatter
        img = _add_target(img, x=150, y=90, w=90, h=60, intensity=240, shadow_len=120, rng=rng)
        # Regular rectangular appearance
        cv2.rectangle(img, (150, 90), (240, 150), 230, 2)

    elif image_key == 'marine_debris_relocated':
        # Slightly shifted version of marine_debris_01
        img = _add_target(img, x=130, y=85, w=42, h=28, intensity=215, shadow_len=55, rng=rng)

    # Clip and convert
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img


def save_demo_images(output_dir: str):
    """Save all demo images to disk. Used by scripts."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    keys = [
        'marine_debris_01', 'natural_formation_01', 'sonar_artifact_01',
        'unknown_anomaly_01', 'potential_hazard_01', 'marine_debris_relocated',
    ]

    for key in keys:
        img = generate_synthetic_sonar(key)
        path = os.path.join(output_dir, f'{key}.png')
        cv2.imwrite(path, img)
        print(f"Saved DEMO/SYNTHETIC image: {path}")

    print("\nAll demo images are SYNTHETIC — not real sonar data.")
    print("Label: DATA SOURCE: DEMO")
