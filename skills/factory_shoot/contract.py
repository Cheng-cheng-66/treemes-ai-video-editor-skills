from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


VALID_ZONES = {
    "A_SYNC_LOCKED",
    "B_SYNC_FLEX",
    "C_AUDIO_FREE",
    "D_ACTION_LOCKED",
}
AUTOMATIC_CONFIDENCE_MINIMUM = {
    "A_SYNC_LOCKED": 0.92,
    "B_SYNC_FLEX": 0.88,
    "C_AUDIO_FREE": 0.94,
    "D_ACTION_LOCKED": 0.95,
}
RISK_LEVELS = {"low", "medium", "high"}
REVIEW_FIELDS = {
    "transcript_pass",
    "professional_terms_pass",
    "story_pass",
    "playback_pass",
}


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    return float(value)


def _range(value: Any, field: str, source_duration: float) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    start = _number(value.get("start"), f"{field}.start")
    end = _number(value.get("end"), f"{field}.end")
    if start < 0 or end <= start or end > source_duration + 1e-6:
        raise ValueError(f"{field} must be ordered and within source duration")
    return {"start": start, "end": end}


def _validate_review(value: Any, fields: set[str], label: str) -> dict[str, bool | None]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    normalized: dict[str, bool | None] = {}
    for field in fields:
        answer = value.get(field)
        if answer is not None and not isinstance(answer, bool):
            raise ValueError(f"{label}.{field} must be true, false or null")
        normalized[field] = answer
    return normalized


