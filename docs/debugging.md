# Debugging guide

1. Run `opengl-system-test validate --config config/scenarios.json` before
   creating a context. Configuration errors use exit code 2.
2. Re-run with `--verbose` to record context creation, scenario boundaries,
   renderer identity, and exception traces.
3. Compare `images/*-actual.png` and `images/*-expected.png`. The JSON report
   records maximum and mean channel deltas plus the failed-pixel ratio.
4. Check image hashes across repetitions. More than one hash indicates output
   instability even when every image is inside the comparison tolerance.
5. Treat timing values as host-specific observations. Reproduce on the same
   driver, renderer, power mode, resolution, warm-up count, and workload before
   investigating a regression.
6. On Linux CI, set `LIBGL_ALWAYS_SOFTWARE=1`, use the `egl` backend, and inspect
   the reported renderer. Mesa llvmpipe is expected in the supplied workflow.
7. The invalid-shader probe must fail compilation and retain a non-empty driver
   log. An unexpected successful compile is a harness setup failure.

Exit codes are 0 for a passing run, 1 for completed validation with a failed
scenario, and 2 for configuration or context setup errors.
