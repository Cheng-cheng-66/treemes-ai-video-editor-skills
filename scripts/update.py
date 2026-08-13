#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import load_config
from core.release import (
    append_history,
    channel_allows_version,
    git_output,
    inspect_git,
    resolve_commit,
)


def _run_validation(python: str) -> bool:
    doctor = subprocess.run(
        [python, "scripts/doctor.py", "--strict"],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if doctor.returncode != 0:
        return False
    tests = subprocess.run(
        [python, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if tests.returncode != 0:
        return False
    smoke = subprocess.run(
        [python, "scripts/smoke_test.py"],
        cwd=PROJECT_ROOT,
        check=False,
    )
    return smoke.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely install an explicit release")
    parser.add_argument("--target", required=True, help="semantic release tag")
    parser.add_argument("--channel", choices=("stable", "beta"))
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config()
    channel = args.channel or config.channel
    if not channel_allows_version(channel, args.target):
        print(
            f"FAIL: {args.target} is not allowed on the {channel} channel",
            file=sys.stderr,
        )
        return 2
    if args.fetch:
        fetched = subprocess.run(
            ["git", "fetch", "--tags", "origin"],
            cwd=PROJECT_ROOT,
            check=False,
        )
        if fetched.returncode != 0:
            return fetched.returncode

    before = inspect_git(PROJECT_ROOT)
    if not before.clean:
        print("FAIL: working tree must be clean before update", file=sys.stderr)
        return 3
    try:
        git_output(PROJECT_ROOT, "show-ref", "--verify", f"refs/tags/{args.target}")
        target_commit = resolve_commit(PROJECT_ROOT, args.target)
    except RuntimeError as exc:
        print(f"FAIL: target cannot be resolved: {exc}", file=sys.stderr)
        return 4
    if target_commit == before.commit:
        print(f"PASS: already running {args.target} ({target_commit[:12]})")
        return 0
    print(
        f"UPDATE PLAN: {before.commit[:12]} -> {args.target} "
        f"({target_commit[:12]}), channel={channel}"
    )
    if args.dry_run:
        return 0

    history_path = config.paths.data_root / "release_history.json"
    local_config = PROJECT_ROOT / "configs" / "local.json"
    backup: Path | None = None
    if local_config.exists():
        backup_dir = config.paths.data_root / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / (
            "local-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
        )
        shutil.copy2(local_config, backup)

    try:
        git_output(PROJECT_ROOT, "switch", "--detach", target_commit)
        if backup:
            shutil.copy2(backup, local_config)
        if not _run_validation(sys.executable):
            raise RuntimeError("doctor or regression tests failed")
    except Exception as exc:
        print(f"FAIL: update validation failed: {exc}", file=sys.stderr)
        git_output(PROJECT_ROOT, "switch", "--detach", before.commit)
        if backup:
            shutil.copy2(backup, local_config)
        append_history(
            history_path,
            {
                "action": "update_failed_restored",
                "from_commit": before.commit,
                "target": args.target,
                "target_commit": target_commit,
                "reason": str(exc),
            },
        )
        return 5

    append_history(
        history_path,
        {
            "action": "update",
            "channel": channel,
            "from_commit": before.commit,
            "from_branch": before.branch,
            "target": args.target,
            "target_commit": target_commit,
            "config_backup": str(backup) if backup else None,
        },
    )
    print(f"PASS: active release is now {args.target} ({target_commit[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
