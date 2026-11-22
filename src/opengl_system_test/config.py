from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import HarnessConfig, Scenario, Tolerance

WORKLOADS = {"solid_color", "texture_quadrants", "alpha_blend", "depth_overlap"}
ROOT_KEYS = {"schema_version", "minimum_gl_version", "invalid_shader_probe", "scenarios"}
SCENARIO_KEYS = {
    "name",
    "workload",
    "width",
    "height",
    "warmup_runs",
    "measured_runs",
    "tolerance",
    "max_unique_images",
    "max_p95_ms",
}
TOLERANCE_KEYS = {"channel_delta", "failed_pixel_ratio"}


class ConfigError(ValueError):
    """Raised when a harness configuration violates its schema."""


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _require_keys(data: dict[str, Any], allowed: set[str], location: str) -> None:
    unknown = set(data) - allowed
    if unknown:
        raise ConfigError(f"{location} contains unknown fields: {sorted(unknown)}")


def _bounded_int(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ConfigError(f"{name} must be between {minimum} and {maximum}")
    return value


def _bounded_number(value: Any, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{name} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise ConfigError(f"{name} must be between {minimum} and {maximum}")
    return number


def load_config(path: str | Path) -> HarnessConfig:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    except OSError as exc:
        raise ConfigError(f"cannot read configuration: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON at line {exc.lineno}: {exc.msg}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be an object")
    _require_keys(raw, ROOT_KEYS, "configuration")

    schema_version = _bounded_int(raw.get("schema_version"), "schema_version", 1, 1)
    minimum_gl_version = _bounded_int(
        raw.get("minimum_gl_version", 330), "minimum_gl_version", 330, 460
    )
    invalid_shader_probe = raw.get("invalid_shader_probe", True)
    if not isinstance(invalid_shader_probe, bool):
        raise ConfigError("invalid_shader_probe must be a boolean")

    raw_scenarios = raw.get("scenarios")
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        raise ConfigError("scenarios must be a non-empty array")

    scenarios: list[Scenario] = []
    names: set[str] = set()
    for index, item in enumerate(raw_scenarios):
        location = f"scenarios[{index}]"
        if not isinstance(item, dict):
            raise ConfigError(f"{location} must be an object")
        _require_keys(item, SCENARIO_KEYS, location)
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f"{location}.name must be a non-empty string")
        if name in names:
            raise ConfigError(f"duplicate scenario name: {name}")
        names.add(name)
        workload = item.get("workload")
        if workload not in WORKLOADS:
            raise ConfigError(f"{location}.workload must be one of {sorted(WORKLOADS)}")

        tolerance_raw = item.get("tolerance", {})
        if not isinstance(tolerance_raw, dict):
            raise ConfigError(f"{location}.tolerance must be an object")
        _require_keys(tolerance_raw, TOLERANCE_KEYS, f"{location}.tolerance")
        tolerance = Tolerance(
            channel_delta=_bounded_int(
                tolerance_raw.get("channel_delta", 1),
                f"{location}.tolerance.channel_delta",
                0,
                255,
            ),
            failed_pixel_ratio=_bounded_number(
                tolerance_raw.get("failed_pixel_ratio", 0.0),
                f"{location}.tolerance.failed_pixel_ratio",
                0.0,
                1.0,
            ),
        )
        max_p95_ms = item.get("max_p95_ms")
        if max_p95_ms is not None:
            max_p95_ms = _bounded_number(
                max_p95_ms, f"{location}.max_p95_ms", 0.001, 600_000.0
            )
        scenarios.append(
            Scenario(
                name=name,
                workload=workload,
                width=_bounded_int(item.get("width", 64), f"{location}.width", 8, 4096),
                height=_bounded_int(item.get("height", 64), f"{location}.height", 8, 4096),
                warmup_runs=_bounded_int(
                    item.get("warmup_runs", 1), f"{location}.warmup_runs", 0, 100
                ),
                measured_runs=_bounded_int(
                    item.get("measured_runs", 5), f"{location}.measured_runs", 1, 1000
                ),
                tolerance=tolerance,
                max_unique_images=_bounded_int(
                    item.get("max_unique_images", 1),
                    f"{location}.max_unique_images",
                    1,
                    1000,
                ),
                max_p95_ms=max_p95_ms,
            )
        )

    return HarnessConfig(
        schema_version=schema_version,
        minimum_gl_version=minimum_gl_version,
        invalid_shader_probe=invalid_shader_probe,
        scenarios=tuple(scenarios),
    )
