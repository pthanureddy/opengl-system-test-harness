import os

import pytest

from opengl_system_test.analysis import compare_images
from opengl_system_test.graphics import GraphicsSession
from opengl_system_test.models import Tolerance


@pytest.fixture(scope="module")
def session():
    graphics = GraphicsSession(backend=os.getenv("OPENGL_TEST_BACKEND", "auto"))
    yield graphics
    graphics.close()


@pytest.mark.graphics
def test_context_reports_renderer(session):
    assert session.capabilities["version_code"] >= 330
    assert session.capabilities["renderer"] != "unknown"


@pytest.mark.graphics
@pytest.mark.parametrize(
    ("workload", "channel_delta"),
    [
        ("solid_color", 1),
        ("texture_quadrants", 0),
        ("alpha_blend", 1),
        ("depth_overlap", 0),
    ],
)
def test_workload_matches_reference(session, workload, channel_delta):
    rendered = session.render(workload, 32, 24)
    comparison = compare_images(
        rendered.actual, rendered.expected, Tolerance(channel_delta=channel_delta)
    )
    assert comparison.passed, comparison.detail


@pytest.mark.graphics
def test_invalid_shader_returns_compiler_log(session):
    log = session.invalid_shader_probe()
    assert log
    assert "shader" in log.lower()
