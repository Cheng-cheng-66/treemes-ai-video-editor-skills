from __future__ import annotations

import re
from typing import Any


SYNC_ZONES = {
    "A_SYNC_LOCKED",
    "B_SYNC_FLEX",
    "C_AUDIO_FREE",
    "D_ACTION_LOCKED",
}


def validate_edit_plan(plan: dict[str, Any]) -> dict[str, Any]:
    for field in ("source", "source_sha256", "actions"):
        if field not in plan:
            raise ValueError(f"{field} is required")
    if not re.fullmatch(r"[0-9a-f]{64}", str(plan["source_sha256"])):
        raise ValueError("source_sha256 must be a lowercase SHA-256")
    if not isinstance(plan["actions"], list) or not plan["actions"]:
        raise ValueError("actions must be a non-empty list")
    for index, action in enumerate(plan["actions"]):
        label = f"actions[{index}]"
        required = (
            "source_start_seconds",
            "source_end_seconds",
            "operation",
            "story_unit",
            "sync_zone",
            "reason",
            "evidence",
            "risk",
            "confidence",
        )
        for field in required:
            if field not in action:
                raise ValueError(f"{label}.{field} is required")
        if float(action["source_end_seconds"]) <= float(
            action["source_start_seconds"]
        ):
            raise ValueError(f"{label} has invalid time range")
        if action["sync_zone"] not in SYNC_ZONES:
            raise ValueError(f"{label} has invalid sync_zone")
        if not str(action["reason"]).strip():
            raise ValueError(f"{label}.reason is required")
        if not action["evidence"]:
            raise ValueError(f"{label}.evidence is required")
        if (
            action["sync_zone"] == "D_ACTION_LOCKED"
            and action["operation"] == "trim_inside"
        ):
            raise ValueError("D_ACTION_LOCKED cannot be trimmed internally")
        confidence = float(action["confidence"])
        if not 0 <= confidence <= 1:
            raise ValueError(f"{label}.confidence must be between 0 and 1")
    return plan
