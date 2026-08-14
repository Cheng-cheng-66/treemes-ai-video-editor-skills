import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from skills.factory_shoot.runner import FactoryRenderRequest, run


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class FactoryShootRunnerTests(unittest.TestCase):
    def test_runs_enabled_beta_workflow_and_keeps_human_gates_null(self):
        with tempfile.TemporaryDirectory(prefix="factory-runner-test-") as temp:
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
            self.assertEqual(generated.returncode, 0, generated.stderr)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            plan_path = root / "plan.json"
            captions_path = root / "captions.json"
            write_json(
                plan_path,
                {
                    "schema_version": 1,
                    "job_id": "factory_runner_test",
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
                            "edit_reason": "opening",
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
                            "edit_reason": "MES operation",
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
                            "edit_reason": "return anchor",
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
            write_json(
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
            result = run(
                FactoryRenderRequest(
                    plan=plan_path,
                    captions=captions_path,
                    output_dir=output,
                    output_size_override=(180, 320),
                    fps_override=24,
                )
            )
            self.assertTrue(result["fallback_preview"].is_file())
            self.assertTrue((output / "shared/picture_master_no_audio.mp4").is_file())
            self.assertTrue((output / "visual_analysis.json").is_file())
            quality = json.loads((output / "quality_report.json").read_text(encoding="utf-8"))
            self.assertEqual(quality["automatic_status"], "PASS")
            self.assertTrue(quality["rendered_beta_candidate"])
            self.assertTrue(quality["manual_review_required"])
            self.assertFalse(quality["release_complete"])
            self.assertIsNone(quality["audio_subtitle_mismatch_count"])
            jianying = json.loads(
                (output / "jianying_import_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(jianying["tracks"]["V1"], "shared/picture_master_no_audio.mp4")
            self.assertFalse(jianying["native_export_completed"])


if __name__ == "__main__":
    unittest.main()
