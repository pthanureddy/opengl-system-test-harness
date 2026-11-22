# Requirements and verification

| ID | Requirement | Verification |
| --- | --- | --- |
| GFX-001 | Create a headless OpenGL 3.3 or newer context and record renderer capabilities. | Graphics context test and every harness run. |
| GFX-002 | Compile and execute vertex and fragment shaders without a window system. | Texture, blend and depth workloads plus graphics integration tests. |
| GFX-003 | Validate nearest texture sampling against an analytical reference image. | Texture-quadrant workload with zero channel tolerance. |
| GFX-004 | Validate source-alpha blending against an analytical RGB reference. | Alpha-blend workload with one-channel rounding tolerance. |
| GFX-005 | Detect incorrect depth ordering in overlapping geometry. | Depth-overlap workload draws near geometry first and far geometry second. |
| GFX-006 | Repeat each workload and detect non-deterministic image output. | SHA-256 image signatures and configurable unique-image limit. |
| GFX-007 | Record warm-up-separated render/readback timings without presenting them as a cross-machine benchmark. | Median and nearest-rank p95 timing fields in JSON and Markdown. |
| GFX-008 | Capture an expected shader compiler failure as diagnostic evidence. | Invalid shader probe and non-empty compiler log check. |
| GFX-009 | Produce machine-readable JSON and JUnit plus reviewable PNG and Markdown evidence. | Reporting tests and system-runner test. |
| GFX-010 | Reject malformed, ambiguous, duplicate, or out-of-bound scenario configuration. | Configuration unit tests. |

The default run uses four workloads, five measured repetitions per workload,
and one warm-up repetition. Hosted Linux CI executes the graphics suite with
Mesa software rendering through EGL. Hosted Windows executes the portable
configuration, analysis, reporting and CLI tests because the standard runner
does not expose a usable OpenGL 3.3 WGL context. A local Windows GPU run remains
the Windows graphics verification path.
