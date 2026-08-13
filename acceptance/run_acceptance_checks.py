#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "acceptance" / "reports"
VENV_PYTHON = (
    PROJECT_ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
)


def run(command: list[str]) -> dict[str, object]:
    started_at = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": command,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def write_log(check_id: str, result: dict[str, object]) -> None:
    command = " ".join(str(part) for part in result["command"])
    content = [
        f"check_id={check_id}",
        f"started_at={result['started_at']}",
        f"finished_at={result['finished_at']}",
        f"exit_code={result['exit_code']}",
        f"command={command}",
        "",
        "[stdout]",
        str(result["stdout"]),
        "[stderr]",
        str(result["stderr"]),
    ]
    (REPORTS_DIR / f"{check_id}.log").write_text(
        "\n".join(content).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> int:
    system_python = sys.executable
    results: dict[str, dict[str, object]] = {}

    # These two checks must run before tracked reports make the worktree dirty.
    results["update_dry_run"] = run(
        [
            system_python,
            "scripts/update.py",
            "--target",
            "v0.9.0-beta.1",
            "--channel",
            "beta",
            "--dry-run",
        ]
    )
    results["rollback_list"] = run(
        [system_python, "scripts/rollback.py", "--list"]
    )
    results["bootstrap"] = run([system_python, "scripts/bootstrap.py"])

    active_python = str(VENV_PYTHON if VENV_PYTHON.is_file() else Path(system_python))
    results["doctor_strict"] = run(
        [active_python, "scripts/doctor.py", "--strict"]
    )
    results["automatic_tests_12"] = run(
        [
            active_python,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ]
    )
    results["synthetic_smoke"] = run(
        [active_python, "scripts/smoke_test.py"]
    )
    results["existing_baseline_regression"] = run(
        [active_python, "scripts/regression.py"]
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    for check_id, result in results.items():
        write_log(check_id, result)

    source_value = os.environ.get("VIDEO_DIARY_STANDARD_SOURCE", "").strip()
    source = Path(source_value).expanduser() if source_value else None
    source_status = (
        "AVAILABLE"
        if source is not None and source.is_file()
        else "BLOCKED_NOT_CONFIGURED"
        if source is None
        else "BLOCKED_NOT_AVAILABLE"
    )
    (REPORTS_DIR / "standard_real_regression.log").write_text(
        "\n".join(
            [
                "check_id=standard_real_regression",
                f"checked_at={datetime.now(timezone.utc).isoformat()}",
                f"source={'configured externally' if source else 'not configured'}",
                f"status={source_status}",
                (
                    "result=NOT_RUN; source media is not configured or available"
                    if source_status != "AVAILABLE"
                    else "result=AVAILABLE; run the separately approved real regression procedure"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "branch": subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip(),
        "commit": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip(),
        "checks": {
            check_id: {
                "exit_code": result["exit_code"],
                "log": f"acceptance/reports/{check_id}.log",
            }
            for check_id, result in results.items()
        },
        "standard_real_regression": {
            "status": source_status,
            "log": "acceptance/reports/standard_real_regression.log",
        },
    }
    (REPORTS_DIR / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    required_zero = [
        "update_dry_run",
        "rollback_list",
        "bootstrap",
        "doctor_strict",
        "automatic_tests_12",
        "synthetic_smoke",
    ]
    failed = [
        check_id
        for check_id in required_zero
        if int(results[check_id]["exit_code"]) != 0
    ]
    for check_id, result in results.items():
        print(f"{check_id}: exit={result['exit_code']}")
    print(f"standard_real_regression: {source_status}")
    if failed:
        print(f"FAIL: required checks failed: {', '.join(failed)}")
        return 1
    print("PASS: executable technical checks completed; release gates remain separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
