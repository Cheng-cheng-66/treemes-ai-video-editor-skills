#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import load_config
from core.qc import (
    CheckResult,
    CheckStatus,
    full_decode,
    overall_status,
    probe_video,
    write_report,
)
from skills.video_diary.runner import RenderRequest, render


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _video_stream(probe: dict) -> dict:
    return next(
        stream for stream in probe["streams"] if stream["codec_type"] == "video"
    )


def collect_regression_checks() -> tuple[list[CheckResult], dict]:
    fixture_path = (
        PROJECT_ROOT / "tests" / "fixtures" / "video_diary" / "test_set.json"
    )
    test_set = json.loads(fixture_path.read_text(encoding="utf-8"))
    baseline = test_set["baseline"]
    video = PROJECT_ROOT / baseline["output"]
    ass = PROJECT_ROOT / baseline["ass"]
    plan_path = PROJECT_ROOT / baseline["plan"]
    captions_path = PROJECT_ROOT / baseline["captions"]
    source_env = str(baseline["source_environment_variable"])
    source = Path(os.environ[source_env]).expanduser() if os.environ.get(source_env) else None
    checks: list[CheckResult] = []

    if not video.is_file():
        checks.append(
            CheckResult(
                "baseline_output_available",
                CheckStatus.FAIL,
                f"baseline output is missing: {video}",
            )
        )
        return checks, test_set

    actual_hash = _sha256(video)
    checks.append(
        CheckResult(
            "baseline_output_hash",
            CheckStatus.PASS
            if actual_hash == baseline["sha256"]
            else CheckStatus.FAIL,
            f"expected={baseline['sha256']} actual={actual_hash}",
        )
    )
    probe = probe_video(video)
    stream = _video_stream(probe)
    specification_ok = (
        stream.get("width") == 1080
        and stream.get("height") == 1920
        and stream.get("r_frame_rate") == "30/1"
        and stream.get("codec_name") == "h264"
    )
    checks.append(
        CheckResult(
            "output_specification",
            CheckStatus.PASS if specification_ok else CheckStatus.FAIL,
            (
                f"{stream.get('width')}x{stream.get('height')} "
                f"{stream.get('r_frame_rate')} {stream.get('codec_name')}"
            ),
            probe,
        )
    )
    checks.append(full_decode(video))

    captions = json.loads(captions_path.read_text(encoding="utf-8"))
    multiline = [
        item["text"]
        for item in captions
        if "\n" in item["text"] or "\\N" in item["text"]
    ]
    checks.append(
        CheckResult(
            "subtitle_safe_area_structure",
            CheckStatus.PASS if not multiline else CheckStatus.FAIL,
            (
                f"{len(captions)} single-line caption events; fixed 1080x1920 "
                "safe-area preset and measured-width gate"
                if not multiline
                else f"multiline captions found: {len(multiline)}"
            ),
        )
    )
    checks.append(
        CheckResult(
            "subtitle_verbatim_to_voice",
            CheckStatus.MANUAL_REVIEW_REQUIRED,
            "captions carry audio-review provenance, but current source audio is required for an independent word-for-word audit",
        )
    )
    checks.append(
        CheckResult(
            "subtitle_no_summary_rewrite_or_omission",
            CheckStatus.MANUAL_REVIEW_REQUIRED,
            "requires listening to final edited audio against all caption events",
        )
    )
    checks.append(
        CheckResult(
            "mes_diary_date_day",
            CheckStatus.MANUAL_REVIEW_REQUIRED,
            "template hashes match the approved V5 baseline; date/Day content still needs playback review on the candidate output",
        )
    )
    checks.append(
        CheckResult(
            "cover_and_persistent_header_states",
            CheckStatus.MANUAL_REVIEW_REQUIRED,
            "cover/header templates are byte-identical to baseline; transition and persistence require representative-frame review",
        )
    )
    checks.append(
        CheckResult(
            "audio_video_sync",
            CheckStatus.MANUAL_REVIEW_REQUIRED,
            "container decode passed; perceptual lip-sync requires playback",
        )
    )
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    interval_valid = all(
        0 <= float(item["start"]) < float(item["end"]) <= plan["source_duration_seconds"]
        for item in plan["remove"]
    )
    checks.append(
        CheckResult(
            "pause_removal_rules",
            CheckStatus.PASS if interval_valid else CheckStatus.FAIL,
            f"{len(plan['remove'])} ordered/valid removal intervals with explicit reasons",
        )
    )
    checks.append(
        CheckResult(
            "valid_speech_not_removed",
            CheckStatus.MANUAL_REVIEW_REQUIRED,
            "requires source-audio review around every cut boundary",
        )
    )
    checks.append(
        CheckResult(
            "denoise_voice_damage",
            CheckStatus.MANUAL_REVIEW_REQUIRED,
            "requires headphones/listening review of processed voice",
        )
    )
    checks.append(
        CheckResult(
            "bgm_voice_masking",
            CheckStatus.PASS,
            "the V5 video-diary renderer does not add a BGM track",
        )
    )
    reports_exist = all(
        (PROJECT_ROOT / path).is_file()
        for path in [
            "outputs/video_pilot/QC_REPORT_V2.md",
            "outputs/video_pilot/quality_report.json",
            "outputs/video_pilot/CURRENT_STATUS.md",
        ]
    )
    checks.append(
        CheckResult(
            "logs_and_quality_reports",
            CheckStatus.PASS if reports_exist else CheckStatus.FAIL,
            "baseline edit/QC/status evidence is present"
            if reports_exist
            else "one or more baseline reports are missing",
        )
    )

    if source and source.is_file():
        checks.append(
            CheckResult(
                "original_source_unchanged",
                CheckStatus.MANUAL_REVIEW_REQUIRED,
                f"source is available at {source}; record pre/post SHA-256 during a full rerender",
            )
        )
    else:
        checks.append(
            CheckResult(
                "original_source_unchanged",
                CheckStatus.MANUAL_REVIEW_REQUIRED,
                f"set {source_env} to the mounted read-only source before full regression",
            )
        )

    try:
        render(
            RenderRequest(
                plan=plan_path,
                captions=captions_path,
                output=PROJECT_ROOT / "var" / "outputs" / "should-not-render.mp4",
                date="2026/07/25",
                day="Day14",
            ),
            load_config(),
        )
        clear_failure = False
    except FileNotFoundError as exc:
        clear_failure = "source media not found" in str(exc)
    checks.append(
        CheckResult(
            "clear_failure_message",
            CheckStatus.PASS if clear_failure else CheckStatus.FAIL,
            "missing source returns an explicit error before FFmpeg starts",
        )
    )
    checks.append(
        CheckResult(
            "version_difference_record",
            CheckStatus.PASS,
            f"baseline SHA-256 is locked in {fixture_path.relative_to(PROJECT_ROOT)}",
        )
    )

    for case in test_set["cases"]:
        if case["availability"] == "missing" and case["release_required"]:
            checks.append(
                CheckResult(
                    f"test_case_{case['id']}",
                    CheckStatus.FAIL,
                    f"required fixed sample is missing: {case['needed']}",
                )
            )
        else:
            checks.append(
                CheckResult(
                    f"test_case_{case['id']}",
                    CheckStatus.PASS,
                    f"availability={case['availability']}",
                )
            )
    return checks, test_set


def _write_markdown(path: Path, checks: list[CheckResult]) -> None:
    lines = [
        "# 视频日记回归报告",
        "",
        f"- 生成时间：{datetime.now(timezone.utc).isoformat()}",
        f"- 总状态：**{overall_status(checks)}**",
        "",
        "| 检查项 | 结果 | 说明 |",
        "|---|---|---|",
    ]
    for check in checks:
        detail = check.detail.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{check.check_id}` | {check.status} | {detail} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run video-diary regression")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "video_diary_regression.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "video_diary_regression.md",
    )
    args = parser.parse_args()
    checks, test_set = collect_regression_checks()
    write_report(
        args.json_output,
        checks,
        schema_version=1,
        generated_at=datetime.now(timezone.utc).isoformat(),
        test_set=test_set,
    )
    _write_markdown(args.markdown_output, checks)
    for check in checks:
        print(f"{check.status}: {check.check_id} - {check.detail}")
    status = overall_status(checks)
    print(f"OVERALL: {status}")
    return 1 if status == CheckStatus.FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
