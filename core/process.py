from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def executable_path(command: str) -> Path | None:
    resolved = shutil.which(command)
    return Path(resolved).resolve() if resolved else None


def run_command(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
    timeout: float | None = None,
) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        env=None if environment is None else dict(environment),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return CommandResult(
        command=tuple(str(part) for part in command),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def first_version_line(command: str, *args: str) -> str | None:
    if executable_path(command) is None:
        return None
    result = run_command([command, *args], timeout=10)
    output = (result.stdout or result.stderr).strip()
    return output.splitlines()[0] if result.returncode == 0 and output else None
