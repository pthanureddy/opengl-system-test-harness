from __future__ import annotations

import logging
import time
from pathlib import Path

from .analysis import compare_images, image_sha256, timing_summary
from .graphics import GraphicsSession
from .models import HarnessConfig, ScenarioResult
from .reporting import save_image, write_json, write_junit, write_markdown

LOGGER = logging.getLogger("opengl_system_test")


def run_harness(
    config: HarnessConfig, output_dir: str | Path, backend: str = "auto"
) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    session = GraphicsSession(backend=backend, minimum_gl_version=config.minimum_gl_version)
    results: list[ScenarioResult] = []
    try:
        capabilities = session.capabilities
        LOGGER.info(
            "context_created backend=%s renderer=%s version=%s",
            backend,
            capabilities.get("renderer"),
            capabilities.get("version"),
        )
        invalid_shader_result = None
        if config.invalid_shader_probe:
            compiler_log = session.invalid_shader_probe()
            invalid_shader_result = {
                "observed": True,
                "log_excerpt": " ".join(compiler_log.split())[:500],
            }
            LOGGER.info("expected_shader_failure_observed log=%s", compiler_log.splitlines()[0])

        for scenario in config.scenarios:
            result = ScenarioResult(
                name=scenario.name, workload=scenario.workload, status="failed"
            )
            LOGGER.info(
                "scenario_started name=%s workload=%s size=%sx%s",
                scenario.name,
                scenario.workload,
                scenario.width,
                scenario.height,
            )
            try:
                for _ in range(scenario.warmup_runs):
                    session.render(scenario.workload, scenario.width, scenario.height)

                comparisons = []
                first_actual = None
                first_expected = None
                for _ in range(scenario.measured_runs):
                    start = time.perf_counter_ns()
                    rendered = session.render(scenario.workload, scenario.width, scenario.height)
                    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000.0
                    result.timings_ms.append(round(elapsed_ms, 6))
                    result.image_hashes.append(image_sha256(rendered.actual))
                    comparisons.append(
                        compare_images(rendered.actual, rendered.expected, scenario.tolerance)
                    )
                    if first_actual is None:
                        first_actual = rendered.actual
                        first_expected = rendered.expected

                median_ms, p95_ms = timing_summary(result.timings_ms)
                result.median_ms = round(median_ms, 6)
                result.p95_ms = round(p95_ms, 6)
                result.comparison = max(
                    comparisons,
                    key=lambda item: (item.failed_pixel_ratio, item.max_channel_delta),
                )
                unique_images = len(set(result.image_hashes))
                stable = unique_images <= scenario.max_unique_images
                performance_ok = (
                    scenario.max_p95_ms is None or result.p95_ms <= scenario.max_p95_ms
                )
                result.status = (
                    "passed" if result.comparison.passed and stable and performance_ok else "failed"
                )
                if not stable:
                    result.error = (
                        f"stability limit exceeded: {unique_images} unique images; "
                        f"allowed {scenario.max_unique_images}"
                    )
                elif not performance_ok:
                    result.error = (
                        f"p95 {result.p95_ms:.3f} ms exceeded {scenario.max_p95_ms:.3f} ms"
                    )
                elif not result.comparison.passed:
                    result.error = result.comparison.detail

                actual_path = output / "images" / f"{scenario.name}-actual.png"
                expected_path = output / "images" / f"{scenario.name}-expected.png"
                save_image(actual_path, first_actual)
                save_image(expected_path, first_expected)
                result.actual_image = str(actual_path.relative_to(output)).replace("\\", "/")
                result.expected_image = str(expected_path.relative_to(output)).replace("\\", "/")
            except Exception as exc:  # Keep other scenarios observable after one workload fails.
                result.error = f"{type(exc).__name__}: {exc}"
                LOGGER.exception("scenario_error name=%s", scenario.name)
            results.append(result)
            LOGGER.info(
                "scenario_finished name=%s status=%s median_ms=%s p95_ms=%s "
                "unique_images=%s max_channel_delta=%s failed_pixel_ratio=%s error=%s",
                result.name,
                result.status,
                result.median_ms,
                result.p95_ms,
                len(set(result.image_hashes)),
                result.comparison.max_channel_delta if result.comparison else None,
                result.comparison.failed_pixel_ratio if result.comparison else None,
                result.error,
            )

        report = {
            "schema_version": 1,
            "status": "passed" if all(item.status == "passed" for item in results) else "failed",
            "backend": backend,
            "capabilities": capabilities,
            "invalid_shader_probe": invalid_shader_result,
            "scenario_count": len(results),
            "passed_scenario_count": sum(item.status == "passed" for item in results),
            "scenarios": [item.to_dict() for item in results],
        }
        write_json(output / "report.json", report)
        write_junit(output / "report.junit.xml", results)
        write_markdown(output / "summary.md", report)
        return report
    finally:
        session.close()
