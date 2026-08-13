from __future__ import annotations

import re
from typing import Any


REQUIRED_STORY_UNITS = (
    "customer_identity",
    "industry_and_factory_context",
    "problem_or_management_need",
    "implementation_or_usage_evidence",
    "role_specific_workflow",
    "outcome_or_management_value",
    "complete_closing",
)

REQUIRED_HUMAN_REVIEWS = (
    "transcript_pass",
    "professional_terms_pass",
    "story_pass",
    "playback_pass",
)


def validate_job_contract(payload: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version",
        "job_id",
        "source",
        "story_units",
        "human_review",
        "release_state",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"missing job fields: {', '.join(missing)}")
    if payload["schema_version"] != 1:
        raise ValueError("unsupported schema_version")
    if not str(payload["job_id"]).strip():
        raise ValueError("job_id is required")

    source = payload["source"]
    if not isinstance(source, dict):
        raise ValueError("source must be an object")
    for field in ("path", "sha256", "duration_seconds"):
        if field not in source:
            raise ValueError(f"source.{field} is required")
    if not re.fullmatch(r"[0-9a-f]{64}", str(source["sha256"])):
        raise ValueError("source.sha256 must be a lowercase SHA-256")
    if float(source["duration_seconds"]) <= 0:
        raise ValueError("source.duration_seconds must be positive")

    story_units = payload["story_units"]
    missing_story = [key for key in REQUIRED_STORY_UNITS if key not in story_units]
    if missing_story:
        raise ValueError(f"missing story units: {', '.join(missing_story)}")
    for key in REQUIRED_STORY_UNITS:
        unit = story_units[key]
        if unit.get("status") == "present" and not unit.get("evidence"):
            raise ValueError(f"story unit {key} has no evidence")

    reviews = payload["human_review"]
    missing_reviews = [key for key in REQUIRED_HUMAN_REVIEWS if key not in reviews]
    if missing_reviews:
        raise ValueError(f"missing human review fields: {', '.join(missing_reviews)}")
    if payload["release_state"] == "READY" and not all(
        reviews[key] is True for key in REQUIRED_HUMAN_REVIEWS
    ):
        raise ValueError("READY requires every human review field to pass")
    return payload
