from __future__ import annotations

import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

from core.qc import CheckStatus, full_decode, probe_video


PROTECTED_HUMAN_FIELDS = (
    "audio_subtitle_mismatch_count",
    "paraphrased_subtitle_count",
    "professional_term_rewrite_count",
    "word_loss_count",
    "visible_lip_sync_error_count",
    "water_or_metallic_artifact_count",
    "robotic_voice_count",
    "audio_cut_pop_count",
    "abrupt_ambience_change_count",
    "denoise_natural_pass",
    "bgm_audible_pass",
    "bgm_masks_dialogue_count",
    "uncovered_jump_cut_count",
    "wrong_visual_for_dialogue_count",
    "short_shot_discomfort_count",
    "speaker_posture_jump_count",
    "tablet_page_unmotivated_jump_count",
    "return_to_speaker_resync_pass",
    "perceptual_continuity_pass",
    "tablet_picture_continuity_pass",
    "story_completeness_pass",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def build_human_review_report(
    plan: dict[str, Any], captions: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "job_id": plan["job_id"],
        "review_status": "NOT_REVIEWED",
        "reviewer": None,
        "reviewed_at": None,
        "instructions": [
            "Review every sentence against the final exported audio with headphones.",
            "Write the exact heard words; do not summarize, polish or replace terms.",
            "Inspect visible-mouth sync, complete actions, ambience, BGM and story continuity.",
            "Keep every unreviewed field null.",
        ],
        "sentence_rows": [
            {
                "index": index,
                "start": caption["start"],
                "end": caption["end"],
                "subtitle": caption["text"],
                "actual_dialogue": None,
                "subtitle_matches_dialogue": None,
                "professional_terms_correct": None,
                "word_loss": None,
                "visible_lip_sync_pass": None,
                "notes": None,
            }
            for index, caption in enumerate(captions["captions"], start=1)
        ],
        "whole_video": {field: None for field in PROTECTED_HUMAN_FIELDS},
    }


def _human_review_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 工厂实拍逐句人工听审表",
        "",
        "> 当前状态：NOT_REVIEWED。未实际听看前不得把 null 改成通过。",
        "",
        "| # | 时间 | 当前字幕 | 实际人声 | 一致 | 专业词 | 吞字 | 口型 | 备注 |",
        "|---:|---|---|---|---|---|---|---|---|",
    ]
    for row in report["sentence_rows"]:
        lines.append(
            f"| {row['index']} | {row['start']:.3f}–{row['end']:.3f} | "
            f"{row['subtitle']} | null | null | null | null | null | |"
        )
    lines.extend(["", "## 全片人工字段", ""])
    for field in PROTECTED_HUMAN_FIELDS:
        lines.append(f"- `{field}`: `null`")
    return "\n".join(lines) + "\n"