def validate_edit_plan(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("factory edit plan must be a JSON object")
    plan = deepcopy(value)
    if plan.get("schema_version") != 1:
        raise ValueError("schema_version must equal 1")
    plan["job_id"] = _required_text(plan.get("job_id"), "job_id")
    plan["source"] = _required_text(plan.get("source"), "source")
    source_hash = _required_text(plan.get("source_sha256"), "source_sha256").lower()
    if re.fullmatch(r"[0-9a-f]{64}", source_hash) is None:
        raise ValueError("source_sha256 must be a lowercase SHA-256 hex digest")
    plan["source_sha256"] = source_hash
    source_duration = _number(
        plan.get("source_duration_seconds"), "source_duration_seconds"
    )
    if source_duration <= 0:
        raise ValueError("source_duration_seconds must be positive")
    plan["source_duration_seconds"] = source_duration

    title = plan.get("title")
    if not isinstance(title, dict):
        raise ValueError("title must be an object")
    if title.get("approved") is not True:
        raise ValueError("title.approved must be true before rendering")
    lines = title.get("lines")
    if not isinstance(lines, list) or not 1 <= len(lines) <= 3:
        raise ValueError("title.lines must contain one to three lines")
    normalized_lines = []
    for index, line in enumerate(lines, start=1):
        if not isinstance(line, dict):
            raise ValueError(f"title.lines[{index}] must be an object")
        color = line.get("color", "white")
        if color not in {"white", "yellow", "red"}:
            raise ValueError(f"title.lines[{index}].color is invalid")
        normalized_lines.append(
            {
                "text": _required_text(line.get("text"), f"title.lines[{index}].text"),
                "color": color,
            }
        )
    if sum(line["color"] == "red" for line in normalized_lines) > 1:
        raise ValueError("title permits at most one red emphasis line")
    plan["title"] = {**title, "lines": normalized_lines, "approved": True}

    segments = plan.get("picture_segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("picture_segments must be a non-empty list")
    normalized_segments: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for index, segment in enumerate(segments, start=1):
        label = f"picture_segments[{index}]"
        if not isinstance(segment, dict):
            raise ValueError(f"{label} must be an object")
        segment_id = _required_text(segment.get("id"), f"{label}.id")
        if segment_id in identifiers:
            raise ValueError(f"duplicate segment id: {segment_id}")
        identifiers.add(segment_id)
        picture = _range(segment.get("picture_source"), f"{label}.picture_source", source_duration)
        zone = segment.get("sync_zone")
        if zone not in VALID_ZONES:
            raise ValueError(f"{label}.sync_zone is invalid")
        confidence = _number(segment.get("confidence"), f"{label}.confidence")
        if not 0 < confidence <= 1:
            raise ValueError(f"{label}.confidence must be within (0, 1]")
        assignment = segment.get("assignment_method")
        if assignment not in {"automatic", "manual"}:
            raise ValueError(f"{label}.assignment_method must be automatic or manual")
        if assignment == "automatic" and confidence < AUTOMATIC_CONFIDENCE_MINIMUM[zone]:
            raise ValueError(f"{label}.confidence is below the automatic threshold for {zone}")
        dialogue = segment.get("dialogue_source_ranges")
        if not isinstance(dialogue, list) or not dialogue:
            raise ValueError(f"{label}.dialogue_source_ranges must be non-empty")
        normalized_dialogue = []
        previous_end = -1.0
        for range_index, source_range in enumerate(dialogue, start=1):
            normalized_range = _range(
                source_range,
                f"{label}.dialogue_source_ranges[{range_index}]",
                source_duration,
            )
            if normalized_range["start"] < previous_end - 1e-6:
                raise ValueError(f"{label}.dialogue_source_ranges must be ordered")
            previous_end = normalized_range["end"]
            normalized_dialogue.append(normalized_range)
        if zone == "A_SYNC_LOCKED" and (
            len(normalized_dialogue) != 1
            or abs(normalized_dialogue[0]["start"] - picture["start"]) > 1e-6
            or abs(normalized_dialogue[0]["end"] - picture["end"]) > 1e-6
        ):
            raise ValueError(
                f"{label} A_SYNC_LOCKED picture and dialogue must use the identical range"
            )
        mouth_visible = segment.get("mouth_visible")
        if not isinstance(mouth_visible, bool):
            raise ValueError(f"{label}.mouth_visible must be boolean")
        if zone == "A_SYNC_LOCKED" and not mouth_visible:
            raise ValueError(f"{label} A_SYNC_LOCKED requires visible mouth")
        if zone == "C_AUDIO_FREE" and mouth_visible:
            raise ValueError(f"{label} C_AUDIO_FREE requires mouth_visible=false")
        risk = segment.get("risk_level")
        if risk not in RISK_LEVELS:
            raise ValueError(f"{label}.risk_level is invalid")
        hand_action = segment.get("hand_action")
        if hand_action is not None:
            hand_action = _required_text(hand_action, f"{label}.hand_action")
        next_anchor = segment.get("next_sync_anchor")
        if next_anchor is not None:
            next_anchor = _required_text(next_anchor, f"{label}.next_sync_anchor")
        normalized_segments.append(
            {
                **segment,
                "id": segment_id,
                "picture_source": picture,
                "dialogue_source_ranges": normalized_dialogue,
                "sync_zone": zone,
                "current_speaker": _required_text(
                    segment.get("current_speaker"), f"{label}.current_speaker"
                ),
                "visual_type": _required_text(
                    segment.get("visual_type"), f"{label}.visual_type"
                ),
                "mouth_visible": mouth_visible,
                "hand_action": hand_action,
                "next_sync_anchor": next_anchor,
                "edit_reason": _required_text(
                    segment.get("edit_reason"), f"{label}.edit_reason"
                ),
                "risk_level": risk,
                "confidence": confidence,
                "assignment_method": assignment,
                "target_duration_seconds": picture["end"] - picture["start"],
            }
        )

    by_id = {segment["id"]: index for index, segment in enumerate(normalized_segments)}
    for index, segment in enumerate(normalized_segments):
        future_a = next(
            (
                candidate["id"]
                for candidate in normalized_segments[index + 1 :]
                if candidate["sync_zone"] == "A_SYNC_LOCKED"
            ),
            None,
        )
        anchor = segment["next_sync_anchor"]
        if anchor is not None and anchor not in by_id:
            raise ValueError(f"{segment['id']}.next_sync_anchor does not exist")
        if segment["sync_zone"] == "B_SYNC_FLEX" and future_a is None:
            raise ValueError(f"{segment['id']} B_SYNC_FLEX requires a future A sync anchor")
        if future_a is not None and segment["sync_zone"] in {
            "B_SYNC_FLEX",
            "C_AUDIO_FREE",
            "D_ACTION_LOCKED",
        }:
            if anchor != future_a:
                raise ValueError(
                    f"{segment['id']}.next_sync_anchor must identify the next A_SYNC_LOCKED segment"
                )

    anchors = plan.get("action_anchors", [])
    if not isinstance(anchors, list):
        raise ValueError("action_anchors must be a list")
    normalized_anchors = []
    for index, anchor in enumerate(anchors, start=1):
        label = f"action_anchors[{index}]"
        if not isinstance(anchor, dict):
            raise ValueError(f"{label} must be an object")
        segment_id = _required_text(anchor.get("segment_id"), f"{label}.segment_id")
        if segment_id not in by_id:
            raise ValueError(f"{label} references an unknown segment")
        segment = normalized_segments[by_id[segment_id]]
        start = _number(anchor.get("source_start"), f"{label}.source_start")
        end = _number(anchor.get("source_end"), f"{label}.source_end")
        picture = segment["picture_source"]
        if start < picture["start"] - 1e-6 or end > picture["end"] + 1e-6 or end <= start:
            raise ValueError(f"{label} action anchor must stay inside one continuous picture segment")
        confidence = _number(anchor.get("confidence"), f"{label}.confidence")
        if not 0 < confidence <= 1:
            raise ValueError(f"{label}.confidence must be within (0, 1]")
        normalized_anchors.append(
            {
                **anchor,
                "id": _required_text(anchor.get("id"), f"{label}.id"),
                "segment_id": segment_id,
                "source_start": start,
                "source_end": end,
                "action": _required_text(anchor.get("action"), f"{label}.action"),
                "confidence": confidence,
            }
        )
    for segment in normalized_segments:
        if segment["sync_zone"] == "D_ACTION_LOCKED" and not any(
            anchor["segment_id"] == segment["id"] for anchor in normalized_anchors
        ):
            raise ValueError(f"D_ACTION_LOCKED segment {segment['id']} requires an action anchor")

    ambience = plan.get("ambience_source_ranges")
    if not isinstance(ambience, list) or not ambience:
        raise ValueError("ambience_source_ranges must contain verified speech-free ranges")
    plan["ambience_source_ranges"] = [
        _range(source_range, f"ambience_source_ranges[{index}]", source_duration)
        for index, source_range in enumerate(ambience, start=1)
    ]

    image = plan.get("image_treatment")
    if not isinstance(image, dict):
        raise ValueError("image_treatment must be an object")
    normalized_image = {}
    ranges = {
        "brightness": (-0.10, 0.10),
        "contrast": (0.85, 1.20),
        "saturation": (0.85, 1.20),
        "sharpen": (0.0, 1.0),
    }
    for field, (minimum, maximum) in ranges.items():
        number = _number(image.get(field), f"image_treatment.{field}")
        if not minimum <= number <= maximum:
            raise ValueError(f"image_treatment.{field} is outside the safe range")
        normalized_image[field] = number
    plan["image_treatment"] = normalized_image
    plan["human_review"] = _validate_review(
        plan.get("human_review"), REVIEW_FIELDS, "human_review"
    )
    plan["picture_segments"] = normalized_segments
    plan["action_anchors"] = normalized_anchors
    plan["final_duration_seconds"] = round(
        sum(segment["target_duration_seconds"] for segment in normalized_segments),
        6,
    )
    return plan


def validate_captions(value: Any, *, final_duration_seconds: float) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("captions must be a JSON object")
    captions = deepcopy(value)
    if captions.get("schema_version") != 1:
        raise ValueError("captions.schema_version must equal 1")
    if captions.get("source_of_truth") != "final_edited_audio":
        raise ValueError("captions.source_of_truth must be final_edited_audio")
    rows = captions.get("captions")
    if not isinstance(rows, list) or not rows:
        raise ValueError("captions.captions must be a non-empty list")
    normalized = []
    previous_end = 0.0
    for index, row in enumerate(rows, start=1):
        label = f"captions[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{label} must be an object")
        start = _number(row.get("start"), f"{label}.start")
        end = _number(row.get("end"), f"{label}.end")
        text = _required_text(row.get("text"), f"{label}.text")
        if "\n" in text or "\r" in text:
            raise ValueError(f"{label} must be single-line")
        if start < previous_end - 1e-6 or start < 0 or end <= start:
            raise ValueError(f"{label} must be ordered and non-overlapping")
        if end > final_duration_seconds + 1e-6:
            raise ValueError(f"{label} exceeds the final timeline")
        normalized.append({**row, "start": start, "end": end, "text": text})
        previous_end = end
    captions["captions"] = normalized
    captions["human_review"] = _validate_review(
        captions.get("human_review"),
        {"audio_subtitle_match_pass", "professional_terms_pass"},
        "captions.human_review",
    )
    return captions
