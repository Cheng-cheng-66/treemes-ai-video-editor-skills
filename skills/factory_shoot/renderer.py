from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

from PIL import ImageFont

from skills.video_diary.aspect_ratio import (
    probe_source_geometry,
    resolve_output_geometry,
)


DEFAULT_FONT = Path("/System/Library/Fonts/STHeiti Medium.ttc")
TITLE_FRAMES = 3
DEFAULT_FPS = 60
DEFAULT_DIALOGUE_CROSSFADE_SECONDS = 0.04


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip() or "command failed"
        raise RuntimeError(detail)


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _ass_time(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    whole_seconds, fraction = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{fraction:02d}"


def _ass_text(value: str) -> str:
    return (
        value.replace("\\", r"\\")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def _scaled_style(width: int, height: int) -> dict[str, int]:
    scale = height / 1920.0
    return {
        "subtitle_size": max(24, round(96 * scale)),
        "subtitle_spacing": max(1, round(4 * scale)),
        "subtitle_outline": max(2, round(7 * scale)),
        "subtitle_margin_v": max(24, round((1920 - 1280) * scale)),
        "subtitle_safe_width": round(width * 0.90),
        "title_size": max(16, round(118 * scale)),
        "title_outline": max(2, round(14 * scale)),
    }


def write_subtitles_ass(
    captions: dict[str, Any],
    output: Path,
    *,
    width: int,
    height: int,
    font_path: Path = DEFAULT_FONT,
) -> dict[str, Any]:
    if not font_path.is_file():
        raise FileNotFoundError(f"factory subtitle font not found: {font_path}")
    style = _scaled_style(width, height)
    font = ImageFont.truetype(str(font_path), style["subtitle_size"])
    width_rows = []
    overflow = 0
    for index, caption in enumerate(captions["captions"], start=1):
        measured = math.ceil(font.getlength(caption["text"]))
        measured += max(0, len(caption["text"]) - 1) * style["subtitle_spacing"]
        measured += style["subtitle_outline"] * 2
        passed = measured <= style["subtitle_safe_width"]
        overflow += int(not passed)
        width_rows.append(
            {
                "index": index,
                "text": caption["text"],
                "rendered_width_px": measured,
                "maximum_width_px": style["subtitle_safe_width"],
                "pass": passed,
            }
        )
    if overflow:
        raise ValueError(
            f"{overflow} subtitle event(s) exceed the fixed single-line safe width; "
            "split them at real speech pauses without rewriting"
        )
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Factory,Heiti SC,{style['subtitle_size']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H55000000,-1,0,0,0,100,100,{style['subtitle_spacing']},0,1,{style['subtitle_outline']},1,2,{round(width * 0.05)},{round(width * 0.05)},{style['subtitle_margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = [
        "Dialogue: 0,"
        f"{_ass_time(row['start'])},{_ass_time(row['end'])},"
        f"Factory,,0,0,0,,{_ass_text(row['text'])}"
        for row in captions["captions"]
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    _write_json(output.with_name("subtitle_width_report.json"), {"rows": width_rows, "overflow_count": 0})
    return {"style": style, "width_rows": width_rows, "overflow_count": 0}


def _base_video_filter(width: int, height: int, fps: int) -> str:
    return (
        f"fps={fps},scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    )


def _image_filter(plan: dict[str, Any]) -> str:
    treatment = plan["image_treatment"]
    filters = [
        "eq="
        f"brightness={treatment['brightness']:.4f}:"
        f"contrast={treatment['contrast']:.4f}:"
        f"saturation={treatment['saturation']:.4f}"
    ]
    if treatment["sharpen"] > 0:
        filters.append(f"unsharp=5:5:{treatment['sharpen']:.3f}:3:3:0")
    return ",".join(filters)


def _title_filters(
    plan: dict[str, Any],
    shared: Path,
    *,
    width: int,
    height: int,
    font_path: Path,
    enabled_expression: str | None,
) -> list[str]:
    style = _scaled_style(width, height)
    lines = plan["title"]["lines"]
    line_height = round(style["title_size"] * 1.18)
    center = round(height * 0.48)
    first_y = center - round((len(lines) - 1) * line_height / 2)
    colors = {"white": "0xFFFFFF", "yellow": "0xFFD900", "red": "0xFF2038"}
    filters = []
    for index, line in enumerate(lines):
        text_path = shared / f".title-line-{index + 1}.txt"
        text_path.write_text(line["text"], encoding="utf-8")
        font = ImageFont.truetype(str(font_path), style["title_size"])
        title_width = math.ceil(font.getlength(line["text"])) + style["title_outline"] * 2
        if title_width > width * 0.88:
            raise ValueError(
                f"title line exceeds safe width: {line['text']}; split it without changing meaning"
            )
        parts = [
            f"drawtext=fontfile='{_filter_path(font_path)}'",
            f"textfile='{_filter_path(text_path)}'",
            f"fontcolor={colors[line['color']]}",
            f"fontsize={style['title_size']}",
            f"borderw={style['title_outline']}",
            "bordercolor=black",
            "x=(w-text_w)/2",
            f"y={first_y + index * line_height}",
        ]
        if enabled_expression:
            parts.append(f"enable='{enabled_expression}'")
        filters.append(":".join(parts))
    return filters


def _build_picture(
    source: Path,
    plan: dict[str, Any],
    subtitles: Path,
    title: Path,
    output: Path,
    shared: Path,
    *,
    width: int,
    height: int,
    fps: int,
    font_path: Path,
    ffmpeg: str,
) -> None:
    filters = []
    labels = []
    for index, segment in enumerate(plan["picture_segments"]):
        source_range = segment["picture_source"]
        filters.append(
            f"[0:v]trim=start={source_range['start']:.6f}:end={source_range['end']:.6f},"
            f"setpts=PTS-STARTPTS,{_base_video_filter(width, height, fps)}[v{index}]"
        )
        labels.append(f"[v{index}]")
    filters.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[vconcat]")
    chain = ["[vconcat]" + _image_filter(plan)]
    chain.extend(
        _title_filters(
            plan,
            shared,
            width=width,
            height=height,
            font_path=font_path,
            enabled_expression=f"lt(n,{TITLE_FRAMES})",
        )
    )
    chain.append(
        f"ass='{_filter_path(subtitles)}':fontsdir='{_filter_path(font_path.parent)}'"
    )
    chain.append("format=yuv420p[vout]")
    filters.append(",".join(chain))
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-an",
            "-r",
            str(fps),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    first_start = plan["picture_segments"][0]["picture_source"]["start"]
    title_chain = [
        _base_video_filter(width, height, fps),
        _image_filter(plan),
        *_title_filters(
            plan,
            shared,
            width=width,
            height=height,
            font_path=font_path,
            enabled_expression=None,
        ),
    ]
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{first_start:.6f}",
            "-i",
            str(source),
            "-frames:v",
            "1",
            "-vf",
            ",".join(title_chain),
            "-threads",
            "1",
            str(title),
        ]
    )


def _audio_range_filter(label: str, start: float, end: float) -> str:
    return (
        f"[0:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS,"
        f"aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[{label}]"
    )


def _build_dialogue(
    source: Path,
    plan: dict[str, Any],
    output: Path,
    *,
    ffmpeg: str,
) -> None:
    filters = []
    segment_labels = []
    for segment_index, segment in enumerate(plan["picture_segments"]):
        range_labels = []
        ranges = segment["dialogue_source_ranges"]
        for range_index, source_range in enumerate(ranges):
            duration = source_range["end"] - source_range["start"]
            if duration <= DEFAULT_DIALOGUE_CROSSFADE_SECONDS * 2:
                raise ValueError("dialogue source ranges must be longer than 80 ms")
            label = f"d{segment_index}_{range_index}"
            filters.append(
                _audio_range_filter(label, source_range["start"], source_range["end"])
            )
            range_labels.append(f"[{label}]")
        current = range_labels[0]
        for range_index, next_label in enumerate(range_labels[1:], start=1):
            output_label = f"[dx{segment_index}_{range_index}]"
            filters.append(
                f"{current}{next_label}acrossfade=d={DEFAULT_DIALOGUE_CROSSFADE_SECONDS:.3f}:"
                f"c1=tri:c2=tri{output_label}"
            )
            current = output_label
        source_dialogue_duration = sum(
            row["end"] - row["start"] for row in ranges
        ) - DEFAULT_DIALOGUE_CROSSFADE_SECONDS * max(0, len(ranges) - 1)
        target_duration = segment["target_duration_seconds"]
        if source_dialogue_duration > target_duration + 0.02:
            raise ValueError(
                f"dialogue for {segment['id']} is longer than its picture; "
                "adjust the approved plan instead of forcing time compression"
            )
        segment_label = f"[ds{segment_index}]"
        filters.append(
            f"{current}apad,atrim=duration={target_duration:.6f},"
            f"asetpts=PTS-STARTPTS{segment_label}"
        )
        segment_labels.append(segment_label)
    filters.append(
        "".join(segment_labels)
        + f"concat=n={len(segment_labels)}:v=0:a=1,"
        "aresample=48000,aformat=sample_fmts=s32:channel_layouts=stereo[aout]"
    )
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[aout]",
            "-c:a",
            "pcm_s24le",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(output),
        ]
    )


def _build_ambience(
    source: Path,
    plan: dict[str, Any],
    output: Path,
    shared: Path,
    *,
    ffmpeg: str,
) -> None:
    ranges = plan["ambience_source_ranges"]
    filters = []
    labels = []
    for index, source_range in enumerate(ranges):
        label = f"amb{index}"
        filters.append(
            _audio_range_filter(label, source_range["start"], source_range["end"])
        )
        labels.append(f"[{label}]")
    current = labels[0]
    for index, next_label in enumerate(labels[1:], start=1):
        output_label = f"[ambx{index}]"
        filters.append(
            f"{current}{next_label}acrossfade=d=0.020:c1=tri:c2=tri{output_label}"
        )
        current = output_label
    filters.append(f"{current}highpass=f=60,lowpass=f=12000[ambout]")
    sample = shared / ".ambience-sample.wav"
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[ambout]",
            "-c:a",
            "pcm_s24le",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(sample),
        ]
    )
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-stream_loop",
            "-1",
            "-i",
            str(sample),
            "-t",
            f"{plan['final_duration_seconds']:.6f}",
            "-af",
            "afade=t=in:st=0:d=0.15,"
            f"afade=t=out:st={max(0.0, plan['final_duration_seconds'] - 0.8):.6f}:d=0.8",
            "-c:a",
            "pcm_s24le",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(output),
        ]
    )


