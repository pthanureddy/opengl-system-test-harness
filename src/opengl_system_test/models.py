from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Tolerance:
    channel_delta: int = 1
    failed_pixel_ratio: float = 0.0


@dataclass(frozen=True)
class Scenario:
    name: str
    workload: str
    width: int
    height: int
    warmup_runs: int
    measured_runs: int
    tolerance: Tolerance
    max_unique_images: int = 1
    max_p95_ms: float | None = None


@dataclass(frozen=True)
class HarnessConfig:
    schema_version: int
    minimum_gl_version: int
    invalid_shader_probe: bool
    scenarios: tuple[Scenario, ...]


@dataclass(frozen=True)
class Comparison:
    passed: bool
    max_channel_delta: int
    mean_channel_delta: float
    failed_pixel_count: int
    failed_pixel_ratio: float
    detail: str


@dataclass
class ScenarioResult:
    name: str
    workload: str
    status: str
    image_hashes: list[str] = field(default_factory=list)
    timings_ms: list[float] = field(default_factory=list)
    median_ms: float | None = None
    p95_ms: float | None = None
    comparison: Comparison | None = None
    actual_image: str | None = None
    expected_image: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