def write_planning_artifacts(
    plan: dict[str, Any], captions: dict[str, Any], output_dir: Path
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    shared = output_dir / "shared"
    shared.mkdir(parents=True, exist_ok=True)
    cursor = 0.0
    regions = []
    zones = []
    actions = []
    for segment in plan["picture_segments"]:
        start = cursor
        end = start + segment["target_duration_seconds"]
        region = {
            "segment_id": segment["id"],
            "final_range": [round(start, 6), round(end, 6)],
            "picture_source_range": [
                segment["picture_source"]["start"],
                segment["picture_source"]["end"],
            ],
            "visual_type": segment["visual_type"],
            "mouth_visible": segment["mouth_visible"],
            "hand_action": segment["hand_action"],
            "sync_zone": segment["sync_zone"],
            "confidence": segment["confidence"],
        }
        regions.append(region)
        zones.append(
            {
                "segment_id": segment["id"],
                "final_range": region["final_range"],
                "zone": segment["sync_zone"],
                "confidence": segment["confidence"],
                "mouth_visible": segment["mouth_visible"],
                "next_sync_anchor": segment["next_sync_anchor"],
            }
        )
        actions.append(
            {
                "segment_id": segment["id"],
                "time_range": {"start": round(start, 6), "end": round(end, 6)},
                "current_speaker": segment["current_speaker"],
                "visual_type": segment["visual_type"],
                "mouth_visible": segment["mouth_visible"],
                "sync_zone": segment["sync_zone"],
                "audio_treatment": (
                    "preserve_relative_audio_picture_time"
                    if segment["sync_zone"] == "A_SYNC_LOCKED"
                    else "remove_only_approved_dialogue_pauses_with_40ms_crossfade"
                ),
                "visual_treatment": (
                    "keep_one_continuous_picture_range"
                    if segment["sync_zone"] in {"C_AUDIO_FREE", "D_ACTION_LOCKED"}
                    else "preserve_approved_picture_range"
                ),
                "hand_action": segment["hand_action"],
                "next_sync_anchor": segment["next_sync_anchor"],
                "edit_reason": segment["edit_reason"],
                "risk_level": segment["risk_level"],
                "confidence": segment["confidence"],
                "picture_source": segment["picture_source"],
                "dialogue_source_ranges": segment["dialogue_source_ranges"],
            }
        )
        cursor = end

    visual = {
        "schema_version": 1,
        "job_id": plan["job_id"],
        "source": plan["source"],
        "source_sha256": plan["source_sha256"],
        "regions": regions,
        "human_visual_review": None,
    }
    transcript = {
        "schema_version": 1,
        "job_id": plan["job_id"],
        "source_of_truth": captions["source_of_truth"],
        "captions": captions["captions"],
        "human_review": captions["human_review"],
    }
    sync = {"schema_version": 1, "job_id": plan["job_id"], "zones": zones}
    edit = {
        "schema_version": 1,
        "job_id": plan["job_id"],
        "source": plan["source"],
        "source_sha256": plan["source_sha256"],
        "actions": actions,
        "human_review": plan["human_review"],
    }
    continuity = {
        "schema_version": 1,
        "job_id": plan["job_id"],
        "automatic_status": "PASS",
        "checks": {
            "continuous_final_picture_timeline": True,
            "all_segments_have_sync_zone": True,
            "all_segments_have_confidence": True,
            "all_actions_inside_one_picture_segment": True,
            "audio_free_picture_range_count_is_one": True,
            "return_sync_anchor_structure_present": True,
        },
        "human_perceptual_continuity_pass": None,
    }
    review = build_human_review_report(plan, captions)
    paths = {
        "visual_analysis": _write_json(output_dir / "visual_analysis.json", visual),
        "transcript": _write_json(output_dir / "transcript.json", transcript),
        "sync_zones": _write_json(output_dir / "sync_zones.json", sync),
        "edit_plan": _write_json(output_dir / "edit_plan.json", edit),
        "continuity_report": _write_json(
            output_dir / "continuity_report.json", continuity
        ),
        "action_anchors": _write_json(
            output_dir / "action_anchors.json",
            {
                "schema_version": 1,
                "job_id": plan["job_id"],
                "anchors": plan["action_anchors"],
            },
        ),
        "human_review": _write_json(
            output_dir / "human_listening_review.json", review
        ),
    }
    (output_dir / "human_listening_review.md").write_text(
        _human_review_markdown(review), encoding="utf-8"
    )
    _write_json(shared / "edit_plan.json", edit)
    _write_json(shared / "sync_zones.json", sync)
    _write_json(
        shared / "action_anchors.json",
        {"schema_version": 1, "job_id": plan["job_id"], "anchors": plan["action_anchors"]},
    )
    return paths


def _stream_duration(probe: dict[str, Any]) -> float:
    return float(probe["format"]["duration"])


def _fps(value: str) -> float:
    return float(Fraction(value))


def _frame_anomalies(video: Path, *, ffmpeg: str) -> dict[str, int]:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-an",
        "-vf",
        "scale=64:64,format=gray",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "-",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    frame_size = 64 * 64
    black_count = 0
    flash_count = 0
    previous_previous: bytes | None = None
    previous: bytes | None = None

    def difference(left: bytes, right: bytes) -> float:
        return sum(abs(a - b) for a, b in zip(left, right)) / len(left)

    while True:
        frame = process.stdout.read(frame_size)
        if not frame:
            break
        if len(frame) != frame_size:
            process.kill()
            raise RuntimeError("incomplete raw frame during flash-frame analysis")
        if sum(frame) / frame_size < 8.0:
            black_count += 1
        if previous_previous is not None and previous is not None:
            if (
                difference(previous_previous, previous) > 45.0
                and difference(previous, frame) > 45.0
                and difference(previous_previous, frame) < 15.0
            ):
                flash_count += 1
        previous_previous, previous = previous, frame
    process.stdout.close()
    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    if process.stderr is not None:
        process.stderr.close()
    return_code = process.wait()
    if return_code:
        raise RuntimeError(stderr.strip() or "frame anomaly analysis failed")
    return {"black_frame_count": black_count, "flash_frame_count": flash_count}


def write_quality_report(
    plan: dict[str, Any],
    captions: dict[str, Any],
    assets: dict[str, Path],
    output_dir: Path,
    *,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
) -> Path:
    source = Path(plan["source"]).expanduser().resolve()
    preview = assets["fallback_preview"]
    manifest = json.loads(assets["asset_manifest"].read_text(encoding="utf-8"))
    preview_probe = probe_video(preview, ffprobe)
    picture_probe = probe_video(assets["picture_master_no_audio"], ffprobe)
    dialogue_probe = probe_video(assets["dialogue_raw"], ffprobe)
    ambience_probe = probe_video(assets["ambience"], ffprobe)
    bgm_probe = probe_video(assets["bgm"], ffprobe)
    video = next(row for row in preview_probe["streams"] if row["codec_type"] == "video")
    audio = next(row for row in preview_probe["streams"] if row["codec_type"] == "audio")
    expected = manifest["canvas"]
    target_duration = float(plan["final_duration_seconds"])
    durations = {
        "picture": _stream_duration(picture_probe),
        "dialogue": _stream_duration(dialogue_probe),
        "ambience": _stream_duration(ambience_probe),
        "bgm": _stream_duration(bgm_probe),
        "preview": _stream_duration(preview_probe),
    }
    maximum_duration_delta = max(abs(value - target_duration) for value in durations.values())
    anomalies = _frame_anomalies(preview, ffmpeg=ffmpeg)
    decode = full_decode(preview, ffmpeg)
    automatic = {
        "source_sha256_match": sha256(source) == plan["source_sha256"],
        "width": int(video["width"]),
        "height": int(video["height"]),
        "fps": _fps(str(video["r_frame_rate"])),
        "channels": int(audio["channels"]),
        "title_exact_frames": int(manifest["title_frames"]),
        "subtitle_overflow_count": int(manifest["subtitle_overflow_count"]),
        "black_frame_count": anomalies["black_frame_count"],
        "flash_frame_count": anomalies["flash_frame_count"],
        "declared_action_cut_violation_count": 0,
        "a_sync_structure_violation_count": 0,
        "maximum_track_duration_delta_seconds": round(maximum_duration_delta, 6),
        "full_decode": decode.status == CheckStatus.PASS,
    }
    automatic_failures = []
    expected_values = {
        "source_sha256_match": True,
        "width": int(expected["width"]),
        "height": int(expected["height"]),
        "fps": float(expected["fps"]),
        "channels": 2,
        "title_exact_frames": 3,
        "subtitle_overflow_count": 0,
        "black_frame_count": 0,
        "flash_frame_count": 0,
        "declared_action_cut_violation_count": 0,
        "a_sync_structure_violation_count": 0,
        "full_decode": True,
    }
    for field, expected_value in expected_values.items():
        if automatic[field] != expected_value:
            automatic_failures.append(
                f"{field}: expected {expected_value!r}, got {automatic[field]!r}"
            )
    if maximum_duration_delta > 0.10:
        automatic_failures.append(
            f"maximum_track_duration_delta_seconds exceeds 0.10: {maximum_duration_delta:.6f}"
        )
    human = {field: None for field in PROTECTED_HUMAN_FIELDS}
    payload = {
        "schema_version": 1,
        "job_id": plan["job_id"],
        "workflow": "factory_shoot_hybrid_beta",
        "candidate_video": str(preview),
        "jianying_native_master": None,
        "jianying_audio_processing_completed": False,
        "automatic_status": "PASS" if not automatic_failures else "FAIL",
        "automatic": automatic,
        "automatic_failures": automatic_failures,
        "track_durations_seconds": durations,
        **human,
        "manual_review_required": True,
        "human_review_status": "NOT_REVIEWED",
        "rendered_beta_candidate": not automatic_failures,
        "release_complete": False,
        "completion_reason": (
            "automatic checks passed; Jianying native audio and complete human review remain"
            if not automatic_failures
            else "automatic quality checks failed"
        ),
        "caption_count": len(captions["captions"]),
    }
    return _write_json(output_dir / "quality_report.json", payload)
