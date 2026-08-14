from __future__ import annotations

import json
import plistlib
import subprocess
import time
from pathlib import Path
from typing import Any

from core.qc import CheckStatus, full_decode, probe_video
from skills.factory_shoot.quality import PROTECTED_HUMAN_FIELDS


JIANING_BUNDLE_ID = "com.lemon.lvpro"
JIANING_APP_CANDIDATES = (
    Path("/Applications/VideoFusion-macOS.app"),
    Path("/Applications/JianyingPro.app"),
)
REQUIRED_UI_EVENTS = (
    "app_opened",
    "tracks_imported",
    "timeline_alignment_confirmed",
    "subtitles_visible",
    "native_denoise_enabled",
    "bgm_present",
    "audio_mix_confirmed",
    "export_completed",
)
REQUIRED_SCREENSHOTS = (
    "timeline",
    "subtitles",
    "native_denoise",
    "bgm_mix",
    "export_complete",
)


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def find_jianying_application(
    candidates: tuple[Path, ...] = JIANING_APP_CANDIDATES,
) -> Path | None:
    return next((path for path in candidates if path.is_dir()), None)


def inspect_jianying_application(app: Path) -> dict[str, Any]:
    info_path = app / "Contents" / "Info.plist"
    if not info_path.is_file():
        raise FileNotFoundError(f"Jianying Info.plist not found: {info_path}")
    with info_path.open("rb") as handle:
        info = plistlib.load(handle)
    bundle_id = str(info.get("CFBundleIdentifier", ""))
    if bundle_id != JIANING_BUNDLE_ID:
        raise ValueError(
            f"unexpected Jianying bundle id: {bundle_id or 'missing'}"
        )
    return {
        "application_path": str(app.resolve()),
        "bundle_id": bundle_id,
        "display_name": str(
            info.get("CFBundleDisplayName")
            or info.get("CFBundleName")
            or app.stem
        ),
        "version": str(info.get("CFBundleShortVersionString", "")),
        "build": str(info.get("CFBundleVersion", "")),
    }


def launch_jianying(output_dir: Path, *, wait_seconds: float = 1.0) -> Path:
    app = find_jianying_application()
    if app is None:
        raise FileNotFoundError(
            "剪映专业版未安装；完整工厂工作流已停止，不能改用粗剪代替"
        )
    application = inspect_jianying_application(app)
    completed = subprocess.run(
        ["open", "-b", JIANING_BUNDLE_ID],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"unable to launch Jianying: {detail}")
    if wait_seconds:
        time.sleep(wait_seconds)
    payload = {
        "schema_version": 1,
        **application,
        "launch_command_succeeded": True,
        "computer_use_required": True,
        "ui_work_completed": False,
    }
    return _write_json(
        output_dir / "jianying" / "session_preflight.json", payload
    )


def write_completion_request(output_dir: Path, *, job_id: str) -> Path:
    shared = output_dir / "shared"
    payload = {
        "schema_version": 1,
        "job_id": job_id,
        "status": "BLOCKED_PENDING_JIANYING_UI_AND_HUMAN_REVIEW",
        "deliverable_video": None,
        "computer_use_required": True,
        "tracks": {
            "V1": str((shared / "picture_master_no_audio.mp4").resolve()),
            "A1": str((shared / "dialogue_raw.wav").resolve()),
            "A2": str((shared / "ambience.wav").resolve()),
            "A3": str((shared / "bgm.wav").resolve()),
        },
        "required_ui_events": list(REQUIRED_UI_EVENTS),
        "required_screenshots": list(REQUIRED_SCREENSHOTS),
        "rules": [
            "Use Codex Desktop computer control; fixed coordinates alone are forbidden.",
            "Confirm V1/A1/A2/A3 all start at zero and the picture timeline is unchanged.",
            "Enable Jianying native noise reduction on A1.",
            "Confirm the burned subtitles are visible and do not add Jianying auto captions.",
            "Confirm BGM is audible but does not mask dialogue.",
            "Export a real stereo video and retain UI screenshots plus an action log.",
            "Complete sentence-by-sentence and whole-video human review before finalization.",
        ],
    }
    return _write_json(output_dir / "completion_request.json", payload)


def _load_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} is invalid JSON: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _validate_ui_log(path: Path) -> dict[str, Any]:
    payload = _load_object(path, "Jianying UI action log")
    if payload.get("schema_version") != 1:
        raise ValueError("Jianying UI action log schema_version must equal 1")
    if payload.get("application_bundle_id") != JIANING_BUNDLE_ID:
        raise ValueError("Jianying UI action log has the wrong application_bundle_id")
    events = payload.get("events")
    if not isinstance(events, list):
        raise ValueError("Jianying UI action log events must be a list")
    confirmed = {
        row.get("id")
        for row in events
        if isinstance(row, dict) and row.get("status") == "confirmed"
    }
    missing_events = [event for event in REQUIRED_UI_EVENTS if event not in confirmed]
    if missing_events:
        raise ValueError(
            "Jianying UI evidence is incomplete; missing confirmed events: "
            + ", ".join(missing_events)
        )
    screenshots = payload.get("screenshots")
    if not isinstance(screenshots, dict):
        raise ValueError("Jianying UI screenshots must be recorded")
    for name in REQUIRED_SCREENSHOTS:
        value = screenshots.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Jianying screenshot is missing: {name}")
        evidence = Path(value).expanduser()
        if not evidence.is_file() or evidence.stat().st_size == 0:
            raise ValueError(f"Jianying screenshot is unreadable: {name} -> {evidence}")
    return payload


