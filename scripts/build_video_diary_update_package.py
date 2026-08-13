#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "configs/default.json",
    "docs/VIDEO_DIARY_BGM_FLEET_SETUP.md",
    "presets/video_diary/README.md",
    "presets/video_diary/bgm.yaml",
    "presets/video_diary/cover.yaml",
    "presets/video_diary/editing_rules.yaml",
    "presets/video_diary/header.yaml",
    "presets/video_diary/quality_rules.yaml",
    "presets/video_diary/subtitle.yaml",
    "scripts/smoke_test.py",
    "skills/video_diary/legacy/render_video_diary_v5.js",
    "skills/video_diary/quality.py",
    "skills/video_diary/runner.py",
    "skills/video_diary/skill.json",
    "tests/fixtures/video_diary/standard_plan.json",
    "tests/test_template_compatibility.py",
    "tests/test_video_diary_quality.py",
    "tests/test_video_diary_runner.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    output_root = Path(
        os.environ.get(
            "AI_VIDEO_EDITOR_PACKAGE_OUTPUT",
            str(PROJECT_ROOT / "outputs" / "video_diary_update"),
        )
    ).expanduser()
    stage = PROJECT_ROOT / "work" / "video_diary_v1_final" / "incremental_update"
    if stage.exists():
        shutil.rmtree(stage)
    payload = stage / "payload"
    payload.mkdir(parents=True)

    entries = []
    for relative_value in FILES:
        relative = Path(relative_value)
        source = PROJECT_ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = payload / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        entries.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256(destination),
                "size": destination.stat().st_size,
            }
        )

    shutil.copy2(PROJECT_ROOT / "scripts" / "apply_video_diary_update.py", stage)
    readme = stage / "README_UPDATE.md"
    readme.write_text(
        "# 视频日记增量更新包\n\n"
        "无需重新安装。解压后在终端运行：\n\n"
        "```bash\n"
        "python3 apply_video_diary_update.py --project /你的/自动剪辑项目路径 --dry-run\n"
        "python3 apply_video_diary_update.py --project /你的/自动剪辑项目路径\n"
        "```\n\n"
        "脚本会备份被覆盖文件、校验包内哈希、运行 doctor、全部测试和"
        "技术样片；失败会恢复备份。\n\n"
        "本包不包含剪映音乐缓存。更新成功后按 "
        "`docs/VIDEO_DIARY_BGM_FLEET_SETUP.md` 在剪映内一次性下载固定曲目。\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "update_id": "video-diary-v1.0-final-20260727",
        "allowed_base_versions": ["0.9.0-beta.1"],
        "source_branch": "release/v1.0.0",
        "source_head": "d5085e01834390f218591daebf9f84ee9cca7657",
        "bgm_track": {
            "provider": "jianying",
            "name": "科技主题  Global Technology Background",
            "material_id": "7377866594003568681",
            "jianying_initial_volume_db": -8.0,
            "standalone_cache_included": False,
        },
        "files": entries,
    }
    (stage / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    output_root.mkdir(parents=True, exist_ok=True)
    archive = output_root / "video-diary-v1.0-final-incremental-update.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(stage).as_posix())
    checksum = output_root / f"{archive.name}.sha256"
    checksum.write_text(
        f"{sha256(archive)}  {archive.name}\n",
        encoding="utf-8",
    )
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
