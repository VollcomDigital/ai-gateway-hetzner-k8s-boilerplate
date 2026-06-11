#!/usr/bin/env python3
"""Local entrypoint — canonical module lives in bootstrap-governance/."""
from __future__ import annotations

import runpy
from pathlib import Path

TARGET = (
    Path(__file__).resolve().parents[1]
    / "k8s/apps/litellm/bootstrap-governance/bootstrap_litellm_governance.py"
)
runpy.run_path(str(TARGET), run_name="__main__")
