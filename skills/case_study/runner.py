from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skills.case_study.contract import validate_job_contract
from skills.case_study.edit_planner import validate_edit_plan
from skills.case_study.renderer import render_segments
from skills.case_study.source_analyzer import build_source_manifest
from skills.case_study.story_analyzer import analyze_story_units
from skills.case_study.sync_zone_analyzer import (
    analyze_sync_zones,
    write_sync_zones,
)
from skills.case_study.transcript_pipeline import load_whisper_segments
from skills.case_study.visual_analyzer import build_contact_sheet, detect_scene_changes


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = ROOT / "var/models/ggml-small-q5_1.bin"
DEFAULT_CASE_PROMPT = (
    "MES系统，智能三色灯，安灯系统，设备联网，生产看板，"
    "电子作业指导书，注塑车间，冲压车间，自动组装，"
    "PMC，计件工资，客户报价，员工激励机制。"
)


@dataclass(frozen=True)
class AnalyzeRequest:
    job_id: str
    source: Path
    output_dir: Path
    whisper_model: Path = DEFAULT_MODEL
    whisper_command: str = "whisper-cli"
    initial_prompt: str = DEFAULT_CASE_PROMPT


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)
    return path


def build_job_contract(
    job_id: str,
    source_manifest: dict[str, Any],
    story_analysis: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "job_id": job_id,
        "source": {
            "path": source_manifest["path"],
            "sha256": source_manifest["sha256"],
            "duration_seconds": source_manifest["duration_seconds"],
        },
        "story_units": story_analysis["units"],
        "human_review": {
            "transcript_pass": None,
            "professional_terms_pass": None,
            "story_pass": None,
            "playback_pass": None,
        },
        "release_state": "ANALYSIS",
    }
    return validate_job_contract(payload)


def _extract_audio(source: Path, output: Path) -> Path:
    if output.is_file() and output.stat().st_size > 44:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-vn",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "audio extraction failed")
    return output


def _transcribe(
    audio: Path,
    output_prefix: Path,
    *,
    model: Path,
    whisper_command: str,
    initial_prompt: str,
) -> Path:
    output = output_prefix.with_suffix(".json")
    if output.is_file():
        return output
    command = shutil.which(whisper_command)
    if command is None:
        raise FileNotFoundError(f"whisper command not found: {whisper_command}")
    if not model.is_file():
        raise FileNotFoundError(model)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            command,
            "-m",
            str(model),
            "-f",
            str(audio),
            "-l",
            "zh",
            "-ojf",
            "-of",
            str(output_prefix),
            "-np",
            "-t",
            "4",
            "--prompt",
            initial_prompt,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "local transcription failed")
    return output


def transcription_cache_key(
    *,
    source_sha256: str,
    audio_size_bytes: int,
    model: Path,
    initial_prompt: str,
) -> str:
    payload = "|".join(
        (
            source_sha256,
            str(audio_size_bytes),
            str(model.expanduser().resolve()),
            str(model.stat().st_size),
            initial_prompt,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _write_transcript_review(
    path: Path,
    segments: list[dict[str, Any]],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "segment_index",
                "from_seconds",
                "to_seconds",
                "machine_text",
                "actual_spoken_text",
                "professional_terms",
                "human_review_pass",
            ),
        )
        writer.writeheader()
        for index, segment in enumerate(segments):
            writer.writerow(
                {
                    "segment_index": index,
                    "from_seconds": segment["from_ms"] / 1000,
                    "to_seconds": segment["to_ms"] / 1000,
                    "machine_text": segment["text"],
                    "actual_spoken_text": "",
                    "professional_terms": "|".join(
                        item["term"]
                        for item in segment["professional_term_flags"]
                    ),
                    "human_review_pass": "",
                }
            )
    return path


def analyze(request: AnalyzeRequest) -> Path:
    source = request.source.expanduser().resolve()
    output = request.output_dir.expanduser().resolve()
    reports = output / "reports"
    source_manifest = build_source_manifest(source)
    write_json(reports / "source_manifest.json", source_manifest)

    audio = _extract_audio(source, output / "audio/source.wav")
    asr_cache_key = transcription_cache_key(
        source_sha256=source_manifest["sha256"],
        audio_size_bytes=audio.stat().st_size,
        model=request.whisper_model,
        initial_prompt=request.initial_prompt,
    )
    asr_json = _transcribe(
        audio,
        output / f"asr/source_{asr_cache_key}",
        model=request.whisper_model,
        whisper_command=request.whisper_command,
        initial_prompt=request.initial_prompt,
    )
    segments = load_whisper_segments(asr_json)
    write_json(
        reports / "transcript.machine.json",
        {
            "schema_version": 1,
            "source": str(source),
            "asr_cache_key": asr_cache_key,
            "model": str(request.whisper_model.expanduser().resolve()),
            "initial_prompt": request.initial_prompt,
            "segments": segments,
            "release_subtitle_source": False,
            "human_review_completed": False,
        },
    )
    _write_transcript_review(reports / "transcript.review.csv", segments)

    story = analyze_story_units(segments)
    write_json(reports / "story_analysis.json", story)
    contract = build_job_contract(request.job_id, source_manifest, story)
    write_json(output / "job.json", contract)

    visual = build_contact_sheet(
        source,
        source_manifest["duration_seconds"],
        output / "source_contact_sheet.jpg",
        frame_dir=output / "frames/source",
    )
    visual["scene_detection"] = detect_scene_changes(source)
    write_json(reports / "visual_analysis.json", visual)

    sync = analyze_sync_zones(source, source_manifest["duration_seconds"])
    write_sync_zones(reports / "sync_zones.json", sync)
    write_json(
        reports / "quality_report.json",
        {
            "schema_version": 1,
            "stage": "analysis",
            "source_probe_pass": True,
            "source_hash_present": True,
            "machine_transcript_present": True,
            "story_complete_candidate": story["status"] == "complete_candidate",
            "sync_zone_candidates_present": bool(sync["zones"]),
            "transcript_human_review_pass": None,
            "professional_terms_human_review_pass": None,
            "story_human_review_pass": None,
            "final_playback_pass": None,
            "release_ready": False,
        },
    )
    return output


def render_draft(plan_path: Path, output: Path, *, allow_unreviewed: bool) -> Path:
    plan = validate_edit_plan(
        json.loads(plan_path.read_text(encoding="utf-8"))
    )
    review = plan.get("human_review", {})
    if not allow_unreviewed and not (
        review.get("plan_approved") is True
        and review.get("transcript_pass") is True
    ):
        raise ValueError("final render requires approved plan and transcript")
    segments = [
        action
        for action in plan["actions"]
        if action["operation"] in {"keep", "reorder_keep"}
    ]
    return render_segments(Path(plan["source"]), segments, output)
