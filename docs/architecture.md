# Architecture

```text
scenarios.json
      |
      v
strict configuration loader
      |
      v
headless OpenGL context ----> capability record
      |
      +---- shader compile diagnostic
      |
      +---- solid color
      +---- texture sampling
      +---- alpha blending
      `---- depth ordering
               |
               v
      framebuffer RGB readback
               |
      analytical reference comparison
               |
      SHA-256 stability + timings
               |
      JSON + JUnit + Markdown + PNG
```

`GraphicsSession` owns the context and resource lifetime. Each workload creates
its programs, buffers, textures, and framebuffer, finishes queued commands,
reads RGB bytes, and releases resources. Analytical expected images avoid
machine-specific golden files. The depth test deliberately renders the near
triangle before the far triangle so a missing depth test produces visible red
leakage.

The runner separates warm-up and measured iterations, keeps processing after a
single scenario error, and reports functional comparison, output stability, and
timing observations independently. Performance thresholds are optional because
hosted runners are unsuitable for universal GPU performance gates.
