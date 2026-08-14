#!/usr/bin/env python3
"""Build the public, double-click-installable macOS Skill ZIP."""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = "ai-video-editing-skills"
REQUIRED = (
    "SKILL.md",
    "VERSION",
    "agents/openai.yaml",
    "core/config.py",
    "presets/video_diary/cover.yaml",
    "scripts/doctor.py",
    "scripts/macos_preflight.py",
    "scripts/run_factory_shoot.py",
    "安装.command",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tracked_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    files = []
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        relative = Path(os.fsdecode(raw))
        path = ROOT / relative
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def add_file(archive: zipfile.ZipFile, source: Path) -> None:
    relative = source.relative_to(ROOT).as_posix()
    arcname = f"{TOP_LEVEL}/{relative}"
    info = zipfile.ZipInfo(arcname, date_time=(2026, 8, 14, 0, 0, 0))
    info.create_system = 3
    mode = stat.S_IMODE(source.stat().st_mode)
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, source.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs/github_release",
    )
    args = parser.parse_args()

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            raise SystemExit(f"FAIL: missing package entry: {relative}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = (
        args.output_dir / f"AI-Video-Editing-Skill-macOS-v{version}.zip"
    )
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    files = tracked_files()
    with zipfile.ZipFile(archive_path, "w") as archive:
        for path in files:
            add_file(archive, path)

    digest = sha256(archive_path)
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")
    print(f"PASS: built {archive_path}")
    print(f"PASS: SHA-256 {digest}")
    print(f"PASS: packaged {len(files)} tracked files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
