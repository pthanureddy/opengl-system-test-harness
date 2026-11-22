$ErrorActionPreference = 'Stop'
python -m ruff check .
python -m pytest --cov=opengl_system_test --cov-report=term-missing --cov-fail-under=85
python -m build
opengl-system-test validate --config config/scenarios.json
opengl-system-test run --config config/scenarios.json --output artifacts/local --backend auto
