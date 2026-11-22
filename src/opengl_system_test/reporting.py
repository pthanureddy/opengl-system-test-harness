from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from PIL import Image

from .models import ScenarioResult


def save_image(path: str | Path, image) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # OpenGL framebuffer rows begin at the lower-left; PNG viewers expect top-left.
    Image.fromarray(image[::-1], mode="RGB").save(destination)


def write_json(path: str | Path, report: dict[str, Any]) -> None:
    destination = Path(path)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_junit(path: str | Path, results: list[ScenarioResult]) -> None:
    failures = sum(result.status != "passed" for result in results)
    suite = ET.Element(
        "testsuite",
        {
            "name": "opengl-system-test",
            "tests": str(len(results)),
            "failures": str(failures),
            "errors": "0",
        },
    )
    for result in results:
        case = ET.SubElement(
            suite,
            "testcase",
            {"classname": "graphics.workload", "name": result.name},
        )
        ET.SubElement(case, "properties")
        if result.status != "passed":
            failure = ET.SubElement(
                case, "failure", {"message": result.error or "validation failed"}
            )
            failure.text = result.error or (
                result.comparison.detail if result.comparison else "validation failed"
            )
        output = ET.SubElement(case, "system-out")
        output.text = json.dumps(result.to_dict(), sort_keys=True)
    tree = ET.ElementTree(suite)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def write_markdown(path: str | Path, report: dict[str, Any]) -> None:
    lines = [
        "# OpenGL System Test Result",
        "",
        f"- Status: **{report['status']}**",
        f"- Backend: `{report['backend']}`",
        f"- Renderer: `{report['capabilities'].get('renderer', 'unknown')}`",
        f"- OpenGL: `{report['capabilities'].get('version', 'unknown')}`",
        "",
        "| Scenario | Workload | Status | Median ms | p95 ms | Unique images |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for item in report["scenarios"]:
        lines.append(
            f"| {item['name']} | {item['workload']} | {item['status']} | "
            f"{item['median_ms']:.3f} | {item['p95_ms']:.3f} | "
            f"{len(set(item['image_hashes']))} |"
        )
    if report.get("invalid_shader_probe"):
        lines.extend(
            [
                "",
                "## Expected shader compilation failure",
                "",
                f"- Observed: `{report['invalid_shader_probe']['observed']}`",
                f"- Log excerpt: `{report['invalid_shader_probe']['log_excerpt']}`",
            ]
        )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
