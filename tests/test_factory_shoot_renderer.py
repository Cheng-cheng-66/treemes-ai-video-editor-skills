import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from core.qc import CheckStatus, full_decode, probe_video
from skills.factory_shoot.contract import validate_captions, validate_edit_plan
from skills.factory_shoot.renderer import render_factory_assets


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FactoryShootRendererTests(unittest.TestCase):
    def test_builds_four_tracks_and_preview_with_continuous_audio_free_picture(self):
        with tempfile.TemporaryDirectory(prefix="factory-render-test-") as temp:
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
                    "testsrc2=size=270x480:rate=30:duration=4",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:sample_rate=48000:duration=4",
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
            plan = validate_edit_plan(
                {
                    "schema_version": 1,
                    "job_id": "factory_renderer_test",
                    "source": str(source),
                    "source_sha256": sha256(source),
                    "source_duration_seconds": 4.0,
                    "title": {
                        "lines": [
                            {"text": "工厂难题", "color": "yellow"},
                            {"text": "MES如何解决", "color": "white"},
                        ],
                        "approved": True,
                    },
                    "picture_segments": [
                        {
                            "id": "speaker_open",
                            "picture_source": {"start": 0.0, "end": 1.0},
                            "dialogue_source_ranges": [{"start": 0.0, "end": 1.0}],
                            "sync_zone": "A_SYNC_LOCKED",
                            "current_speaker": "speaker",
                            "visual_type": "front_speaker",
                            "mouth_visible": True,
                            "hand_action": None,
                            "next_sync_anchor": "speaker_open",
                            "edit_reason": "problem opening",
                            "risk_level": "high",
                            "confidence": 0.96,
                            "assignment_method": "automatic",
                        },
                        {
                            "id": "tablet",
                            "picture_source": {"start": 1.0, "end": 3.0},
                            "dialogue_source_ranges": [
                                {"start": 1.0, "end": 1.6},
                                {"start": 2.2, "end": 2.7},
                            ],
                            "sync_zone": "C_AUDIO_FREE",
                            "current_speaker": "speaker_voice_over",
                            "visual_type": "continuous_tablet",
                            "mouth_visible": False,
                            "hand_action": "tap",
                            "next_sync_anchor": "speaker_return",
                            "edit_reason": "show the mentioned MES operation",
                            "risk_level": "medium",
                            "confidence": 0.97,
                            "assignment_method": "automatic",
                        },
                        {
                            "id": "speaker_return",
                            "picture_source": {"start": 3.0, "end": 4.0},
                            "dialogue_source_ranges": [{"start": 3.0, "end": 4.0}],
                            "sync_zone": "A_SYNC_LOCKED",
                            "current_speaker": "speaker",
                            "visual_type": "front_speaker_return",
                            "mouth_visible": True,
                            "hand_action": None,
                            "next_sync_anchor": "speaker_return",
                            "edit_reason": "restore sync anchor",
                            "risk_level": "high",
                            "confidence": 0.96,
                            "assignment_method": "automatic",
                        },
                    ],
                    "action_anchors": [
                        {
                            "id": "tap",
                            "segment_id": "tablet",
                            "source_start": 1.3,
                            "source_end": 1.8,
                            "action": "complete tap",
                            "confidence": 0.97,
                        }
                    ],
                    "ambience_source_ranges": [{"start": 2.8, "end": 3.0}],
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
                }
            )
            captions = validate_captions(
                {
                    "schema_version": 1,
                    "source_of_truth": "final_edited_audio",
                    "captions": [
                        {"start": 0.10, "end": 0.90, "text": "如果有这些难题"},
                        {"start": 1.00, "end": 1.55, "text": "平板连续操作"},
                        {"start": 3.10, "end": 3.90, "text": "重新回到人物"},
                    ],
                    "human_review": {
                        "audio_subtitle_match_pass": None,
                        "professional_terms_pass": None,
                    },
                },
                final_duration_seconds=4.0,
            )
            outputs = render_factory_assets(
                plan,
                captions,
                root / "run",
                output_size_override=(270, 480),
                fps_override=30,
            )
            for name in (
                "picture_master_no_audio",
                "dialogue_raw",
                "ambience",
                "bgm",
                "subtitles",
                "title",
                "fallback_preview",
            ):
                self.assertTrue(outputs[name].is_file(), name)
            picture_probe = probe_video(outputs["picture_master_no_audio"])
            self.assertFalse(
                any(stream["codec_type"] == "audio" for stream in picture_probe["streams"])
            )
            preview_probe = probe_video(outputs["fallback_preview"])
            video = next(row for row in preview_probe["streams"] if row["codec_type"] == "video")
            audio = next(row for row in preview_probe["streams"] if row["codec_type"] == "audio")
            self.assertEqual((video["width"], video["height"]), (270, 480))
            self.assertEqual(audio["channels"], 2)
            self.assertEqual(full_decode(outputs["fallback_preview"]).status, CheckStatus.PASS)
            self.assertIn("平板连续操作", outputs["subtitles"].read_text(encoding="utf-8"))
            manifest = json.loads(outputs["asset_manifest"].read_text(encoding="utf-8"))
            tablet = next(row for row in manifest["segments"] if row["id"] == "tablet")
            self.assertEqual(tablet["picture_source_range_count"], 1)
            self.assertEqual(tablet["dialogue_source_range_count"], 2)


if __name__ == "__main__":
    unittest.main()
