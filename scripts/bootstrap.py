#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import create_runtime_dirs, load_config, write_local_config_template


def _venv_python(directory: Path) -> Path:
    return (
        directory / "Scripts" / "python.exe"
        if os.name == "nt"
        else directory / "bin" / "python"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the video editor")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--no-venv", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    if sys.version_info < (3, 11):
        print("FAIL: Python 3.11 or newer is required", file=sys.stderr)
        return 1

    environment = dict(os.environ)
    if args.config:
        environment["AI_VIDEO_EDITOR_CONFIG"] = str(args.config)
    config = load_config(environment=environment)
    created = create_runtime_dirs(config)
    local = write_local_config_template(config)
    print(f"PASS: runtime directories ready ({len(created)})")
    print(f"PASS: local config preserved/created at {local}")

    python = Path(sys.executable)
    if not args.no_venv:
        venv_dir = PROJECT_ROOT / ".venv"
        if not _venv_python(venv_dir).is_file():
            print(f"Creating virtual environment: {venv_dir}")
            venv.EnvBuilder(with_pip=True).create(venv_dir)
        python = _venv_python(venv_dir)

    requirements = PROJECT_ROOT / "requirements.lock"
    installable = [
        line
        for line in requirements.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if installable:
        completed = subprocess.run(
            [str(python), "-m", "pip", "install", "-r", str(requirements)],
            cwd=PROJECT_ROOT,
            check=False,
        )
        if completed.returncode != 0:
            print("FAIL: dependency installation failed", file=sys.stderr)
            return completed.returncode
    else:
        print("PASS: no third-party Python runtime dependencies")

    doctor = subprocess.run(
        [str(python), str(PROJECT_ROOT / "scripts" / "doctor.py"), "--config", str(local)],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if doctor.returncode != 0:
        return doctor.returncode
    if not args.skip_tests:
        tests = subprocess.run(
            [str(python), "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=PROJECT_ROOT,
            check=False,
        )
        if tests.returncode != 0:
            return tests.returncode
        smoke = subprocess.run(
            [str(python), str(PROJECT_ROOT / "scripts" / "smoke_test.py")],
            cwd=PROJECT_ROOT,
            check=False,
        )
        if smoke.returncode != 0:
            return smoke.returncode
        factory_smoke = subprocess.run(
            [
                str(python),
                str(PROJECT_ROOT / "scripts" / "smoke_test_factory_shoot.py"),
            ],
            cwd=PROJECT_ROOT,
            check=False,
        )
        if factory_smoke.returncode != 0:
            return factory_smoke.returncode
    print("PASS: bootstrap completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
