import numpy as np
import pytest

from opengl_system_test.analysis import compare_images, image_sha256, percentile_95
from opengl_system_test.models import Tolerance


def test_identical_images_pass():
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    result = compare_images(image, image.copy(), Tolerance(channel_delta=0))
    assert result.passed
    assert result.failed_pixel_count == 0


def test_pixel_delta_fails_when_ratio_exceeded():
    actual = np.zeros((2, 2, 3), dtype=np.uint8)
    expected = actual.copy()
    expected[0, 0] = (10, 0, 0)
    result = compare_images(actual, expected, Tolerance(channel_delta=1, failed_pixel_ratio=0.0))
    assert not result.passed
    assert result.failed_pixel_count == 1
    assert result.failed_pixel_ratio == pytest.approx(0.25)


def test_shape_mismatch_is_reported():
    a = np.zeros((2, 2, 3), dtype=np.uint8)
    b = np.zeros((3, 2, 3), dtype=np.uint8)
    result = compare_images(a, b, Tolerance())
    assert not result.passed
    assert "shape mismatch" in result.detail


def test_hash_changes_with_image_content():
    first = np.zeros((2, 2, 3), dtype=np.uint8)
    second = first.copy()
    second[0, 0, 0] = 1
    assert image_sha256(first) != image_sha256(second)


def test_percentile_95_uses_nearest_rank():
    assert percentile_95([1.0, 2.0, 3.0, 4.0, 5.0]) == 5.0


def test_percentile_rejects_empty_list():
    with pytest.raises(ValueError):
        percentile_95([])
