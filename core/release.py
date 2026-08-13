from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.process import run_command


_STABLE_VERSION = re.compile(r"^v\d+\.\d+\.\d+$")
_BETA_VERSION = re.compile(
    r"^v\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?$"
)


def channel_allows_version(channel: str, version: str) -> bool:
    if channel == "stable":
        return _STABLE_VERSION.fullmatch(version) is not None
    if channel == "beta":
        return _BETA_VERSION.fullmatch(version) is not None
    return False


@dataclass(frozen=True)
class GitState:
    commit: str
    branch: str
    clean: bool


def git_output(project_root: Path, *arguments: str) -> str:
    result = run_command(["git", *arguments], cwd=project_root, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def inspect_git(project_root: Path) -> GitState:
    commit = git_output(project_root, "rev-parse", "HEAD")
    branch = git_output(project_root, "branch", "--show-current") or "(detached)"
    status = git_output(project_root, "status", "--porcelain")
    return GitState(commit=commit, branch=branch, clean=not bool(status))


def resolve_commit(project_root: Path, reference: str) -> str:
    return git_output(project_root, "rev-parse", "--verify", f"{reference}^{{commit}}")


def read_history(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "events": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise ValueError(f"invalid release history: {path}")
    return payload


def append_history(path: Path, event: dict[str, Any]) -> None:
    payload = read_history(path)
    payload["events"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event,
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
