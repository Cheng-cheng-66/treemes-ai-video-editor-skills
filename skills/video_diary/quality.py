from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core.process import run_command
from skills.video_diary.aspect_ratio import probe_source_geometry


def parse_ebur128_summary(stderr: str) -> dict[str, float]:
    loudness = re.findall(r"\bI:\s*(-?\d+(?:\.\d+)?)\s+LUFS", stderr)
    true_peak = re.findall(r"\bPeak:\s*(-?\d+(?:\.\d+)?)\s+dBFS", stderr)
    if not loudness or not true_peak:
        raise ValueError("unable to parse FFmpeg ebur128 summary")
    return {
        "integrated_loudness_lufs": float(loudness[-1]),
        "true_peak_dbtp": float(true_peak[-1]),
    }


def measure_audio(media: Path, ffmpeg: str = "ffmpeg") -> dict[str, Any]:
    result = run_command(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-i",
            str(media),
            "-map",
            "0:a:0",
            "-af",
            "ebur128=peak=true",
            "-f",
            "null",
            "-",
        ],
        timeout=None,
    )
    if result.returncode != 0:
        raise RuntimeError(f"audio measurement failed for {media}")
    return parse_ebur128_summary(result.stderr)


def write_quality_report(
    *,
    plan: dict[str, Any],
    output: Path,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
    expected_geometry: dict[str, Any] | None = None,
) -> Path:
    source = Path(str(plan["source"])).expanduser()
    decode = run_command(
        [ffmpeg, "-v", "error", "-i", str(output), "-f", "null", "-"],
        timeout=None,
    )
    before = measure_audio(source, ffmpeg)
    after = measure_audio(output, ffmpeg)
    actual_output_geometry = probe_source_geometry(output, ffprobe)
    aspect_ratio_matches = True
    if expected_geometry is not None:
        aspect_ratio_matches = (
            actual_output_geometry.encoded_width
            == expected_geometry["output_width"]
            and actual_output_geometry.encoded_height
            == expected_geometry["output_height"]
            and actual_output_geometry.inherited_output_aspect_ratio
            == expected_geometry["output_aspect_ratio"]
        )
    report = {
        "schema_version": 1,
        "workflow": "video_diary_v1_final",
        "source": str(source),
        "output": str(output),
        "speed": plan["speed"],
        "aspect_ratio": {
            "policy": "inherit_source_unless_explicitly_authorized",
            "requested": plan.get("output_aspect_ratio", "source"),
            "expected": expected_geometry,
            "actual_output": actual_output_geometry.to_dict(),
            "matches_expected": aspect_ratio_matches,
        },
        "speed_assessment": plan.get(
            "speed_assessment",
            {
                "original_pace": "not explicitly slow",
                "post_cut_pace": "no acceleration required",
                "reason": "default 1.00 when no explicit acceleration judgment exists",
            },
        ),
        "remove_intervals": plan["remove"],
        "image_treatment": plan["image_treatment"],
        "audio_treatment": plan["audio_treatment"],
        "bgm": {
            "mode": plan["bgm_mode"],
            "track": plan.get("bgm_track"),
            "manual_review": (
                "NOT_APPLICABLE"
                if plan["bgm_mode"] == "off"
                else "NOT_REVIEWED"
            ),
        },
        "audio_before": before,
        "audio_after": after,
        "audio_gain_lu": round(
            after["integrated_loudness_lufs"]
            - before["integrated_loudness_lufs"],
            1,
        ),
        "automatic_checks": {
            "full_decode": "PASS" if decode.returncode == 0 else "FAIL",
            "source_aspect_ratio_detected": (
                "PASS" if expected_geometry is not None else "NOT_REVIEWED"
            ),
            "output_aspect_ratio_matches_expected": (
                "PASS" if aspect_ratio_matches else "FAIL"
            ),
            "integrated_loudness_target_lufs": -16.0,
            "true_peak_limit_dbtp": -1.0,
            "clipping_detected": after["true_peak_dbtp"] > -1.0,
        },
        "manual_review": {
            "subtitle_verbatim": "NOT_REVIEWED",
            "professional_terms": "NOT_REVIEWED",
            "meaningful_speech_not_removed": "NOT_REVIEWED",
            "audio_artifacts": "NOT_REVIEWED",
            "audio_video_sync": "NOT_REVIEWED",
            "breath_and_pause_naturalness": "NOT_REVIEWED",
            "noise_reduction_sound": "NOT_REVIEWED",
            "bgm_sound": (
                "NOT_APPLICABLE"
                if plan["bgm_mode"] == "off"
                else "NOT_REVIEWED"
            ),
            "cover_and_header": "NOT_REVIEWED",
            "quicktime_full_playback": "NOT_REVIEWED",
        },
    }
    report_path = output.with_suffix(".quality_report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not aspect_ratio_matches:
        raise RuntimeError(
            "output aspect ratio does not match the source-inheritance "
            f"decision; see {report_path}"
        )
    return report_path
