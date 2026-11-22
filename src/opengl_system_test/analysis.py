from __future__ import annotations

import hashlib
import math
import statistics

import numpy as np

from .models import Comparison, Tolerance


def image_sha256(image: np.ndarray) -> str:
    return hashlib.sha256(image.tobytes(order="C")).hexdigest()


def compare_images(
    actual: np.ndarray, expected: np.ndarray, tolerance: Tolerance
) -> Comparison:
    if actual.shape != expected.shape:
        return Comparison(
            passed=False,
            max_channel_delta=255,
            mean_channel_delta=255.0,
            failed_pixel_count=max(actual.size, expected.size),
            failed_pixel_ratio=1.0,
            detail=f"shape mismatch: actual={actual.shape}, expected={expected.shape}",
        )
    delta = np.abs(actual.astype(np.int16) - expected.astype(np.int16))
    failed_pixels = np.any(delta > tolerance.channel_delta, axis=2)
    failed_count = int(np.count_nonzero(failed_pixels))
    pixel_count = actual.shape[0] * actual.shape[1]
    ratio = failed_count / pixel_count
    passed = ratio <= tolerance.failed_pixel_ratio
    return Comparison(
        passed=passed,
        max_channel_delta=int(delta.max(initial=0)),
        mean_channel_delta=float(delta.mean()),
        failed_pixel_count=failed_count,
        failed_pixel_ratio=ratio,
        detail=(
            f"{failed_count}/{pixel_count} pixels exceeded channel delta "
            f"{tolerance.channel_delta}; allowed ratio={tolerance.failed_pixel_ratio:.6f}"
        ),
    )


def percentile_95(values: list[float]) -> float:
    if not values:
        raise ValueError("cannot calculate percentile for an empty list")
    ordered = sorted(values)
    index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[index]


def timing_summary(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError("timing list cannot be empty")
    return statistics.median(values), percentile_95(values)
