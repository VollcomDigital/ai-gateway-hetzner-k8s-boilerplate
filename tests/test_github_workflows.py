"""Validate GitHub Actions workflow security conventions."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
USES_PATTERN = re.compile(r"^\s*uses:\s+(\S+)", re.MULTILINE)


def _collect_action_refs() -> list[tuple[str, str, str]]:
    refs: list[tuple[str, str, str]] = []
    for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
        content = workflow.read_text(encoding="utf-8")
        for match in USES_PATTERN.finditer(content):
            action_ref = match.group(1)
            action, _, ref = action_ref.partition("@")
            refs.append((workflow.name, action, ref))
    return refs


@pytest.mark.parametrize(
    ("workflow_name", "action", "ref"),
    _collect_action_refs(),
    ids=lambda value: value if isinstance(value, str) else "/".join(value),
)
def test_workflow_actions_pinned_to_commit(
    workflow_name: str,
    action: str,
    ref: str,
) -> None:
    pin = ref.split("#", 1)[0]
    assert COMMIT_SHA.match(pin), (
        f"{workflow_name}: {action}@{ref} must use a full commit SHA, not a mutable tag"
    )
