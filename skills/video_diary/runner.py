from __future__ import annotations

import json
import os
import platform
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import AppConfig, create_runtime_dirs, load_config
from core.process import executable_path, run_command
from skills.video_diary.aspect_ratio import (
    probe_source_geometry,
    resolve_output_geometry,
)
from skills.video_diary.quality import write_quality_report


REVIEW_STATUSES = {"NOT_REVIEWED", "PASS", "FAIL", "NOT_APPLICABLE"}
IMAGE_TREATMENT_MODES = {"none", "dark", "low_contrast", "noisy"}
AUDIO_CLASSES = {"A", "B", "C", "D"}
BGM_MODES = {"default", "off", "custom"}
OUTPUT_ASPECT_RATIO_MODES = {"source", "16:9", "9:16"}


@dataclass(frozen=True)
class RenderRequest:
    plan: Path
    captions: Path
    output: Path
    date: str
    day: str
    template_only: bool = False

    def validate_metadata(self) -> None:
        if re.fullmatch(r"\d{4}/\d{2}/\d{2}", self.date) is None:
            raise ValueError("date must use YYYY/MM/DD")
        if re.fullmatch(r"Day\d+", self.day) is None:
            raise ValueError("day must use Day<number>")


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _review_status(value: Any, field: str) -> str:
    if value not in REVIEW_STATUSES:
        allowed = ", ".join(sorted(REVIEW_STATUSES))
        raise ValueError(f"{field} must be one of: {allowed}")
    return str(value)


def validate_edit_plan(value: Any) -> dict[str, Any]:
    """Validate and normalize the release-scoped video diary decisions."""
    if not isinstance(value, dict):
        raise ValueError("edit plan must be a JSON object")
    plan = deepcopy(value)

    _required_text(plan.get("source"), "source")
    duration = plan.get("source_duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        raise ValueError("source_duration_seconds must be a positive number")
    if float(duration) <= 0:
        raise ValueError("source_duration_seconds must be a positive number")
    plan["source_duration_seconds"] = float(duration)
    plan["title"] = _required_text(plan.get("title"), "title")

    output_aspect_ratio = plan.get("output_aspect_ratio", "source")
    if output_aspect_ratio not in OUTPUT_ASPECT_RATIO_MODES:
        raise ValueError(
            "output_aspect_ratio must be source, 16:9 or 9:16"
        )
    if output_aspect_ratio != "source":
        if plan.get("aspect_ratio_override_authorized") is not True:
            raise ValueError(
                "explicit aspect-ratio conversion requires "
                "aspect_ratio_override_authorized=true"
            )
        _required_text(
            plan.get("aspect_ratio_override_reason"),
            "aspect_ratio_override_reason",
        )
    plan["output_aspect_ratio"] = output_aspect_ratio

    title_lines = plan.get("cover_title_lines")
    if title_lines is not None:
        if (
            not isinstance(title_lines, list)
            or not 1 <= len(title_lines) <= 2
            or not all(
                isinstance(line, str) and line.strip() for line in title_lines
            )
        ):
            raise ValueError(
                "cover_title_lines must contain one or two non-empty lines"
            )
        plan["cover_title_lines"] = [line.strip() for line in title_lines]

    speed = plan.get("speed", 1.0)
    if isinstance(speed, bool) or not isinstance(speed, (int, float)):
        raise ValueError("speed must be a number")
    speed = float(speed)
    if not 1.0 <= speed <= 1.08:
        raise ValueError("speed must be between 1.00 and 1.08")
    if speed > 1.0:
        assessment = plan.get("speed_assessment")
        if not isinstance(assessment, dict):
            raise ValueError(
                "speed_assessment is required when speed is above 1.00"
            )
        for field in ("original_pace", "post_cut_pace", "reason"):
            _required_text(
                assessment.get(field),
                f"speed_assessment.{field}",
            )
    plan["speed"] = speed

    remove = plan.get("remove", [])
    if not isinstance(remove, list):
        raise ValueError("remove must be a list")
    previous_end = 0.0
    normalized_remove: list[dict[str, Any]] = []
    for index, cut in enumerate(remove, start=1):
        if not isinstance(cut, dict):
            raise ValueError(f"remove[{index}] must be an object")
        start = cut.get("start")
        end = cut.get("end")
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, (int, float))
            or not isinstance(end, (int, float))
        ):
            raise ValueError(f"remove[{index}] start/end must be numbers")
        start_number = float(start)
        end_number = float(end)
        if (
            start_number < previous_end
            or start_number < 0
            or end_number <= start_number
            or end_number > plan["source_duration_seconds"]
        ):
            raise ValueError(
                f"remove[{index}] must be ordered and within source duration"
            )
        normalized_remove.append(
            {
                **cut,
                "start": start_number,
                "end": end_number,
                "reason": _required_text(
                    cut.get("reason"),
                    f"remove[{index}].reason",
                ),
            }
        )
        previous_end = end_number
    plan["remove"] = normalized_remove

    image = plan.get("image_treatment")
    if not isinstance(image, dict):
        raise ValueError("image_treatment decision is required")
    image_mode = image.get("mode")
    if image_mode not in IMAGE_TREATMENT_MODES:
        raise ValueError(
            "image_treatment.mode must be none, dark, low_contrast or noisy"
        )
    _required_text(image.get("reason"), "image_treatment.reason")
    _review_status(
        image.get("manual_visual_review"),
        "image_treatment.manual_visual_review",
    )

    audio = plan.get("audio_treatment")
    if not isinstance(audio, dict):
        raise ValueError("audio_treatment decision is required")
    if audio.get("class") not in AUDIO_CLASSES:
        raise ValueError("audio_treatment.class must be A, B, C or D")
    _required_text(audio.get("reason"), "audio_treatment.reason")
    _review_status(
        audio.get("manual_listening_review"),
        "audio_treatment.manual_listening_review",
    )

    bgm_mode = plan.get("bgm_mode", "default")
    if bgm_mode not in BGM_MODES:
        raise ValueError("bgm_mode must be default, off or custom")
    if bgm_mode == "custom":
        _required_text(plan.get("bgm_path"), "bgm_path")
        if plan.get("bgm_authorization_status") != "CONFIRMED":
            raise ValueError(
                "custom BGM requires bgm_authorization_status=CONFIRMED"
            )
    plan["bgm_mode"] = bgm_mode
    return plan


