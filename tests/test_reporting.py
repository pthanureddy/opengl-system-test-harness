import json
import xml.etree.ElementTree as ET

from opengl_system_test.models import Comparison, ScenarioResult
from opengl_system_test.reporting import write_json, write_junit, write_markdown


def _result(status="passed"):
    return ScenarioResult(
        name="solid",
        workload="solid_color",
        status=status,
        image_hashes=["abc"],
        timings_ms=[1.0],
        median_ms=1.0,
        p95_ms=1.0,
        comparison=Comparison(True, 0, 0.0, 0, 0.0, "ok"),
    )


def test_writes_parseable_junit(tmp_path):
    path = tmp_path / "result.xml"
    write_junit(path, [_result()])
    root = ET.parse(path).getroot()
    assert root.attrib["tests"] == "1"
    assert root.attrib["failures"] == "0"


def test_failed_result_maps_to_failure(tmp_path):
    path = tmp_path / "result.xml"
    result = _result("failed")
    result.error = "image mismatch"
    write_junit(path, [result])
    assert ET.parse(path).find(".//failure").attrib["message"] == "image mismatch"


def test_writes_json_and_markdown(tmp_path):
    result = _result()
    report = {
        "status": "passed",
        "backend": "auto",
        "capabilities": {"renderer": "test", "version": "3.3"},
        "invalid_shader_probe": None,
        "scenarios": [result.to_dict()],
    }
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "summary.md"
    write_json(json_path, report)
    write_markdown(markdown_path, report)
    assert json.loads(json_path.read_text())["status"] == "passed"
    assert "| solid |" in markdown_path.read_text()
