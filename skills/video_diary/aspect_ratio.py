from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.process import run_command


STANDARD_OUTPUTS = {
    "16:9": {"width": 1920, "height": 1080, "orientation": "landscape"},
    "9:16": {"width": 1080, "height": 1920, "orientation": "portrait"},
}


@dataclass(frozen=True)
class SourceGeometry:
    encoded_width: int
    encoded_height: int
    rotation_degrees: int
    sample_aspect_ratio: str
    display_width: float
    display_height: float
    display_aspect_ratio: float
    orientation: str
    inherited_output_aspect_ratio: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be a positive integer") from error
    if number <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return number


def _sample_aspect_ratio(value: Any) -> tuple[str, float]:
    text = str(value or "1:1")
    try:
        numerator_text, denominator_text = text.split(":", 1)
        numerator = float(numerator_text)
        denominator = float(denominator_text)
    except (TypeError, ValueError, ZeroDivisionError):
        return "1:1", 1.0
    if numerator <= 0 or denominator <= 0:
        return "1:1", 1.0
    return text, numerator / denominator


def _rotation(stream: dict[str, Any]) -> int:
    for side_data in stream.get("side_data_list", []):
        if "rotation" in side_data:
            try:
                return int(round(float(side_data["rotation"]))) % 360
            except (TypeError, ValueError):
                pass
    try:
        return int(round(float(stream.get("tags", {}).get("rotate", 0)))) % 360
    except (TypeError, ValueError):
        return 0


def parse_ffprobe_geometry(payload: dict[str, Any]) -> SourceGeometry:
    streams = payload.get("streams")
    if not isinstance(streams, list) or not streams:
        raise ValueError("ffprobe did not return a video stream")
    stream = streams[0]
    if not isinstance(stream, dict):
        raise ValueError("ffprobe returned an invalid video stream")

    encoded_width = _positive_integer(stream.get("width"), "video width")
    encoded_height = _positive_integer(stream.get("height"), "video height")
    sample_aspect_text, sample_aspect = _sample_aspect_ratio(
        stream.get("sample_aspect_ratio")
    )
    rotation = _rotation(stream)

    unrotated_width = encoded_width * sample_aspect
    unrotated_height = float(encoded_height)
    if rotation in {90, 270}:
        display_width = unrotated_height
        display_height = unrotated_width
    else:
        display_width = unrotated_width
        display_height = unrotated_height
    ratio = display_width / display_height
    if abs(ratio - 1.0) < 0.01:
        raise ValueError(
            "source is square or aspect ratio is ambiguous; "
            "set output_aspect_ratio explicitly"
        )
    orientation = "landscape" if ratio > 1.0 else "portrait"
    inherited = "16:9" if orientation == "landscape" else "9:16"
    return SourceGeometry(
        encoded_width=encoded_width,
        encoded_height=encoded_height,
        rotation_degrees=rotation,
        sample_aspect_ratio=sample_aspect_text,
        display_width=round(display_width, 4),
        display_height=round(display_height, 4),
        display_aspect_ratio=round(ratio, 6),
        orientation=orientation,
        inherited_output_aspect_ratio=inherited,
    )


def probe_source_geometry(
    source: Path,
    ffprobe: str = "ffprobe",
) -> SourceGeometry:
    result = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            (
                "stream=width,height,sample_aspect_ratio:"
                "stream_tags=rotate:stream_side_data=rotation"
            ),
            "-of",
            "json",
            str(source),
        ],
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"unable to inspect source aspect ratio: {result.stderr.strip()}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("ffprobe returned invalid JSON") from error
    return parse_ffprobe_geometry(payload)


def resolve_output_geometry(
    requested_aspect_ratio: str,
    source: SourceGeometry,
) -> dict[str, Any]:
    if requested_aspect_ratio == "source":
        output_aspect_ratio = source.inherited_output_aspect_ratio
        selection = "inherited_from_source"
    elif requested_aspect_ratio in STANDARD_OUTPUTS:
        output_aspect_ratio = requested_aspect_ratio
        selection = "explicit_user_override"
    else:
        raise ValueError(
            "output_aspect_ratio must be source, 16:9 or 9:16"
        )
    target = STANDARD_OUTPUTS[output_aspect_ratio]
    return {
        "policy": "inherit_source_unless_explicitly_authorized",
        "selection": selection,
        "requested_aspect_ratio": requested_aspect_ratio,
        "output_aspect_ratio": output_aspect_ratio,
        "output_width": target["width"],
        "output_height": target["height"],
        "output_orientation": target["orientation"],
        "source": source.to_dict(),
    }
