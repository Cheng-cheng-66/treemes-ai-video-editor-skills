#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.skills import discover_skills


def command_version(command: str, *arguments: str) -> dict[str, Any]:
    path = shutil.which(command)
    if path is None:
        return {"status": "FAIL", "path": None, "version": None}
    completed = subprocess.run(
        [path, *arguments],
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "path": str(Path(path).resolve()),
        "version": output[0] if output else None,
    }


def python_module(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:
        return {"status": "FAIL", "error": str(exc)}
    return {
        "status": "PASS",
        "version": getattr(imported, "__version__", None),
    }


def model_check(path: Path, minimum_bytes: int) -> dict[str, Any]:
    return {
        "status": (
            "PASS"
            if path.is_file() and path.stat().st_size >= minimum_bytes
            else "BLOCKED"
        ),
        "path": str(path),
        "size_bytes": path.stat().st_size if path.is_file() else None,
    }


def build_report() -> dict[str, Any]:
    skills = discover_skills(ROOT)
    case_skill = skills.get("case_study")
    checks = {
        "ffmpeg": command_version("ffmpeg", "-version"),
        "ffprobe": command_version("ffprobe", "-version"),
        "whisper_cli": command_version("whisper-cli", "--help"),
        "python_cv2": python_module("cv2"),
        "python_numpy": python_module("numpy"),
        "python_scipy": python_module("scipy"),
        "python_pillow": python_module("PIL"),
        "whisper_model": model_check(
            ROOT / "var/models/ggml-small-q5_1.bin",
            100_000_000,
        ),
        "face_model": model_check(
            ROOT / "var/models/face_detection_yunet_2026may.onnx",
            200_000,
        ),
        "case_study_skill": {
            "status": (
                "PASS"
                if case_skill
                and case_skill.enabled
                and case_skill.entrypoint
                else "FAIL"
            ),
            "enabled": case_skill.enabled if case_skill else None,
            "entrypoint": case_skill.entrypoint if case_skill else None,
            "skill_status": case_skill.status if case_skill else None,
        },
    }
    statuses = [check["status"] for check in checks.values()]
    overall = (
        "FAIL"
        if "FAIL" in statuses
        else "BLOCKED"
        if "BLOCKED" in statuses
        else "PASS"
    )
    return {
        "schema_version": 1,
        "status": overall,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report()
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered if args.json else f"{report['status']}: case_study doctor")
    return 0 if report["status"] == "PASS" else 2 if report["status"] == "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