def _font_profile(config: AppConfig) -> dict[str, str]:
    profile = str(config.video_diary.get("font_profile", "auto"))
    if profile == "auto":
        profile = "windows" if platform.system() == "Windows" else "macos"
    profiles = config.video_diary.get("fonts", {})
    fonts = profiles.get(profile)
    if not isinstance(fonts, dict):
        raise ValueError(f"font profile is not configured: {profile}")
    return {str(key): str(value) for key, value in fonts.items()}


def build_renderer_environment(
    config: AppConfig,
    request: RenderRequest,
    output_geometry: dict[str, Any] | None = None,
) -> dict[str, str]:
    request.validate_metadata()
    fonts = _font_profile(config)
    environment = dict(os.environ)
    video_cache = config.paths.cache_dir / "video_diary"
    template_dir = config.paths.output_dir / "video_diary" / "templates"
    report_dir = config.paths.logs_dir / "video_diary"
    bgm = config.video_diary.get("bgm", {})
    if not isinstance(bgm, dict):
        raise ValueError("video_diary.bgm must be an object")
    jianying_audio = config.video_diary.get("jianying_audio", {})
    if not isinstance(jianying_audio, dict):
        raise ValueError("video_diary.jianying_audio must be an object")
    bgm_path = str(bgm.get("path", "")).strip()
    if bgm_path:
        candidate = Path(bgm_path).expanduser()
        if not candidate.is_absolute():
            candidate = config.project_root / candidate
        bgm_path = str(candidate.resolve())
    environment.update(
        {
            "VIDEO_DIARY_DATE": request.date,
            "VIDEO_DIARY_DAY": request.day,
            "VIDEO_DIARY_WORK_DIR": str(video_cache),
            "VIDEO_DIARY_TEMPLATE_DIR": str(template_dir),
            "VIDEO_DIARY_WIDTH_REPORT": str(
                report_dir / "subtitle_width_report.json"
            ),
            "VIDEO_DIARY_FONT_SUBTITLE": fonts["subtitle"],
            "VIDEO_DIARY_FONT_COVER_TITLE": fonts["cover_title"],
            "VIDEO_DIARY_FONT_LATIN_BOLD": fonts["latin_bold"],
            "VIDEO_DIARY_FONT_DATE": fonts["date"],
            "VIDEO_DIARY_FONT_DAY": fonts["day"],
            "VIDEO_DIARY_FONT_MICRO": fonts["micro"],
            "VIDEO_DIARY_DEFAULT_BGM_PATH": bgm_path,
            "VIDEO_DIARY_DEFAULT_BGM_PROVIDER": str(
                bgm.get("provider", "local")
            ),
            "VIDEO_DIARY_DEFAULT_BGM_MATERIAL_ID": str(
                bgm.get("material_id", "")
            ),
            "VIDEO_DIARY_DEFAULT_BGM_AUTHORIZATION": str(
                bgm.get("authorization_status", "NOT_CONFIRMED")
            ),
            "VIDEO_DIARY_DEFAULT_BGM_NAME": str(
                bgm.get("name", "UNASSIGNED")
            ),
            "VIDEO_DIARY_JIANYING_VOICE_SEPARATION_ENABLED": (
                "1"
                if jianying_audio.get("voice_separation_enabled", False)
                else "0"
            ),
            "VIDEO_DIARY_JIANYING_VOICE_SEPARATION_MODE": str(
                jianying_audio.get("voice_separation_mode", "disabled")
            ),
            "VIDEO_DIARY_JIANYING_VOICE_VOLUME_DB": str(
                jianying_audio.get("voice_volume_db", 0.0)
            ),
            "VIDEO_DIARY_JIANYING_BGM_VOLUME_DB": str(
                bgm.get("jianying_initial_volume_db", 0.0)
            ),
        }
    )
    if output_geometry is not None:
        environment.update(
            {
                "VIDEO_DIARY_ASPECT_RATIO_POLICY": str(
                    output_geometry["policy"]
                ),
                "VIDEO_DIARY_ASPECT_RATIO_SELECTION": str(
                    output_geometry["selection"]
                ),
                "VIDEO_DIARY_OUTPUT_ASPECT_RATIO": str(
                    output_geometry["output_aspect_ratio"]
                ),
                "VIDEO_DIARY_OUTPUT_WIDTH": str(
                    output_geometry["output_width"]
                ),
                "VIDEO_DIARY_OUTPUT_HEIGHT": str(
                    output_geometry["output_height"]
                ),
                "VIDEO_DIARY_SOURCE_ORIENTATION": str(
                    output_geometry["source"]["orientation"]
                ),
                "VIDEO_DIARY_SOURCE_DISPLAY_ASPECT_RATIO": str(
                    output_geometry["source"]["display_aspect_ratio"]
                ),
                "VIDEO_DIARY_SOURCE_ROTATION_DEGREES": str(
                    output_geometry["source"]["rotation_degrees"]
                ),
            }
        )
    if request.template_only:
        environment["VIDEO_DIARY_TEMPLATE_ONLY"] = "1"
    return environment


