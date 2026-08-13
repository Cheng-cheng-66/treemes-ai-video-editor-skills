#!/usr/bin/env python3
"""Build a media-free, credential-free migration bundle for the video editor."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "migration"
PACKAGE_ID = "ai-video-editor-full-migration-20260728"

TOP_LEVEL_FILES = {
    ".env.example",
    ".gitignore",
    "CHANGELOG.md",
    "CURRENT_STATUS.md",
    "README.md",
    "SKILL.md",
    "LICENSE_STATUS.md",
    "VERSION",
    "requirements.lock",
}

TREE_RULES = {
    "acceptance": {".md", ".json", ".txt"},
    "core": {".py"},
    "docs": {".md", ".json", ".yaml", ".yml", ".txt"},
    "presets": {".md", ".json", ".yaml", ".yml", ".txt"},
    "research": {".md", ".json", ".yaml", ".yml", ".txt"},
    "scripts": {".py", ".sh", ".ps1"},
    "skills": {".py", ".js", ".json", ".md", ".yaml", ".yml"},
    "tests": {".py", ".json", ".md", ".txt"},
}

SELECTIVE_RULES = {
    "references/factory_demo": {".json", ".yaml", ".yml", ".txt", ".md"},
    "templates/factory_demo_hybrid": {".json", ".yaml", ".yml", ".txt", ".md"},
}

EXCLUDED_NAMES = {
    ".DS_Store",
    "configs/local.json",
}

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "media_slots",
    "reports",
}

FORBIDDEN_SUFFIXES = {
    ".mov",
    ".mp4",
    ".m4a",
    ".mp3",
    ".wav",
    ".aac",
    ".flac",
    ".avi",
    ".mkv",
    ".db",
    ".sqlite",
    ".pem",
    ".key",
    ".p12",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_text(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip()


def eligible(path: Path, suffixes: set[str]) -> bool:
    relative = path.relative_to(PROJECT_ROOT)
    relative_text = relative.as_posix()
    if relative_text in EXCLUDED_NAMES:
        return False
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return False
    return path.is_file() and path.suffix.lower() in suffixes


def collect_files() -> list[Path]:
    selected: set[Path] = set()
    for value in TOP_LEVEL_FILES:
        path = PROJECT_ROOT / value
        if not path.is_file():
            raise FileNotFoundError(path)
        selected.add(path)

    default_config = PROJECT_ROOT / "configs/default.json"
    if not default_config.is_file():
        raise FileNotFoundError(default_config)
    selected.add(default_config)

    for relative_root, suffixes in TREE_RULES.items():
        root = PROJECT_ROOT / relative_root
        if not root.is_dir():
            raise FileNotFoundError(root)
        for path in root.rglob("*"):
            if eligible(path, suffixes):
                selected.add(path)

    for relative_root, suffixes in SELECTIVE_RULES.items():
        root = PROJECT_ROOT / relative_root
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if eligible(path, suffixes):
                selected.add(path)

    return sorted(selected, key=lambda item: item.relative_to(PROJECT_ROOT).as_posix())


def write_readme(package_root: Path, config: dict) -> None:
    bgm = config["video_diary"]["bgm"]
    audio = config["video_diary"]["jianying_audio"]
    (package_root / "MIGRATION_README.md").write_text(
        f"""# AI视频剪辑数字员工：完整移植包

## 包身份

