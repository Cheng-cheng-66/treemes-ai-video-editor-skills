from __future__ import annotations

import wave
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
from scipy.signal import correlate


def load_mono_pcm16(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as handle:
        if handle.getnchannels() != 1 or handle.getsampwidth() != 2:
            raise ValueError("audio alignment requires mono PCM16 WAV")
        sample_rate = handle.getframerate()
        samples = np.frombuffer(
            handle.readframes(handle.getnframes()),
            dtype=np.int16,
        ).astype(np.float32)
    return sample_rate, samples


def normalized_cross_correlation_match(
    source: np.ndarray,
    reference: np.ndarray,
) -> dict[str, Any]:
    if len(reference) < 2 or len(source) < len(reference):
        raise ValueError("source must be longer than reference")
    source_feature = np.diff(source.astype(np.float32))
    reference_feature = np.diff(reference.astype(np.float32))
    source_feature -= source_feature.mean()
    reference_feature -= reference_feature.mean()
    correlation = correlate(
        source_feature,
        reference_feature,
        mode="valid",
        method="fft",
    )
    local_energy = np.convolve(
        source_feature * source_feature,
        np.ones(len(reference_feature), dtype=np.float32),
        mode="valid",
    )
    denominator = np.sqrt(
        np.maximum(local_energy, 1e-9)
        * max(float(np.sum(reference_feature * reference_feature)), 1e-9)
    )
    normalized = correlation / denominator
    best = int(np.argmax(normalized))
    return {
        "sample_offset": best,
        "score": float(normalized[best]),
    }


def _anchor_positions(start: float, end: float, window_seconds: float) -> list[float]:
    available = end - start
    if available <= window_seconds:
        return [max(start, (start + end - window_seconds) / 2)]
    first = start + 0.25 * available - window_seconds / 2
    middle = (start + end) / 2 - window_seconds / 2
    last = start + 0.75 * available - window_seconds / 2
    upper = end - window_seconds
    return [max(start, min(value, upper)) for value in (first, middle, last)]


def build_audio_anchors(
    source_wav: Path,
    reference_wav: Path,
    transcript_alignment: dict[str, Any],
    *,
    search_margin_seconds: float = 8.0,
    window_seconds: float = 2.0,
    anchor_step_seconds: float | None = None,
    downsample_factor: int = 1,
) -> dict[str, Any]:
    source_rate, source = load_mono_pcm16(source_wav)
    reference_rate, reference = load_mono_pcm16(reference_wav)
    if source_rate != reference_rate:
        raise ValueError("source and reference sample rates differ")
    if downsample_factor < 1:
        raise ValueError("downsample_factor must be positive")
    if downsample_factor > 1:
        source = source[::downsample_factor]
        reference = reference[::downsample_factor]
        source_rate //= downsample_factor
        reference_rate = source_rate
    anchors = []
    used_reference_windows: set[float] = set()
    for match_index, match in enumerate(transcript_alignment["matches"]):
        reference_start = match["reference_from_ms"] / 1000.0
        reference_end = match["reference_to_ms"] / 1000.0
        search_start = max(
            0.0,
            match["source_from_ms"] / 1000.0 - search_margin_seconds,
        )
        search_end = min(
            len(source) / source_rate,
            match["source_to_ms"] / 1000.0 + search_margin_seconds,
        )
        if anchor_step_seconds is None:
            positions = _anchor_positions(
                reference_start,
                reference_end,
                window_seconds,
            )
        else:
            positions = []
            current = reference_start
            upper = reference_end - window_seconds
            while current <= upper + 1e-9:
                positions.append(current)
                current += anchor_step_seconds
            if not positions:
                positions = _anchor_positions(
                    reference_start,
                    reference_end,
                    window_seconds,
                )
        for window_start in positions:
            dedupe_key = round(window_start, 3)
            if dedupe_key in used_reference_windows:
                continue
            used_reference_windows.add(dedupe_key)
            reference_slice = reference[
                int(window_start * reference_rate) :
                int((window_start + window_seconds) * reference_rate)
            ]
            source_slice = source[
                int(search_start * source_rate) :
                int(search_end * source_rate)
            ]
            if len(source_slice) < len(reference_slice) or len(reference_slice) < 2:
                continue
            result = normalized_cross_correlation_match(
                source_slice,
                reference_slice,
            )
            source_time = search_start + result["sample_offset"] / source_rate
            score = float(result["score"])
            anchors.append(
                {
                    "transcript_match_index": match_index,
                    "reference_start_seconds": round(window_start, 6),
                    "reference_end_seconds": round(
                        window_start + window_seconds,
                        6,
                    ),
                    "source_start_seconds": round(source_time, 6),
                    "source_end_seconds": round(source_time + window_seconds, 6),
                    "source_minus_reference_offset_seconds": round(
                        source_time - window_start,
                        6,
                    ),
                    "normalized_cross_correlation": round(score, 6),
                    "confidence": (
                        "high" if score >= 0.8 else "medium" if score >= 0.45 else "low"
                    ),
                    "human_review_required": score < 0.8,
                }
            )
    segments = group_audio_anchors(anchors)
    return {
        "schema_version": 1,
        "method": "2-second PCM waveform anchors with normalized cross-correlation",
        "source_wav": str(source_wav),
        "reference_wav": str(reference_wav),
        "sample_rate": source_rate,
        "downsample_factor": downsample_factor,
        "anchor_step_seconds": anchor_step_seconds,
        "anchor_count": len(anchors),
        "high_confidence_anchor_count": sum(
            item["confidence"] == "high" for item in anchors
        ),
        "medium_confidence_anchor_count": sum(
            item["confidence"] == "medium" for item in anchors
        ),
        "low_confidence_anchor_count": sum(
            item["confidence"] == "low" for item in anchors
        ),
        "anchors": anchors,
        "mapping_segments": segments,
        "exact_timecode_mapping_complete": False,
        "human_review_completed": False,
    }


def group_audio_anchors(
    anchors: list[dict[str, Any]],
    *,
    offset_tolerance_seconds: float = 0.35,
    maximum_reference_gap_seconds: float = 8.0,
) -> list[dict[str, Any]]:
    usable = [
        anchor
        for anchor in anchors
        if anchor["normalized_cross_correlation"] >= 0.45
    ]
    if not usable:
        return []
    usable.sort(key=lambda item: item["reference_start_seconds"])
    groups = [[usable[0]]]
    for anchor in usable[1:]:
        previous = groups[-1][-1]
        reference_gap = (
            anchor["reference_start_seconds"]
            - previous["reference_start_seconds"]
        )
        offset_change = abs(
            anchor["source_minus_reference_offset_seconds"]
            - previous["source_minus_reference_offset_seconds"]
        )
        source_progresses = (
            anchor["source_start_seconds"] >= previous["source_start_seconds"]
        )
        if (
            reference_gap <= maximum_reference_gap_seconds
            and offset_change <= offset_tolerance_seconds
            and source_progresses
        ):
            groups[-1].append(anchor)
        else:
            groups.append([anchor])
    result = []
    for index, group in enumerate(groups):
        offsets = [
            anchor["source_minus_reference_offset_seconds"]
            for anchor in group
        ]
        scores = [
            anchor["normalized_cross_correlation"]
            for anchor in group
        ]
        result.append(
            {
                "mapping_segment_index": index,
                "reference_start_seconds": group[0]["reference_start_seconds"],
                "reference_end_seconds": group[-1]["reference_end_seconds"],
                "source_start_seconds": group[0]["source_start_seconds"],
                "source_end_seconds": group[-1]["source_end_seconds"],
                "median_source_minus_reference_offset_seconds": round(
                    median(offsets),
                    6,
                ),
                "anchor_count": len(group),
                "mean_normalized_cross_correlation": round(
                    sum(scores) / len(scores),
                    6,
                ),
                "human_review_required": any(
                    anchor["human_review_required"] for anchor in group
                ),
            }
        )
    return result
