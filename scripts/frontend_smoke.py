"""Repeatable frontend smoke checks for Task 117.

Steps:
  1. Compile check: frontend/ and app/ via subprocess.
  2. Import check: key frontend modules via subprocess (avoids st contamination).
  3. Constants integrity: METRIC_SPECS, MODEL_LABELS, REVIEW_SECTIONS, PER_MODEL_REVIEW_SECTIONS.
  4. Manual check summary: URLs that require Streamlit running.

Run: uv run python scripts/frontend_smoke.py
Expected final line: frontend smoke ok
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# frontend/ is not in the editable install (pyproject.toml includes only app*).
# Add the project root so _check_constants can import frontend.constants directly.
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def main() -> None:
    _check_compile()
    _check_imports()
    _check_constants()
    _print_manual_checks()
    print("frontend smoke ok")


def _check_compile() -> None:
    env = {**os.environ, "PYTHONPYCACHEPREFIX": "/tmp/allocadabra-pycache-main"}
    result = subprocess.run(
        [sys.executable, "-m", "compileall", "frontend", "app"],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print("ERROR: compile check failed for frontend/ and app/", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)


def _check_imports() -> None:
    modules = (
        "frontend.app, frontend.chat, frontend.review, "
        "frontend.configuration, frontend.data, frontend.runtime, "
        "frontend.modelling, frontend.theme, frontend.constants, "
        "frontend.dev_tools"
    )
    result = subprocess.run(
        [sys.executable, "-c", f"import {modules}; print('frontend imports ok')"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or "frontend imports ok" not in result.stdout:
        print("ERROR: frontend import check failed", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)


def _check_constants() -> None:
    # frontend.constants has no st calls at module level — safe to import directly.
    from frontend.constants import (
        METRIC_SPECS,
        MODEL_LABELS,
        PER_MODEL_REVIEW_SECTIONS,
        REVIEW_SECTIONS,
    )

    assert len(METRIC_SPECS) > 0, "METRIC_SPECS must be non-empty"

    for key in ("mean_variance", "risk_parity", "hierarchical_risk_parity"):
        assert key in MODEL_LABELS, f"MODEL_LABELS missing key: {key}"

    assert len(REVIEW_SECTIONS) > 0, "REVIEW_SECTIONS must be non-empty"
    assert len(PER_MODEL_REVIEW_SECTIONS) > 0, "PER_MODEL_REVIEW_SECTIONS must be non-empty"


def _print_manual_checks() -> None:
    print(
        "\nMANUAL CHECKS REQUIRED (need Streamlit running):\n"
        "  http://localhost:8501/?alloca_dev_no_ai_env=1"
        "           — missing-key Configuration error\n"
        "  http://localhost:8501/?alloca_dev_review_fixture=brief3"
        " — synthetic Review fixture\n"
        "  http://localhost:8501/?alloca_dev_review_fixture=brief3"
        "&alloca_dev_no_ai_env=1 — fixture + missing-key\n"
    )


if __name__ == "__main__":
    main()
