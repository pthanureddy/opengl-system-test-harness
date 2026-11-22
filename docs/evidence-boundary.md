# Evidence boundary

This repository is a self-contained portfolio system-test harness. It executes
real OpenGL 3.3 shader programs and framebuffer operations through ModernGL and
the host graphics implementation. It provides reproducible software-rendered
Linux CI and local Windows execution.

It does not test Arm Mali hardware or drivers. It does not implement or claim
Vulkan, OpenGL ES, DirectX, Khronos conformance, Microsoft certification,
driver certification, physical-device testing, production GPU performance, or
game compatibility. Mesa llvmpipe CI confirms software-stack behavior, not
hardware performance. Timings are diagnostic observations and are not presented
as portable benchmarks.

The GitLab pipeline file is an executable CI definition included for review. It
is not evidence of a hosted GitLab run unless a real GitLab job URL is supplied.
