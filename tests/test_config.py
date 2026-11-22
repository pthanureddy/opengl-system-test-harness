import json

import pytest

from opengl_system_test.config import ConfigError, load_config


def _valid_config():
    return {
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


def test_loads_valid_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(_valid_config()), encoding="utf-8")
    config = load_config(path)
    assert config.minimum_gl_version == 330
    assert config.scenarios[0].workload == "solid_color"


def test_rejects_unknown_field(tmp_path):
    data = _valid_config()
    data["unexpected"] = True
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ConfigError, match="unknown fields"):
        load_config(path)


def test_rejects_duplicate_json_key(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"schema_version": 1, "schema_version": 1}', encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate JSON key"):
        load_config(path)


@pytest.mark.parametrize("width", [True, 7, 4097])
def test_rejects_invalid_dimensions(tmp_path, width):
    data = _valid_config()
    data["scenarios"][0]["width"] = width
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ConfigError, match="width"):
        load_config(path)


def test_rejects_duplicate_scenario_names(tmp_path):
    data = _valid_config()
    data["scenarios"].append(dict(data["scenarios"][0]))
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate scenario name"):
        load_config(path)
