import json
import os

import pytest

from opengl_system_test.cli import main
from opengl_system_test.config import load_config
from opengl_system_test.runner import run_harness


def _config_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "minimum_gl_version": 330,
                "invalid_shader_probe": True,
                "scenarios": [
                    {
                        "name": "solid",
                        "workload": "solid_color",
                        "width": 16,
                        "height": 16,
                        "warmup_runs": 0,
                        "measured_runs": 1,
                        "tolerance": {"channel_delta": 1, "failed_pixel_ratio": 0.0},
                        "max_unique_images": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_validate_command(tmp_path, capsys):
    path = _config_file(tmp_path)
    assert main(["validate", "--config", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True


@pytest.mark.graphics
def test_runner_writes_all_reports(tmp_path):
    config = load_config(_config_file(tmp_path))
    output = tmp_path / "artifacts"
    report = run_harness(
        config, output, backend=os.getenv("OPENGL_TEST_BACKEND", "auto")
    )
    assert report["status"] == "passed"
    assert (output / "report.json").is_file()
    assert (output / "report.junit.xml").is_file()
    assert (output / "summary.md").is_file()
    assert (output / "images" / "solid-actual.png").is_file()


def test_invalid_config_returns_setup_exit_code(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("{}", encoding="utf-8")
    assert main(["validate", "--config", str(path)]) == 2
    assert "configuration error" in capsys.readouterr().err
