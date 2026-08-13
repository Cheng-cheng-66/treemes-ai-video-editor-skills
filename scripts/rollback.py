#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import load_config
from core.release import append_history, git_output, inspect_git, read_history


def _successful_updates(events: list[dict]) -> list[dict]:
    return [event for event in events if event.get("action") == "update"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Rollback the production release")
    parser.add_argument("--list", action="store_true", dest="list_only")
    parser.add_argument("--reason")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config()
    history_path = config.paths.data_root / "release_history.json"
    history = read_history(history_path)
    updates = _successful_updates(history["events"])
    if args.list_only:
        if not updates:
            print("No recorded rollback targets.")
            return 0
        for index, event in enumerate(reversed(updates), start=1):
            print(
                f"{index}. {event['from_commit']} "
                f"(before {event.get('target', 'unknown')})"
            )
        return 0
    if not args.reason:
        print("FAIL: --reason is required for rollback", file=sys.stderr)
        return 2
    if not updates:
        print("FAIL: no recorded stable version is available", file=sys.stderr)
        return 3
    state = inspect_git(PROJECT_ROOT)
    if not state.clean:
        print("FAIL: working tree must be clean before rollback", file=sys.stderr)
        return 4
    target = str(updates[-1]["from_commit"])
    print(f"ROLLBACK PLAN: {state.commit[:12]} -> {target[:12]}")
    if args.dry_run:
        return 0

    try:
        git_output(PROJECT_ROOT, "switch", "--detach", target)
        validation = subprocess.run(
            [sys.executable, "scripts/doctor.py", "--strict"],
            cwd=PROJECT_ROOT,
            check=False,
        )
        if validation.returncode != 0:
            raise RuntimeError("doctor failed after rollback")
    except Exception as exc:
        git_output(PROJECT_ROOT, "switch", "--detach", state.commit)
        print(f"FAIL: rollback restored current release: {exc}", file=sys.stderr)
        return 5

    append_history(
        history_path,
        {
            "action": "rollback",
            "from_commit": state.commit,
            "target_commit": target,
            "reason": args.reason,
        },
    )
    print(f"PASS: rolled back to {target[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
