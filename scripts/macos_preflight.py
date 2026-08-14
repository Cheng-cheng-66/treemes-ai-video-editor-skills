#!/usr/bin/env python3
from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


JIANING_APP_PATHS = (
    Path("/Applications/VideoFusion-macOS.app"),
    Path("/Applications/JianyingPro.app"),
)


def missing_commands() -> list[str]:
    return [
        command
        for command in ("ffmpeg", "ffprobe", "node")
        if shutil.which(command) is None
    ]


def install_missing_with_homebrew(missing: list[str]) -> None:
    if not missing:
        return
    brew = shutil.which("brew")
    if brew is None:
        raise RuntimeError(
            "缺少 "
            + ", ".join(missing)
            + "，并且没有检测到 Homebrew。安装已停止；不能在缺少媒体依赖时继续。"
        )
    packages = []
    if "ffmpeg" in missing or "ffprobe" in missing:
        packages.append("ffmpeg")
    if "node" in missing:
        packages.append("node")
    for package in packages:
        completed = subprocess.run(
            [brew, "install", package],
            text=True,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(f"Homebrew 安装 {package} 失败")


def find_jianying() -> Path | None:
    return next((path for path in JIANING_APP_PATHS if path.is_dir()), None)


def verify(*, install_missing: bool, require_jianying: bool) -> list[str]:
    if platform.system() != "Darwin":
        raise RuntimeError("macOS dependency preflight can only run on macOS")
    if sys.version_info < (3, 11):
        raise RuntimeError(
            f"需要 Python 3.11+，当前为 {platform.python_version()}"
        )
    missing = missing_commands()
    if missing and install_missing:
        install_missing_with_homebrew(missing)
        missing = missing_commands()
    if missing:
        raise RuntimeError(
            "缺少必需命令：" + ", ".join(missing) + "。完整工作流已停止。"
        )
    if require_jianying and find_jianying() is None:
        raise RuntimeError(
            "未检测到剪映专业版。完整工作流已停止；安装并登录剪映后再重试。"
        )
    return ["python3", "ffmpeg", "ffprobe", "node"] + (
        ["jianying"] if require_jianying else []
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify macOS video workflow dependencies")
    parser.add_argument("--install-missing", action="store_true")
    parser.add_argument("--require-jianying", action="store_true")
    args = parser.parse_args()
    try:
        ready = verify(
            install_missing=args.install_missing,
            require_jianying=args.require_jianying,
        )
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: complete workflow dependencies ready: " + ", ".join(ready))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
