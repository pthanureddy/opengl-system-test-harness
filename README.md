# OpenGL System Test Harness

[![CI](https://github.com/pthanureddy/opengl-system-test-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/pthanureddy/opengl-system-test-harness/actions/workflows/ci.yml)

A Python harness that creates a headless OpenGL context, executes deterministic
shader workloads, compares framebuffer output with analytical references,
detects output instability, captures driver compiler diagnostics, and writes
JSON, JUnit, Markdown, and PNG evidence for CI review.

## What it validates

- OpenGL context creation and capability capture.
- Vertex/fragment shader compilation and framebuffer RGB readback.
- Solid-color output, nearest texture sampling, source-alpha blending, and
  depth ordering.
- Per-channel image differences and failed-pixel ratios.
- Repeatability through SHA-256 signatures across measured runs.
- Warm-up-separated median and p95 render/readback timings.
- Expected shader compilation failure with retained driver log text.
- Strict versioned JSON scenarios with duplicate-key and boundary validation.

The default suite contains four workloads with one warm-up and five measured
runs each. Timings are diagnostic observations, not cross-machine benchmarks.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
.\scripts\verify.ps1
```

Linux with a native or Mesa EGL implementation:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
OPENGL_BACKEND=egl ./scripts/verify.sh
```

Direct commands:

```bash
opengl-system-test validate --config config/scenarios.json
opengl-system-test run --config config/scenarios.json --output artifacts/local --backend auto
```

The run exits 0 when every scenario passes, 1 for completed validation with a
failed scenario, and 2 for invalid configuration or context setup.

## Output

```text
artifacts/local/
  report.json
  report.junit.xml
  summary.md
  images/
    *-actual.png
    *-expected.png
```

The JSON report records the OpenGL vendor, renderer and version, scenario
comparison metrics, timing samples, image hashes, and the expected invalid
shader diagnostic. JUnit integrates with CI test views; PNG pairs support
manual failure analysis.

## CI

GitHub Actions runs lint and portable tests on Python 3.11/3.12 for Windows and
Linux, then runs the complete graphics suite and coverage gate on Linux using
Mesa software rendering through EGL. The hosted Windows image does not expose a
usable OpenGL 3.3 WGL context, so Windows graphics execution is verified on a
local GPU rather than misrepresented as a hosted run. The workflow uploads
Linux reports, PNGs and coverage plus the built package.

The repository also contains a GitLab CI definition that executes the same
headless EGL path and publishes JUnit, Cobertura coverage, images and packages.
It is included as a reviewable pipeline definition; no hosted GitLab execution
is claimed.

## Repository map

```text
src/opengl_system_test/  configuration, rendering, comparison, runner, reports
config/                   default workload scenarios
tests/                    unit, graphics integration, reporting and CLI tests
docs/                     architecture, requirements, debugging and boundaries
scripts/                  PowerShell and Bash verification entry points
.github/workflows/        Windows/Linux GitHub Actions pipeline
.gitlab-ci.yml             reviewable GitLab CI pipeline
```

## Documentation

- [Requirements and verification](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Debugging guide](docs/debugging.md)
- [Evidence boundary](docs/evidence-boundary.md)

## Evidence boundary

This harness executes real OpenGL 3.3 workloads through the host implementation.
It does not test Arm Mali, Vulkan, OpenGL ES or DirectX; it does not claim
Khronos/Microsoft certification, driver conformance, hardware performance or
game compatibility. See the [full boundary](docs/evidence-boundary.md).

## License

MIT
