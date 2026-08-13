#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

from build_video_diary_update_package import FILES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "d5085e01834390f218591daebf9f84ee9cca7657"
BASE_VERSION = "0.9.0-beta.1"
PACKAGE_NAME = "video-diary-fresh-install-0.9.0-beta.1-latest"
OUTPUT_ROOT = Path(
    os.environ.get(
        "AI_VIDEO_EDITOR_PACKAGE_OUTPUT",
        str(PROJECT_ROOT / "outputs" / "video_diary_fresh_install"),
    )
).expanduser()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_install_readme(package_root: Path) -> None:
    (package_root / "FRESH_INSTALL_README.md").write_text(
        """# 视频日记全新电脑安装包

## 版本身份

- 基础程序版本：`0.9.0-beta.1`
- 视频日记工作流：V1.0 最终收口候选
- 正式 `v1.0.0`：尚未创建

## macOS 全新安装

先安装 Homebrew，再在终端执行：

```bash
brew install python node ffmpeg
cd "/解压后的项目目录"
./scripts/install_macos.sh
./.venv/bin/python scripts/doctor.py --strict
./.venv/bin/python scripts/smoke_test.py
```

安装脚本会建立虚拟环境、运行环境检查、全部自动测试和技术样片。

## 剪映固定 BGM

- 曲名：`科技主题  Global Technology Background`
- 素材 ID：`7377866594003568681`
- 初始音量：`-8.0dB`
- 淡入、淡出：各 1 秒

音乐缓存不在本包内。每台电脑必须使用有权益的剪映账号下载一次，并绑定到
本机视频日记固定模板。详细说明见
`docs/VIDEO_DIARY_BGM_FLEET_SETUP.md`。

## 边界

- 本包不包含原素材、成片、剪映草稿、缓存、账号、密钥或本机私有配置。
- 本包是候选安装包，不是正式 stable Release。
- 全新电脑真实安装、剪映绑定和人工听审完成前，不得标记正式发布通过。
""",
        encoding="utf-8",
    )


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    archive = OUTPUT_ROOT / f"{PACKAGE_NAME}.zip"
    checksum = OUTPUT_ROOT / f"{archive.name}.sha256"

    with tempfile.TemporaryDirectory(prefix="video-diary-fresh-install-") as temp:
        temp_root = Path(temp)
        base_tar = temp_root / "base.tar"
        stage_root = temp_root / PACKAGE_NAME

        subprocess.run(
            [
                "git",
                "archive",
                "--format=tar",
                f"--output={base_tar}",
                BASE_COMMIT,
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )
        stage_root.mkdir()
        with tarfile.open(base_tar, "r") as bundle:
            bundle.extractall(stage_root, filter="data")

        overlay_entries = []
        for relative_value in FILES:
            relative = Path(relative_value)
            source = PROJECT_ROOT / relative
            destination = stage_root / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
            overlay_entries.append(
                {
                    "path": relative.as_posix(),
                    "sha256": sha256(destination),
                    "size": destination.stat().st_size,
                }
            )

        write_install_readme(stage_root)
        manifest = {
            "schema_version": 1,
            "package_id": PACKAGE_NAME,
            "base_commit": BASE_COMMIT,
            "base_version": BASE_VERSION,
            "video_diary_update_id": "video-diary-v1.0-final-20260727",
            "formal_v1_tag_created": False,
            "fresh_machine_acceptance": "NOT_REVIEWED",
            "bgm_track": {
                "provider": "jianying",
                "name": "科技主题  Global Technology Background",
                "material_id": "7377866594003568681",
                "jianying_initial_volume_db": -8.0,
                "standalone_cache_included": False,
            },
            "overlay_files": overlay_entries,
        }
        (stage_root / "INSTALL_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for path in sorted(stage_root.rglob("*")):
                if path.is_file():
                    output.write(
                        path,
                        Path(PACKAGE_NAME) / path.relative_to(stage_root),
                    )

    checksum.write_text(
        f"{sha256(archive)}  {archive.name}\n",
        encoding="utf-8",
    )
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
