#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.qc import CheckStatus, full_decode
from skills.factory_shoot.runner import FactoryRenderRequest, run


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="factory-shoot-smoke-") as temp:
        root = Path(temp)
        source = root / "source.mp4"
        generated = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=180x320:rate=24:duration=2",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=330:sample_rate=48000:duration=2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                str(source),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if generated.returncode != 0:
            print(f"FAIL: synthetic factory input generation - {generated.stderr.strip()}")
            return 1

        plan_path = root / "edit_plan.json"
        captions_path = root / "captions.json"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        _write_json(
            plan_path,
            {
                "schema_version": 1,
                "job_id": "factory_smoke",
                "source": str(source),
                "source_sha256": digest,
                "source_duration_seconds": 2.0,
                "title": {
                    "lines": [
                        {"text": "工厂现场", "color": "yellow"},
                        {"text": "MES解决方案", "color": "white"},
                    ],
                    "approved": True,
                },
                "picture_segments": [
                    {
                        "id": "a1",
                        "picture_source": {"start": 0.0, "end": 0.5},
                        "dialogue_source_ranges": [{"start": 0.0, "end": 0.5}],
                        "sync_zone": "A_SYNC_LOCKED",
                        "current_speaker": "speaker",
                        "visual_type": "front_speaker",
                        "mouth_visible": True,
                        "hand_action": None,
                        "next_sync_anchor": "a1",
                        "edit_reason": "opening sync anchor",
                        "risk_level": "high",
                        "confidence": 0.96,
                        "assignment_method": "automatic",
                    },
                    {
                        "id": "c1",
                        "picture_source": {"start": 0.5, "end": 1.5},
                        "dialogue_source_ranges": [
                            {"start": 0.5, "end": 0.9},
                            {"start": 1.1, "end": 1.4},
                        ],
                        "sync_zone": "C_AUDIO_FREE",
                        "current_speaker": "speaker_voice_over",
                        "visual_type": "tablet",
                        "mouth_visible": False,
                        "hand_action": "tap",
                        "next_sync_anchor": "a2",
                        "edit_reason": "compress dialogue while keeping the operation continuous",
                        "risk_level": "medium",
                        "confidence": 0.97,
                        "assignment_method": "automatic",
                    },
                    {
                        "id": "a2",
                        "picture_source": {"start": 1.5, "end": 2.0},
                        "dialogue_source_ranges": [{"start": 1.5, "end": 2.0}],
                        "sync_zone": "A_SYNC_LOCKED",
                        "current_speaker": "speaker",
                        "visual_type": "front_speaker_return",
                        "mouth_visible": True,
                        "hand_action": None,
                        "next_sync_anchor": "a2",
                        "edit_reason": "restore exact lip sync",
                        "risk_level": "high",
                        "confidence": 0.96,
                        "assignment_method": "automatic",
                    },
                ],
                "action_anchors": [
                    {
                        "id": "tap1",
                        "segment_id": "c1",
                        "source_start": 0.7,
                        "source_end": 1.0,
                        "action": "complete tap",
                        "confidence": 0.97,
                    }
                ],
                "ambience_source_ranges": [{"start": 1.4, "end": 1.5}],
                "image_treatment": {
                    "brightness": 0.0,
                    "contrast": 1.0,
                    "saturation": 1.0,
                    "sharpen": 0.0,
                },
                "human_review": {
                    "transcript_pass": None,
                    "professional_terms_pass": None,
                    "story_pass": None,
                    "playback_pass": None,
                },
            },
        )
        _write_json(
            captions_path,
            {
                "schema_version": 1,
                "source_of_truth": "final_edited_audio",
                "captions": [
                    {"start": 0.1, "end": 0.4, "text": "工厂现场"},
                    {"start": 0.55, "end": 0.85, "text": "平板操作"},
                    {"start": 1.6, "end": 1.9, "text": "回到人物"},
                ],
                "human_review": {
                    "audio_subtitle_match_pass": None,
                    "professional_terms_pass": None,
                },
            },
        )

        output = root / "run"
        try:
            result = run(
                FactoryRenderRequest(
                    plan=plan_path,
                    captions=captions_path,
                    output_dir=output,
                    output_size_override=(180, 320),
                    fps_override=24,
                )
            )
            quality = json.loads(
                result["quality_report"].read_text(encoding="utf-8")
            )
            if quality["automatic_status"] != "PASS":
                print(f"FAIL: factory automatic QC - {quality}")
                return 2
            if quality["audio_subtitle_mismatch_count"] is not None:
                print("FAIL: listening-review field was fabricated")
                return 3
            decoded = full_decode(result["technical_preview"])
            if decoded.status != CheckStatus.PASS:
                print(f"FAIL: factory preview decode - {decoded.detail}")
                return 4
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            print(f"FAIL: factory smoke render - {exc}")
            return 5

    print(
        "PASS: factory A_SYNC_LOCKED -> C_AUDIO_FREE -> A_SYNC_LOCKED "
        "sample rendered, QC checked and fully decoded"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
