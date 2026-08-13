from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _frame_rate(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    numerator, denominator = value.split("/", 1)
    return float(numerator) / float(denominator)


def probe_media(path: Path, ffprobe: str = "ffprobe") -> dict[str, Any]:
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_type,codec_name,width,height,"
            "r_frame_rate,sample_rate,channels:stream_tags=rotate",
            "-of",
            "json",
            str(path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or f"ffprobe failed: {path}")
    payload = json.loads(completed.stdout)
    video_stream = next(
        stream for stream in payload["streams"] if stream["codec_type"] == "video"
    )
    audio_stream = next(
        (
            stream
            for stream in payload["streams"]
            if stream["codec_type"] == "audio"
        ),
        None,
    )
    rotation = int(video_stream.get("tags", {}).get("rotate", 0))
    width = int(video_stream["width"])
    height = int(video_stream["height"])
    if rotation % 180:
        display_width, display_height = height, width
    else:
        display_width, display_height = width, height
    return {
        "duration_seconds": round(float(payload["format"]["duration"]), 3),
        "size_bytes": int(payload["format"].get("size", path.stat().st_size)),
        "video": {
            "codec": video_stream["codec_name"],
            "width": width,
            "height": height,
            "display_width": display_width,
            "display_height": display_height,
            "rotation": rotation,
            "frame_rate": _frame_rate(video_stream.get("r_frame_rate")),
        },
        "audio": (
            {
                "codec": audio_stream["codec_name"],
                "sample_rate": int(audio_stream["sample_rate"]),
                "channels": int(audio_stream["channels"]),
            }
            if audio_stream
            else None
        ),
    }


def build_source_manifest(path: Path) -> dict[str, Any]:
    source = path.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    metadata = probe_media(source)
    return {
        "schema_version": 1,
        "path": str(source),
        "sha256": sha256_file(source),
        **metadata,
        "source_modified": False,
        "human_source_identity_reviewed": None,
    }