def _build_bgm(
    bgm_source: Path | None,
    duration: float,
    output: Path,
    *,
    ffmpeg: str,
) -> None:
    if bgm_source is None:
        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=stereo",
        ]
    else:
        if not bgm_source.is_file():
            raise FileNotFoundError(f"BGM not found: {bgm_source}")
        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-stream_loop",
            "-1",
            "-i",
            str(bgm_source),
        ]
    command.extend(
        [
            "-t",
            f"{duration:.6f}",
            "-af",
            f"afade=t=in:st=0:d=0.5,afade=t=out:st={max(0.0, duration - 0.8):.6f}:d=0.8",
            "-c:a",
            "pcm_s24le",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(output),
        ]
    )
    _run(command)


def _build_preview(
    picture: Path,
    dialogue: Path,
    ambience: Path,
    bgm: Path,
    output: Path,
    *,
    duration: float,
    ffmpeg: str,
) -> None:
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(picture),
            "-i",
            str(dialogue),
            "-i",
            str(ambience),
            "-i",
            str(bgm),
            "-filter_complex",
            "[1:a]volume=0dB[d];[2:a]volume=-24dB[amb];[3:a]volume=-20dB[m];"
            "[d][amb][m]amix=inputs=3:duration=first:dropout_transition=0,"
            "loudnorm=I=-16:LRA=7:TP=-1.5[aout]",
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-t",
            f"{duration:.6f}",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def render_factory_assets(
    plan: dict[str, Any],
    captions: dict[str, Any],
    output_dir: Path,
    *,
    bgm_source: Path | None = None,
    font_path: Path = DEFAULT_FONT,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
    output_size_override: tuple[int, int] | None = None,
    fps_override: int | None = None,
) -> dict[str, Path]:
    source = Path(plan["source"]).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"factory source not found: {source}")
    if output_size_override is None:
        geometry = resolve_output_geometry(
            "source", probe_source_geometry(source, ffprobe)
        )
        width = int(geometry["output_width"])
        height = int(geometry["output_height"])
    else:
        width, height = output_size_override
    fps = int(fps_override or DEFAULT_FPS)
    if width <= 0 or height <= 0 or fps <= 0:
        raise ValueError("output geometry and fps must be positive")

    output_dir = output_dir.resolve()
    shared = output_dir / "shared"
    shared.mkdir(parents=True, exist_ok=True)
    paths = {
        "picture_master_no_audio": shared / "picture_master_no_audio.mp4",
        "dialogue_raw": shared / "dialogue_raw.wav",
        "ambience": shared / "ambience.wav",
        "bgm": shared / "bgm.wav",
        "subtitles": shared / "subtitles.ass",
        "title": shared / "title.png",
        "fallback_preview": output_dir / "fallback_preview.mp4",
        "asset_manifest": shared / "asset_manifest.json",
    }
    subtitle_metrics = write_subtitles_ass(
        captions,
        paths["subtitles"],
        width=width,
        height=height,
        font_path=font_path,
    )
    _build_picture(
        source,
        plan,
        paths["subtitles"],
        paths["title"],
        paths["picture_master_no_audio"],
        shared,
        width=width,
        height=height,
        fps=fps,
        font_path=font_path,
        ffmpeg=ffmpeg,
    )
    _build_dialogue(source, plan, paths["dialogue_raw"], ffmpeg=ffmpeg)
    _build_ambience(source, plan, paths["ambience"], shared, ffmpeg=ffmpeg)
    _build_bgm(
        bgm_source,
        plan["final_duration_seconds"],
        paths["bgm"],
        ffmpeg=ffmpeg,
    )
    _build_preview(
        paths["picture_master_no_audio"],
        paths["dialogue_raw"],
        paths["ambience"],
        paths["bgm"],
        paths["fallback_preview"],
        duration=plan["final_duration_seconds"],
        ffmpeg=ffmpeg,
    )
    _write_json(
        paths["asset_manifest"],
        {
            "schema_version": 1,
            "job_id": plan["job_id"],
            "canvas": {"width": width, "height": height, "fps": fps},
            "title_frames": TITLE_FRAMES,
            "dialogue_crossfade_ms": round(
                DEFAULT_DIALOGUE_CROSSFADE_SECONDS * 1000
            ),
            "subtitle_overflow_count": subtitle_metrics["overflow_count"],
            "bgm_source_supplied": bgm_source is not None,
            "segments": [
                {
                    "id": segment["id"],
                    "sync_zone": segment["sync_zone"],
                    "picture_source_range_count": 1,
                    "dialogue_source_range_count": len(
                        segment["dialogue_source_ranges"]
                    ),
                    "target_duration_seconds": segment[
                        "target_duration_seconds"
                    ],
                }
                for segment in plan["picture_segments"]
            ],
            "assets": {key: str(value) for key, value in paths.items() if key != "asset_manifest"},
        },
    )
    return paths
