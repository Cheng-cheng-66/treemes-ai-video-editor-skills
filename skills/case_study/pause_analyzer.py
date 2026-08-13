from __future__ import annotations

import re
import json
import subprocess
from pathlib import Path
from typing import Any


START_PATTERN = re.compile(r"silence_start:\s*([0-9.]+)")
END_PATTERN = re.compile(
    r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)"
)


def parse_silencedetect(log: str) -> list[dict[str, Any]]:
    starts = []
    pauses = []
    for line in log.splitlines():
        start_match = START_PATTERN.search(line)
        if start_match:
            starts.append(float(start_match.group(1)))
            continue
        end_match = END_PATTERN.search(line)
        if not end_match:
            continue
        end = float(end_match.group(1))
        duration = float(end_match.group(2))
        start = starts.pop(0) if starts else end - duration
        pauses.append(
            {
                "start_seconds": round(start, 6),
                "end_seconds": round(end, 6),
                "duration_seconds": round(duration, 6),
                "class": (
                    "long"
                    if duration >= 1.0
                    else "medium"
                    if duration >= 0.5
                    else "short"
                ),
            }
        )
    return pauses


def analyze_pauses(
    source: Path,
    *,
    noise_db: float = -35.0,
    minimum_duration_seconds: float = 0.3,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "info",
            "-i",
            str(source),
            "-af",
            (
                f"silencedetect=noise={noise_db}dB:"
                f"d={minimum_duration_seconds}"
            ),
            "-f",
            "null",
            "-",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "silencedetect failed")
    pauses = parse_silencedetect(completed.stderr)
    return {
        "source": str(source),
        "method": (
            f"ffmpeg silencedetect noise={noise_db}dB "
            f"minimum={minimum_duration_seconds}s"
        ),
        "pause_count": len(pauses),
        "total_pause_seconds": round(
            sum(item["duration_seconds"] for item in pauses),
            6,
        ),
        "long_pause_count": sum(item["class"] == "long" for item in pauses),
        "medium_pause_count": sum(item["class"] == "medium" for item in pauses),
        "short_pause_count": sum(item["class"] == "short" for item in pauses),
        "pauses": pauses,
        "human_review_completed": False,
    }


def extract_token_pauses(
    whisper_json: Path,
    *,
    minimum_gap_seconds: float = 0.25,
) -> dict[str, Any]:
    payload = json.loads(
        whisper_json.read_text(encoding="utf-8", errors="replace")
    )
    tokens = []
    for segment in payload.get("transcription", []):
        for token in segment.get("tokens", []):
            text = str(token.get("text", ""))
            if not re.search(r"[0-9A-Za-z\u4e00-\u9fff]", text):
                continue
            offsets = token.get("offsets", {})
            start = offsets.get("from")
            end = offsets.get("to")
            if start is None or end is None or int(end) <= int(start):
                continue
            tokens.append(
                {
                    "text": text,
                    "from_ms": int(start),
                    "to_ms": int(end),
                }
            )
    pauses = []
    for previous, current in zip(tokens, tokens[1:]):
        gap_ms = current["from_ms"] - previous["to_ms"]
        if gap_ms < minimum_gap_seconds * 1000:
            continue
        duration = gap_ms / 1000.0
        pauses.append(
            {
                "start_seconds": round(previous["to_ms"] / 1000.0, 6),
                "end_seconds": round(current["from_ms"] / 1000.0, 6),
                "duration_seconds": round(duration, 6),
                "before_text": previous["text"],
                "after_text": current["text"],
                "class": (
                    "long"
                    if duration >= 1.0
                    else "medium"
                    if duration >= 0.5
                    else "short"
                ),
            }
        )
    return {
        "source": str(whisper_json),
        "method": "whisper token timestamp gaps",
        "minimum_gap_seconds": minimum_gap_seconds,
        "token_count": len(tokens),
        "pause_count": len(pauses),
        "total_pause_seconds": round(
            sum(item["duration_seconds"] for item in pauses),
            6,
        ),
        "long_pause_count": sum(item["class"] == "long" for item in pauses),
        "medium_pause_count": sum(item["class"] == "medium" for item in pauses),
        "short_pause_count": sum(item["class"] == "short" for item in pauses),
        "pauses": pauses,
        "human_review_completed": False,
    }