- 快照日期：2026-07-28
- 基础版本：{(PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()}
- 正式 stable Release：尚未创建
- 生产可用主流程：video_diary
- factory_shoot：包含 disabled manifest、预设和说明；不包含客户特定原型或生产入口

## 新 Mac 部署

1. 安装 Homebrew、Python 3.11+、Node.js、FFmpeg 和剪映专业版 7.9.0。
2. 解压本 ZIP，不要覆盖正在运行的旧项目。
3. 在终端进入解压后的目录。
4. 执行：

```bash
brew install python node ffmpeg
chmod +x DEPLOY_MACOS.sh scripts/install_macos.sh
./DEPLOY_MACOS.sh
```

部署脚本会建立本机 `.venv`、创建 `var/` 运行目录、运行全部可迁移自动测试、
严格环境检查和合成技术样片。只有所有命令返回 PASS 才进入素材测试。

## 视频日记固定剪映规格

- 人声分离：开启；
- 分离模式：仅保留人声；
- 人声音量：{audio["voice_volume_db"]:+.1f}dB；
- BGM：{bgm["name"]}；
- 剪映素材 ID：{bgm["material_id"]}；
- BGM 音量：{bgm["jianying_initial_volume_db"]:.1f}dB；
- 淡入、淡出：各 {bgm["fade_in_seconds"]:.1f} 秒。

剪映BGM缓存、账号和会员权益不在包内。目标电脑必须登录有权益的账号，
在剪映中重新下载同一素材并核对素材ID。

## 包内包含

- 核心程序、配置、预设、Skills、安装脚本和自动测试；
- 视频日记完整默认规则；
- 工厂实拍与混合路线的预设、ADR和disabled边界；
- 迁移清单、逐文件SHA256和本地验证脚本。

## 明确不包含

- 原素材、客户视频、成片、音频、BGM缓存和剪映草稿；
- 浏览器登录态、剪映账号、会员凭证、密钥、Cookie和 `configs/local.json`；
- `.git`、本机 `.venv`、`var/`、`runs/`、`outputs/`、大体积实验目录；
- 工厂实拍实验用的本机证据视频。缺少这些证据时，相关回归测试会明确
  `SKIP`，不会伪装成 PASS。

## 迁移后的真实验收

自动部署通过不等于新电脑正式生产通过。还必须：

1. 在新电脑登录剪映并绑定固定BGM；
2. 提供一条真实视频日记素材，完整跑通并人工听审；
3. 如启用工厂实拍，再提供真实原素材并重建四轨资产；
4. 人声、字幕、专业词、口型、BGM和连续性人工审核通过后，再启用生产。
""",
        encoding="utf-8",
    )


def write_deployer(package_root: Path) -> None:
    path = package_root / "DEPLOY_MACOS.sh"
    path.write_text(
        """#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT"

python3 verify_migration.py
./scripts/install_macos.sh
./.venv/bin/python scripts/doctor.py --strict
./.venv/bin/python scripts/smoke_test.py

echo "PASS: migration package deployed and verified"
echo "NEXT: bind Jianying 7.9.0 and run one real-source shadow test"
""",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_verifier(package_root: Path) -> None:
    (package_root / "verify_migration.py").write_text(
        """#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MIGRATION_MANIFEST.json"
FORBIDDEN_SUFFIXES = {
    ".mov", ".mp4", ".m4a", ".mp3", ".wav", ".aac", ".flac",
    ".avi", ".mkv", ".db", ".sqlite", ".pem", ".key", ".p12",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = []
    for row in payload["files"]:
        path = ROOT / row["path"]
        if not path.is_file():
            errors.append(f"missing: {row['path']}")
            continue
        if path.stat().st_size != row["size"]:
            errors.append(f"size mismatch: {row['path']}")
        if sha256(path) != row["sha256"]:
            errors.append(f"sha256 mismatch: {row['path']}")

    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden media/secret-like file: {path.relative_to(ROOT)}")
        if path.name == "local.json" or (
            path.name.startswith(".env") and path.name != ".env.example"
        ):
            errors.append(f"forbidden local config: {path.relative_to(ROOT)}")

    if errors:
        for value in errors:
            print(f"FAIL: {value}")
        return 1
    print(f"PASS: {len(payload['files'])} files match manifest")
    print("PASS: no raw media, rendered media, credentials or local config found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""",
        encoding="utf-8",
    )


def main_for_output(
    output_root: Path,
    local_isolated_deployment: str = "NOT_RUN_FOR_THIS_ARCHIVE",
) -> int:
    output_root = output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    config = json.loads(
        (PROJECT_ROOT / "configs/default.json").read_text(encoding="utf-8")
    )
    selected = collect_files()
    archive = output_root / f"{PACKAGE_ID}.zip"
    checksum = output_root / f"{archive.name}.sha256"

    with tempfile.TemporaryDirectory(prefix=f"{PACKAGE_ID}-") as temp:
        package_root = Path(temp) / PACKAGE_ID
        package_root.mkdir()

        for source in selected:
            relative = source.relative_to(PROJECT_ROOT)
            destination = package_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        write_readme(package_root, config)
        write_deployer(package_root)
        write_verifier(package_root)

        generated = [
            package_root / "MIGRATION_README.md",
            package_root / "DEPLOY_MACOS.sh",
            package_root / "verify_migration.py",
        ]
        all_files = sorted(
            [package_root / path.relative_to(PROJECT_ROOT) for path in selected]
            + generated,
            key=lambda item: item.relative_to(package_root).as_posix(),
        )
        entries = [
            {
                "path": path.relative_to(package_root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in all_files
        ]
        manifest = {
            "schema_version": 1,
            "package_id": PACKAGE_ID,
            "created_at": datetime.now().astimezone().isoformat(),
            "source": {
                "project_root_redacted": PROJECT_ROOT.name,
                "git_head": git_text("rev-parse", "HEAD"),
                "git_branch": git_text("branch", "--show-current"),
                "working_tree_dirty": bool(git_text("status", "--porcelain")),
                "dirty_paths": git_text("status", "--porcelain").splitlines(),
            },
            "capabilities": {
                "video_diary": "DEPLOYABLE_PENDING_NEW_MACHINE_REAL_SOURCE_REVIEW",
                "factory_shoot": "PLANNED_DISABLED_PRESETS_AND_RULES_ONLY",
            },
            "video_diary_audio": {
                "voice_separation_enabled": audio_value(
                    config, "voice_separation_enabled"
                ),
                "voice_separation_mode": audio_value(
                    config, "voice_separation_mode"
                ),
                "voice_volume_db": audio_value(config, "voice_volume_db"),
                "bgm_material_id": config["video_diary"]["bgm"]["material_id"],
                "bgm_volume_db": config["video_diary"]["bgm"][
                    "jianying_initial_volume_db"
                ],
            },
            "exclusions": [
                "raw_media",
                "rendered_media",
                "jianying_drafts",
                "licensed_bgm_cache",
                "credentials_and_login_state",
                "configs/local.json",
                ".git",
                ".venv",
                "var",
                "runs",
                "outputs",
                "experiments",
            ],
            "fresh_machine_acceptance": "NOT_REVIEWED",
            "local_isolated_deployment": local_isolated_deployment,
            "files": entries,
        }
        (package_root / "MIGRATION_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with zipfile.ZipFile(
            archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as bundle:
            for path in sorted(package_root.rglob("*")):
                if path.is_file():
                    arcname = Path(PACKAGE_ID) / path.relative_to(package_root)
                    info = zipfile.ZipInfo.from_file(path, arcname.as_posix())
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = (path.stat().st_mode & 0xFFFF) << 16
                    with path.open("rb") as handle:
                        bundle.writestr(info, handle.read())

    checksum.write_text(
        f"{sha256(archive)}  {archive.name}\n",
        encoding="utf-8",
    )
    print(archive)
    print(checksum)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--local-isolated-deployment",
        default="NOT_RUN_FOR_THIS_ARCHIVE",
        choices={
            "NOT_RUN_FOR_THIS_ARCHIVE",
            "PASS_ON_SOURCE_MACHINE_2026-07-28",
        },
    )
    args = parser.parse_args()
    return main_for_output(args.output_root, args.local_isolated_deployment)


def audio_value(config: dict, key: str):
    return config["video_diary"]["jianying_audio"][key]


if __name__ == "__main__":
    raise SystemExit(main())