def render(
    request: RenderRequest,
    config: AppConfig | None = None,
) -> Path:
    active = config or load_config()
    create_runtime_dirs(active)
    request.validate_metadata()
    if not request.plan.is_file():
        raise FileNotFoundError(f"edit plan not found: {request.plan}")
    if not request.captions.is_file():
        raise FileNotFoundError(f"captions not found: {request.captions}")
    plan = validate_edit_plan(
        json.loads(request.plan.read_text(encoding="utf-8"))
    )
    source = Path(str(plan.get("source", ""))).expanduser()
    if not request.template_only and not source.is_file():
        raise FileNotFoundError(f"source media not found: {source}")
    output_geometry: dict[str, Any] | None = None
    if not request.template_only:
        source_geometry = probe_source_geometry(
            source,
            str(active.video_diary.get("ffprobe_command", "ffprobe")),
        )
        output_geometry = resolve_output_geometry(
            str(plan["output_aspect_ratio"]),
            source_geometry,
        )

    node = str(active.video_diary.get("node_command", "node"))
    if executable_path(node) is None:
        raise RuntimeError(f"Node.js command not found: {node}")
    renderer = active.project_root / str(active.video_diary["renderer"])
    if not renderer.is_file():
        raise FileNotFoundError(f"video diary renderer not found: {renderer}")

    request.output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        node,
        str(renderer),
        str(request.plan.resolve()),
        str(request.captions.resolve()),
        str(request.output.resolve()),
    ]
    result = run_command(
        command,
        cwd=active.project_root,
        environment=build_renderer_environment(
            active,
            request,
            output_geometry,
        ),
        timeout=None,
    )
    log_dir = active.paths.logs_dir / "video_diary"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / (
        "render-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
    )
    log_path.write_text(
        "\n".join(
            [
                f"command={command!r}",
                f"returncode={result.returncode}",
                "[stdout]",
                result.stdout,
                "[stderr]",
                result.stderr,
            ]
        ),
        encoding="utf-8",
    )
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        if len(detail) > 50:
            tail = "\n".join(detail[:20] + ["..."] + detail[-30:])
        else:
            tail = "\n".join(detail) if detail else "no stderr output"
        raise RuntimeError(
            f"video diary render failed; see {log_path}\n{tail}"
        )
    if not request.template_only:
        write_quality_report(
            plan=plan,
            output=request.output,
            ffmpeg=str(active.video_diary.get("ffmpeg_command", "ffmpeg")),
            ffprobe=str(
                active.video_diary.get("ffprobe_command", "ffprobe")
            ),
            expected_geometry=output_geometry,
        )
    return request.output
