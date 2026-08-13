from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def build_filter_complex(
    segments: list[dict[str, Any]],
) -> tuple[str, str, str]:
    if not segments:
        raise ValueError("at least one segment is required")
    filters = []
    concat_inputs = []
    for index, segment in enumerate(segments):
        start = float(segment["source_start_seconds"])
        end = float(segment["source_end_seconds"])
        if end <= start:
            raise ValueError(f"segment {index} has invalid time range")
        filters.append(
            f"[0:v]trim=start={start:.3f}:end={end:.3f},"
            f"setpts=PTS-STARTPTS[v{index}]"
        )
        filters.append(
            f"[0:a]atrim=start={start:.3f}:end={end:.3f},"
            f"asetpts=PTS-STARTPTS[a{index}]"
        )
        concat_inputs.append(f"[v{index}][a{index}]")
    filters.append(
        "".join(concat_inputs)
        + f"concat=n={len(segments)}:v=1:a=1[vout][aout]"
    )
    return ";".join(filters), "[vout]", "[aout]"


def render_segments(
    source: Path,
    segments: list[dict[str, Any]],
    output: Path,
    *,
    ffmpeg: str = "ffmpeg",
    video_codec: str = "h264_videotoolbox",
) -> Path:
    filters, video_label, audio_label = build_filter_complex(segments)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-i",
        str(source),
        "-filter_complex",
        filters,
        "-map",
        video_label,
        "-map",
        audio_label,
        "-c:v",
        video_codec,
        "-b:v",
        "10M",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "case render failed")
    return output
