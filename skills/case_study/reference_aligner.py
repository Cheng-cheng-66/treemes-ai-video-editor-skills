from __future__ import annotations

from typing import Any

from skills.case_study.transcript_pipeline import align_transcript_chunks


def cluster_alignment(
    alignment: dict[str, Any],
    *,
    source_gap_seconds: float = 8.0,
    reference_gap_seconds: float = 4.0,
) -> list[dict[str, Any]]:
    matches = alignment["matches"]
    if not matches:
        return []
    clusters: list[list[dict[str, Any]]] = []
    current = [matches[0]]
    for match in matches[1:]:
        previous = current[-1]
        source_gap = (
            match["source_from_ms"] - previous["source_to_ms"]
        ) / 1000.0
        reference_gap = (
            match["reference_from_ms"] - previous["reference_to_ms"]
        ) / 1000.0
        same_direction = (
            match["source_segment_index"] >= previous["source_segment_index"]
        )
        if (
            same_direction
            and source_gap <= source_gap_seconds
            and reference_gap <= reference_gap_seconds
        ):
            current.append(match)
        else:
            clusters.append(current)
            current = [match]
    clusters.append(current)

    result = []
    for index, cluster in enumerate(clusters):
        scores = [float(item["text_similarity"]) for item in cluster]
        source_start = min(item["source_from_ms"] for item in cluster) / 1000.0
        source_end = max(item["source_to_ms"] for item in cluster) / 1000.0
        reference_start = (
            min(item["reference_from_ms"] for item in cluster) / 1000.0
        )
        reference_end = max(item["reference_to_ms"] for item in cluster) / 1000.0
        result.append(
            {
                "cluster_index": index,
                "source_start_seconds": round(source_start, 3),
                "source_end_seconds": round(source_end, 3),
                "reference_start_seconds": round(reference_start, 3),
                "reference_end_seconds": round(reference_end, 3),
                "match_count": len(cluster),
                "mean_text_similarity": round(sum(scores) / len(scores), 6),
                "low_confidence_match_count": sum(
                    item["confidence"] == "low" for item in cluster
                ),
                "source_segment_indices": [
                    item["source_segment_index"] for item in cluster
                ],
                "reference_segment_indices": [
                    item["reference_segment_index"] for item in cluster
                ],
                "human_review_required": any(
                    item["human_review_required"] for item in cluster
                ),
            }
        )
    return result


def align_reference_to_source(
    source_segments: list[dict[str, Any]],
    reference_segments: list[dict[str, Any]],
) -> dict[str, Any]:
    alignment = align_transcript_chunks(source_segments, reference_segments)
    clusters = cluster_alignment(alignment)
    return {
        **alignment,
        "clusters": clusters,
        "exact_audio_alignment_completed": False,
        "exact_visual_alignment_completed": False,
        "safe_for_automatic_render": False,
    }
