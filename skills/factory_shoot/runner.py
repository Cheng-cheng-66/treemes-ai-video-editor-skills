from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import AppConfig, create_runtime_dirs, load_config
from core.process import executable_path
from core.qc import probe_video
from skills.factory_shoot.contract import validate_captions, validate_edit_plan
from skills.factory_shoot.quality import (
    sha256,
    write_planning_artifacts,
    write_quality_report,
)
from skills.factory_shoot.renderer import DEFAULT_FONT, render_factory_assets


@dataclass(frozen=True)
class FactoryRenderRequest:
    plan: Path
    captions: Path
    output_dir: Path
    bgm: Path | None = None
    output_size_override: tuple[int, int] | None = None
    fps_override: int | None = None


def _font_path(config: AppConfig) -> Path:
    profile = str(config.video_diary.get("font_profile", "auto"))
    if profile == "auto":
        profile = "windows" if platform.system() == "Windows" else "macos"
    value = (
        config.video_diary.get("fonts", {})
        .get(profile, {})
        .get("subtitle")
    )
    return Path(str(value)).expanduser() if value else DEFAULT_FONT


def _write_jianying_manifest(
    output_dir: Path, plan: dict[str, Any], *, bgm_supplied: bool
) -> Path:
    payload = {
        "schema_version": 1,
        "job_id": plan["job_id"],
        "route": "supervised_jianying_native_audio_finishing",
        "application": "剪映专业版",
        "validated_environment": "7.9.0 historical baseline; confirm installed version before use",
        "tracks": {
            "V1": "shared/picture_master_no_audio.mp4",
            "A1": "shared/dialogue_raw.wav",
            "A2": "shared/ambience.wav",
            "A3": "shared/bgm.wav",
        },
        "all_tracks_start_seconds": 0.0,
        "picture_timeline_locked": True,
        "jianying_may_regenerate_subtitles": False,
        "jianying_may_change_title": False,
        "jianying_may_add_visual_effects": False,
        "dialogue_native_noise_reduction_required": True,
        "bgm_source_supplied": bgm_supplied,
        "native_export_completed": False,
        "native_export_path": None,
        "human_audio_review": None,
    }
    path = output_dir / "jianying_import_manifest.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def run(
    request: FactoryRenderRequest,
    config: AppConfig | None = None,
) -> dict[str, Path]:
    active = config or load_config()
    create_runtime_dirs(active)
    for command in ("ffmpeg", "ffprobe"):
        if executable_path(command) is None:
            raise RuntimeError(f"required command not found: {command}")
    if not request.plan.is_file():
        raise FileNotFoundError(f"factory plan not found: {request.plan}")
    if not request.captions.is_file():
        raise FileNotFoundError(f"factory captions not found: {request.captions}")
    plan = validate_edit_plan(
        json.loads(request.plan.read_text(encoding="utf-8"))
    )
    captions = validate_captions(
        json.loads(request.captions.read_text(encoding="utf-8")),
        final_duration_seconds=plan["final_duration_seconds"],
    )
    source = Path(plan["source"]).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"factory source not found: {source}")
    actual_hash = sha256(source)
    if actual_hash != plan["source_sha256"]:
        raise ValueError(
            f"factory source hash mismatch: expected {plan['source_sha256']}, got {actual_hash}"
        )
    source_probe = probe_video(source)
    actual_duration = float(source_probe["format"]["duration"])
    if abs(actual_duration - plan["source_duration_seconds"]) > 0.15:
        raise ValueError(
            "factory source duration does not match the approved plan: "
            f"expected {plan['source_duration_seconds']:.3f}, got {actual_duration:.3f}"
        )
    request.output_dir.mkdir(parents=True, exist_ok=True)
    planning = write_planning_artifacts(plan, captions, request.output_dir)
    assets = render_factory_assets(
        plan,
        captions,
        request.output_dir,
        bgm_source=request.bgm,
        font_path=_font_path(active),
        output_size_override=request.output_size_override,
        fps_override=request.fps_override,
    )
    jianying = _write_jianying_manifest(
        request.output_dir, plan, bgm_supplied=request.bgm is not None
    )
    quality = write_quality_report(
        plan,
        captions,
        assets,
        request.output_dir,
    )
    return {**planning, **assets, "jianying_manifest": jianying, "quality_report": quality}
