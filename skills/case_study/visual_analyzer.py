from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


FONT = Path("/System/Library/Fonts/STHeiti Medium.ttc")


def sample_timestamps(duration_seconds: float, count: int = 20) -> list[float]:
    if count <= 0:
        raise ValueError("count must be positive")
    return [
        duration_seconds * (index + 0.5) / count
        for index in range(count)
    ]


def extract_frame(
    source: Path,
    timestamp_seconds: float,
    output: Path,
    *,
    width: int = 216,
    height: int = 384,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp_seconds:.3f}",
            "-i",
            str(source),
            "-frames:v",
            "1",
            "-vf",
            (
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
            ),
            "-q:v",
            "3",
            str(output),
        ],
        check=False,
        capture_output=True,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode(errors="replace").strip())
    return output


def build_contact_sheet(
    source: Path,
    duration_seconds: float,
    output: Path,
    *,
    frame_dir: Path,
    count: int = 20,
) -> dict[str, Any]:
    timestamps = sample_timestamps(duration_seconds, count)
    width, height, label_height = 216, 384, 34
    columns = 4
    rows = (count + columns - 1) // columns
    title_height = 76
    title_font = ImageFont.truetype(str(FONT), 25)
    label_font = ImageFont.truetype(str(FONT), 19)
    sheet = Image.new(
        "RGB",
        (columns * width, title_height + rows * (height + label_height)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (16, 18),
        f"{source.name}｜{duration_seconds / 60:.2f} min｜机器抽样预览",
        font=title_font,
        fill="black",
    )
    frames = []
    for index, timestamp in enumerate(timestamps):
        frame = frame_dir / f"{index:02d}_{timestamp:09.3f}.jpg"
        if not frame.is_file():
            extract_frame(source, timestamp, frame, width=width, height=height)
        frames.append(frame)
        image = Image.open(frame).convert("RGB")
        column = index % columns
        row = index // columns
        x = column * width
        y = title_height + row * (height + label_height)
        sheet.paste(image, (x, y))
        draw.rectangle(
            (x, y + height, x + width, y + height + label_height),
            fill=(20, 20, 20),
        )
        minute = int(timestamp // 60)
        second = timestamp - minute * 60
        draw.text(
            (x + 8, y + height + 5),
            f"{minute:02d}:{second:04.1f}",
            font=label_font,
            fill="white",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=91, optimize=True)
    return {
        "source": str(source),
        "duration_seconds": duration_seconds,
        "sample_count": count,
        "timestamps_seconds": [round(value, 3) for value in timestamps],
        "frames": [str(path) for path in frames],
        "contact_sheet": str(output),
        "machine_sample_only": True,
        "human_visual_review_pass": None,
    }


def detect_scene_changes(
    source: Path,
    *,
    threshold: float = 0.32,
    sample_fps: int = 5,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "info",
            "-i",
            str(source),
            "-vf",
            (
                f"fps={sample_fps},scale=270:-2,"
                f"select='gt(scene,{threshold})',showinfo"
            ),
            "-an",
            "-f",
            "null",
            "-",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "scene detection failed")
    times = []
    for line in completed.stderr.splitlines():
        marker = "pts_time:"
        if marker not in line:
            continue
        value = line.split(marker, 1)[1].split()[0]
        try:
            times.append(round(float(value), 3))
        except ValueError:
            continue
    return {
        "method": f"ffmpeg scene>{threshold} at {sample_fps}fps proxy",
        "estimated_scene_change_times_seconds": times,
        "estimated_cut_count": len(times),
        "manual_cut_review_completed": False,
    }
