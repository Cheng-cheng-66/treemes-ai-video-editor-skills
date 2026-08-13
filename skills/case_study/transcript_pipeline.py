from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


PROFESSIONAL_TERMS = (
    "智能三色灯",
    "三色灯",
    "交通灯协议",
    "绕过每个设备协议",
    "设备协议",
    "MES",
    "安灯系统",
    "标工基建",
    "计件工资",
    "客户报价",
    "员工激励机制",
    "工价",
    "电子作业指导书",
    "生产看板",
)


def normalize_spoken_text(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", text).lower()


def professional_term_flags(text: str) -> list[dict[str, Any]]:
    found: list[tuple[int, str]] = []
    occupied: list[tuple[int, int]] = []
    for term in PROFESSIONAL_TERMS:
        start = text.find(term)
        if start < 0:
            continue
        end = start + len(term)
        if any(start >= left and end <= right for left, right in occupied):
            continue
        found.append((start, term))
        occupied.append((start, end))
    return [
        {
            "term": term,
            "character_offset": offset,
            "human_review_required": True,
            "automatic_rewrite_allowed": False,
        }
        for offset, term in sorted(found)
    ]


def load_whisper_segments(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    result = []
    for segment in payload.get("transcription", []):
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        offsets = segment.get("offsets", {})
        result.append(
            {
                "from_ms": int(offsets.get("from", 0)),
                "to_ms": int(offsets.get("to", 0)),
                "text": text,
                "professional_term_flags": professional_term_flags(text),
                "human_reviewed": False,
            }
        )
    return result


def _similarity(left: str, right: str) -> float:
    normalized_left = normalize_spoken_text(left)
    normalized_right = normalize_spoken_text(right)
    if not normalized_left or not normalized_right:
        return 0.0
    sequence = _partial_ratio(normalized_left, normalized_right)
    left_bigrams = {
        normalized_left[index : index + 2]
        for index in range(max(1, len(normalized_left) - 1))
    }
    right_bigrams = {
        normalized_right[index : index + 2]
        for index in range(max(1, len(normalized_right) - 1))
    }
    union = left_bigrams | right_bigrams
    jaccard = len(left_bigrams & right_bigrams) / len(union) if union else 0.0
    return 0.7 * sequence + 0.3 * jaccard


def _partial_ratio(left: str, right: str) -> float:
    if len(left) > len(right):
        left, right = right, left
    if not left:
        return 0.0
    if left in right:
        return 1.0
    matcher = SequenceMatcher(None, left, right)
    best = 0.0
    for block in matcher.get_matching_blocks():
        start = max(0, block.b - block.a)
        window = right[start : start + len(left)]
        best = max(best, SequenceMatcher(None, left, window).ratio())
        if best >= 0.995:
            break
    return best


def align_transcript_segments(
    source_segments: list[dict[str, Any]],
    reference_segments: list[dict[str, Any]],
) -> dict[str, Any]:
    matches = []
    for reference_index, reference in enumerate(reference_segments):
        ranked = sorted(
            (
                (
                    _similarity(reference["text"], source["text"]),
                    source_index,
                    source,
                )
                for source_index, source in enumerate(source_segments)
            ),
            reverse=True,
            key=lambda item: item[0],
        )
        score, source_index, source = ranked[0]
        matches.append(
            {
                "reference_segment_index": reference_index,
                "reference_from_ms": reference["from_ms"],
                "reference_to_ms": reference["to_ms"],
                "reference_text": reference["text"],
                "source_segment_index": source_index,
                "source_from_ms": source["from_ms"],
                "source_to_ms": source["to_ms"],
                "source_text": source["text"],
                "text_similarity": round(score, 6),
                "confidence": (
                    "high" if score >= 0.7 else "medium" if score >= 0.45 else "low"
                ),
                "human_review_required": score < 0.7,
            }
        )
    indices = [item["source_segment_index"] for item in matches]
    reordering = any(right < left for left, right in zip(indices, indices[1:]))
    return {
        "schema_version": 1,
        "matches": matches,
        "reordering_detected": reordering,
        "high_confidence_count": sum(
            item["confidence"] == "high" for item in matches
        ),
        "medium_confidence_count": sum(
            item["confidence"] == "medium" for item in matches
        ),
        "low_confidence_count": sum(
            item["confidence"] == "low" for item in matches
        ),
        "human_review_completed": False,
    }


def chunk_segments(
    segments: list[dict[str, Any]],
    *,
    target_duration_ms: int = 12000,
    minimum_characters: int = 24,
) -> list[dict[str, Any]]:
    chunks = []
    current: list[tuple[int, dict[str, Any]]] = []
    for index, segment in enumerate(segments):
        current.append((index, segment))
        duration = current[-1][1]["to_ms"] - current[0][1]["from_ms"]
        text = "".join(item["text"] for _, item in current)
        if duration < target_duration_ms or len(normalize_spoken_text(text)) < minimum_characters:
            continue
        chunks.append(
            {
                "start_segment_index": current[0][0],
                "end_segment_index": current[-1][0],
                "from_ms": current[0][1]["from_ms"],
                "to_ms": current[-1][1]["to_ms"],
                "text": text,
            }
        )
        current = []
    if current:
        text = "".join(item["text"] for _, item in current)
        chunks.append(
            {
                "start_segment_index": current[0][0],
                "end_segment_index": current[-1][0],
                "from_ms": current[0][1]["from_ms"],
                "to_ms": current[-1][1]["to_ms"],
                "text": text,
            }
        )
    return chunks


def align_transcript_chunks(
    source_segments: list[dict[str, Any]],
    reference_segments: list[dict[str, Any]],
    *,
    max_source_window_ms: int = 26000,
) -> dict[str, Any]:
    def chunk_similarity(reference_text: str, source_text: str) -> float:
        base = _similarity(reference_text, source_text)
        reference_length = len(normalize_spoken_text(reference_text))
        source_length = len(normalize_spoken_text(source_text))
        if reference_length == 0:
            return 0.0
        source_coverage = min(1.0, source_length / reference_length)
        return base * source_coverage**0.5

    reference_chunks = chunk_segments(reference_segments)
    source_windows = []
    for start_index, start in enumerate(source_segments):
        text_parts = []
        for end_index in range(start_index, min(len(source_segments), start_index + 6)):
            end = source_segments[end_index]
            duration = end["to_ms"] - start["from_ms"]
            if duration > max_source_window_ms and end_index > start_index:
                break
            text_parts.append(end["text"])
            source_windows.append(
                {
                    "start_segment_index": start_index,
                    "end_segment_index": end_index,
                    "from_ms": start["from_ms"],
                    "to_ms": end["to_ms"],
                    "text": "".join(text_parts),
                }
            )

    matches = []
    for reference_index, reference in enumerate(reference_chunks):
        ranked = sorted(
            (
                (chunk_similarity(reference["text"], source["text"]), source)
                for source in source_windows
            ),
            reverse=True,
            key=lambda item: item[0],
        )
        score, source = ranked[0]
        matches.append(
            {
                "reference_segment_index": reference_index,
                "reference_source_segment_start": reference["start_segment_index"],
                "reference_source_segment_end": reference["end_segment_index"],
                "reference_from_ms": reference["from_ms"],
                "reference_to_ms": reference["to_ms"],
                "reference_text": reference["text"],
                "source_segment_index": source["start_segment_index"],
                "source_segment_end_index": source["end_segment_index"],
                "source_from_ms": source["from_ms"],
                "source_to_ms": source["to_ms"],
                "source_text": source["text"],
                "text_similarity": round(score, 6),
                "confidence": (
                    "high" if score >= 0.72 else "medium" if score >= 0.48 else "low"
                ),
                "human_review_required": score < 0.72,
            }
        )
    indices = [item["source_segment_index"] for item in matches]
    return {
        "schema_version": 1,
        "method": "12-second reference chunks against 1-to-6 source segment windows",
        "matches": matches,
        "reordering_detected": any(
            right < left for left, right in zip(indices, indices[1:])
        ),
        "high_confidence_count": sum(
            item["confidence"] == "high" for item in matches
        ),
        "medium_confidence_count": sum(
            item["confidence"] == "medium" for item in matches
        ),
        "low_confidence_count": sum(
            item["confidence"] == "low" for item in matches
        ),
        "human_review_completed": False,
    }
