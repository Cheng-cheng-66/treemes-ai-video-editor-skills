from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def classify_face_state(
    face_boxes: list[tuple[int, int, int, int]],
    frame_width: int,
    frame_height: int,
) -> dict[str, Any]:
    if not face_boxes:
        return {
            "sync_zone": "C_AUDIO_FREE",
            "mouth_visibility_candidate": False,
            "confidence": 0.7,
            "reason": "no frontal face detected in sampled frame",
        }
    largest = max(face_boxes, key=lambda box: box[2] * box[3])
    x, y, width, height = largest
    area_ratio = width * height / (frame_width * frame_height)
    center_x = x + width / 2
    safely_centered = frame_width * 0.08 <= center_x <= frame_width * 0.92
    if area_ratio >= 0.035 and safely_centered:
        return {
            "sync_zone": "A_SYNC_LOCKED",
            "mouth_visibility_candidate": True,
            "confidence": min(0.92, 0.7 + area_ratio),
            "reason": "large frontal face detected",
        }
    return {
        "sync_zone": "B_SYNC_FLEX",
        "mouth_visibility_candidate": False,
        "confidence": 0.62,
        "reason": "face detected but small or near frame edge",
    }


def merge_samples(
    samples: list[dict[str, Any]],
    *,
    sample_interval_seconds: float,
) -> list[dict[str, Any]]:
    if not samples:
        return []
    zones = []
    current = [samples[0]]
    for sample in samples[1:]:
        if sample["sync_zone"] == current[-1]["sync_zone"]:
            current.append(sample)
            continue
        zones.append(_zone_from_samples(current, sample_interval_seconds))
        current = [sample]
    zones.append(_zone_from_samples(current, sample_interval_seconds))
    return zones


def _zone_from_samples(
    samples: list[dict[str, Any]],
    interval: float,
) -> dict[str, Any]:
    return {
        "start_seconds": samples[0]["time_seconds"],
        "end_seconds": samples[-1]["time_seconds"] + interval,
        "sync_zone": samples[0]["sync_zone"],
        "mean_confidence": round(
            sum(float(item["confidence"]) for item in samples) / len(samples),
            4,
        ),
        "sample_count": len(samples),
        "machine_candidate_only": True,
        "human_reviewed": False,
    }


def analyze_sync_zones(
    source: Path,
    duration_seconds: float,
    *,
    sample_fps: float = 1.0,
    frame_width: int = 270,
    frame_height: int = 480,
    model_path: Path | None = None,
) -> dict[str, Any]:
    selected_model = model_path or (
        Path(__file__).resolve().parents[2]
        / "var/models/face_detection_yunet_2026may.onnx"
    )
    if not selected_model.is_file():
        raise FileNotFoundError(
            f"YuNet face detector is required for sync-zone analysis: {selected_model}"
        )
    detector = cv2.FaceDetectorYN.create(
        str(selected_model),
        "",
        (frame_width, frame_height),
        0.72,
        0.3,
        5000,
    )
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-vf",
        (
            f"fps={sample_fps},scale={frame_width}:{frame_height}:"
            "force_original_aspect_ratio=decrease,"
            f"pad={frame_width}:{frame_height}:(ow-iw)/2:(oh-ih)/2:black"
        ),
        "-pix_fmt",
        "bgr24",
        "-f",
        "rawvideo",
        "-",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    frame_bytes = frame_width * frame_height * 3
    samples = []
    index = 0
    while True:
        raw = process.stdout.read(frame_bytes)
        if len(raw) < frame_bytes:
            break
        frame = np.frombuffer(raw, dtype=np.uint8).reshape(
            (frame_height, frame_width, 3)
        )
        _, detections = detector.detect(frame)
        faces = [] if detections is None else detections[:, :4]
        state = classify_face_state(
            [tuple(int(value) for value in box) for box in faces],
            frame_width,
            frame_height,
        )
        samples.append(
            {
                "time_seconds": round(index / sample_fps, 3),
                **state,
            }
        )
        index += 1
    stderr = process.stderr.read().decode(errors="replace") if process.stderr else ""
    returncode = process.wait()
    if returncode:
        raise RuntimeError(stderr.strip() or "sync-zone frame extraction failed")
    interval = 1.0 / sample_fps
    return {
        "schema_version": 1,
        "source": str(source),
        "duration_seconds": duration_seconds,
        "sample_fps": sample_fps,
        "samples": samples,
        "zones": merge_samples(samples, sample_interval_seconds=interval),
        "d_action_locked_automatic_detection": False,
        "warning": (
            "Face detection supplies sync-zone candidates only. "
            "D_ACTION_LOCKED and visible mouth state require manual confirmation."
        ),
        "human_review_completed": False,
    }


def write_sync_zones(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
