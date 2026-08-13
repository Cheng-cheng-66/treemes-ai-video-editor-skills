#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(package_root: Path) -> dict[str, Any]:
    path = package_root / "manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("files"), list):
        raise ValueError("invalid update manifest")
    return payload


def safe_relative(value: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise ValueError(f"unsafe payload path: {value}")
    return Path(*pure.parts)


def verify_payload(package_root: Path, manifest: dict[str, Any]) -> list[Path]:
    payload_root = package_root / "payload"
    paths: list[Path] = []
    for item in manifest["files"]:
        if not isinstance(item, dict):
            raise ValueError("invalid file entry in manifest")
        relative = safe_relative(str(item.get("path", "")))
        source = payload_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"payload file missing: {relative}")
        expected = str(item.get("sha256", ""))
        actual = sha256(source)
        if actual != expected:
            raise ValueError(f"payload checksum mismatch: {relative}")
        paths.append(relative)
    return paths


def run_validation(project: Path) -> tuple[bool, list[dict[str, Any]]]:
    commands = [
        [sys.executable, "scripts/doctor.py", "--strict"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "scripts/smoke_test.py"],
    ]
    results: list[dict[str, Any]] = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=project,
            text=True,
            capture_output=True,
            check=False,
        )
        results.append(
            {
                "command": command,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        if completed.returncode != 0:
            return False, results
    return True, results


def restore(
    project: Path,
    backup_root: Path,
    existed: dict[Path, bool],
) -> None:
    for relative, was_present in existed.items():
        destination = project / relative
        backup = backup_root / relative
        if was_present:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, destination)
        elif destination.exists():
            destination.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply the video diary incremental update with backup and rollback"
    )
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    package_root = Path(__file__).resolve().parent
    project = args.project.expanduser().resolve()
    if not (project / "VERSION").is_file() or not (
        project / "scripts" / "doctor.py"
    ).is_file():
        print("FAIL: --project is not an installed auto-video-editor", file=sys.stderr)
        return 2

    manifest = load_manifest(package_root)
    paths = verify_payload(package_root, manifest)
    installed_version = (project / "VERSION").read_text(encoding="utf-8").strip()
    allowed = {str(item) for item in manifest.get("allowed_base_versions", [])}
    if installed_version not in allowed:
        print(
            f"FAIL: installed VERSION {installed_version!r} is not supported; "
            f"expected one of {sorted(allowed)}",
            file=sys.stderr,
        )
        return 3

    print(
        f"UPDATE PLAN: {installed_version} -> {manifest['update_id']} "
        f"({len(paths)} files)"
    )
    if args.dry_run:
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = project / "var" / "backups" / f"video-diary-{stamp}"
    existed: dict[Path, bool] = {}
    payload_root = package_root / "payload"
    for relative in paths:
        destination = project / relative
        was_present = destination.is_file()
        existed[relative] = was_present
        if was_present:
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(payload_root / relative, destination)

    passed, results = run_validation(project)
    receipt_dir = project / "var" / "update_history"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = receipt_dir / f"video-diary-{stamp}.json"
    status = "PASS" if passed else "FAIL_ROLLED_BACK"
    if not passed:
        restore(project, backup_root, existed)
    receipt.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "update_id": manifest["update_id"],
                "status": status,
                "backup": str(backup_root),
                "bgm_track": manifest["bgm_track"],
                "bgm_cache_packaged": False,
                "validation": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if not passed:
        print(f"FAIL: validation failed; files restored; see {receipt}", file=sys.stderr)
        return 4
    print(f"PASS: incremental update applied; receipt={receipt}")
    print(
        "NEXT: follow docs/VIDEO_DIARY_BGM_FLEET_SETUP.md once on this computer"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