def _validate_human_review(path: Path) -> dict[str, Any]:
    payload = _load_object(path, "human listening review")
    if payload.get("review_status") != "PASS":
        raise ValueError("human listening review_status must be PASS")
    if not payload.get("reviewer") or not payload.get("reviewed_at"):
        raise ValueError("human listening review must record reviewer and reviewed_at")
    rows = payload.get("sentence_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("human listening review sentence_rows must be non-empty")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"sentence_rows[{index}] must be an object")
        actual = row.get("actual_dialogue")
        if not isinstance(actual, str) or not actual.strip():
            raise ValueError(f"sentence_rows[{index}].actual_dialogue is required")
        for field in (
            "subtitle_matches_dialogue",
            "professional_terms_correct",
            "visible_lip_sync_pass",
        ):
            if row.get(field) is not True:
                raise ValueError(f"sentence_rows[{index}].{field} must be true")
        if row.get("word_loss") is not False:
            raise ValueError(f"sentence_rows[{index}].word_loss must be false")
    whole = payload.get("whole_video")
    if not isinstance(whole, dict):
        raise ValueError("human listening review whole_video must be an object")
    for field in PROTECTED_HUMAN_FIELDS:
        expected: int | bool = 0 if field.endswith("_count") else True
        if whole.get(field) != expected:
            raise ValueError(f"whole_video.{field} must equal {expected!r}")
    return payload


def _validate_subtitles(output_dir: Path, quality: dict[str, Any]) -> None:
    if int(quality.get("caption_count", 0)) <= 0:
        raise ValueError("subtitle caption_count must be greater than zero")
    subtitles = output_dir / "shared" / "subtitles.ass"
    if not subtitles.is_file():
        raise FileNotFoundError(f"subtitle asset not found: {subtitles}")
    text = subtitles.read_text(encoding="utf-8")
    if "Dialogue:" not in text:
        raise ValueError("subtitle asset contains no rendered subtitle events")


def finalize_factory_export(
    *,
    output_dir: Path,
    export: Path,
    ui_log: Path,
    human_review: Path,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
) -> dict[str, Any]:
    output_dir = output_dir.expanduser().resolve()
    quality_path = output_dir / "quality_report.json"
    quality = _load_object(quality_path, "factory quality report")
    if quality.get("automatic_status") != "PASS":
        raise ValueError("automatic factory quality report must pass before finalization")
    _validate_subtitles(output_dir, quality)
    ui_evidence = _validate_ui_log(ui_log.expanduser().resolve())
    review = _validate_human_review(human_review.expanduser().resolve())
    export = export.expanduser().resolve()
    if not export.is_file():
        raise FileNotFoundError(f"Jianying export not found: {export}")
    probe = probe_video(export, ffprobe)
    stream_types = {row.get("codec_type") for row in probe.get("streams", [])}
    if not {"video", "audio"}.issubset(stream_types):
        raise ValueError("Jianying export must contain both video and audio")
    decode = full_decode(export, ffmpeg)
    if decode.status != CheckStatus.PASS:
        raise ValueError(f"Jianying export failed full decode: {decode.detail}")

    whole_video = review["whole_video"]
    quality.update(
        {
            "candidate_video": None,
            "final_video": str(export),
            "jianying_native_master": str(export),
            "jianying_audio_processing_completed": True,
            "jianying_ui_evidence": str(ui_log.resolve()),
            **whole_video,
            "manual_review_required": False,
            "human_review_status": "PASS",
            "rendered_beta_candidate": True,
            "release_complete": True,
            "completion_reason": (
                "automatic QC, Jianying native export, subtitles, BGM, denoise evidence, "
                "sentence review and whole-video review passed"
            ),
        }
    )
    _write_json(quality_path, quality)
    manifest = {
        "schema_version": 1,
        "status": "COMPLETE",
        "job_id": quality.get("job_id"),
        "final_video": str(export),
        "quality_report": str(quality_path),
        "ui_action_log": str(ui_log.resolve()),
        "human_review": str(human_review.resolve()),
        "application_version": ui_evidence.get("application_version"),
        "full_decode_pass": True,
    }
    manifest_path = _write_json(output_dir / "final_delivery_manifest.json", manifest)
    return {
        "status": "COMPLETE",
        "final_video": export,
        "quality_report": quality_path,
        "final_delivery_manifest": manifest_path,
    }
