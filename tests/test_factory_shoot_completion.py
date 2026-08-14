import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from skills.factory_shoot.completion import (
    PROTECTED_HUMAN_FIELDS,
    REQUIRED_SCREENSHOTS,
    REQUIRED_UI_EVENTS,
    finalize_factory_export,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class FactoryShootCompletionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="factory-completion-")
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.shared = self.run / "shared"
        self.shared.mkdir(parents=True)
        self.export = self.root / "jianying_export.mp4"
        created = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=180x320:rate=24:duration=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000:duration=1",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                str(self.export),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(created.returncode, 0, created.stderr)
        (self.shared / "picture_master_no_audio.mp4").write_bytes(
            self.export.read_bytes()
        )
        (self.shared / "subtitles.ass").write_text(
            "[Events]\nDialogue: 0,0:00:00.00,0:00:00.90,Factory,,0,0,0,,字幕\n",
            encoding="utf-8",
        )
        write_json(
            self.run / "quality_report.json",
            {
                "schema_version": 1,
                "job_id": "completion_test",
                "automatic_status": "PASS",
                "caption_count": 1,
                "release_complete": False,
            },
        )
        self.screenshots = self.run / "jianying" / "screenshots"
        self.screenshots.mkdir(parents=True)
        for name in REQUIRED_SCREENSHOTS:
            (self.screenshots / f"{name}.png").write_bytes(b"evidence")
        self.ui_log = self.run / "jianying" / "ui_action_log.json"
        write_json(
            self.ui_log,
            {
                "schema_version": 1,
                "application_bundle_id": "com.lemon.lvpro",
                "application_version": "7.9.0",
                "events": [
                    {"id": event, "status": "confirmed"}
                    for event in REQUIRED_UI_EVENTS
                ],
                "screenshots": {
                    name: str(self.screenshots / f"{name}.png")
                    for name in REQUIRED_SCREENSHOTS
                },
            },
        )
        self.review = self.run / "human_listening_review.json"
        whole_video = {
            field: (0 if field.endswith("_count") else True)
            for field in PROTECTED_HUMAN_FIELDS
        }
        write_json(
            self.review,
            {
                "schema_version": 1,
                "review_status": "PASS",
                "reviewer": "human",
                "reviewed_at": "2026-08-14T12:00:00+08:00",
                "sentence_rows": [
                    {
                        "index": 1,
                        "subtitle": "字幕",
                        "actual_dialogue": "字幕",
                        "subtitle_matches_dialogue": True,
                        "professional_terms_correct": True,
                        "word_loss": False,
                        "visible_lip_sync_pass": True,
                        "notes": "",
                    }
                ],
                "whole_video": whole_video,
            },
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_complete_requires_all_evidence_and_updates_quality(self):
        result = finalize_factory_export(
            output_dir=self.run,
            export=self.export,
            ui_log=self.ui_log,
            human_review=self.review,
        )
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["final_video"], self.export.resolve())
        quality = json.loads(
            (self.run / "quality_report.json").read_text(encoding="utf-8")
        )
        self.assertTrue(quality["release_complete"])
        self.assertTrue(quality["jianying_audio_processing_completed"])
        self.assertFalse(quality["manual_review_required"])

    def test_missing_native_denoise_evidence_blocks_completion(self):
        payload = json.loads(self.ui_log.read_text(encoding="utf-8"))
        payload["events"] = [
            row for row in payload["events"] if row["id"] != "native_denoise_enabled"
        ]
        write_json(self.ui_log, payload)
        with self.assertRaisesRegex(ValueError, "native_denoise_enabled"):
            finalize_factory_export(
                output_dir=self.run,
                export=self.export,
                ui_log=self.ui_log,
                human_review=self.review,
            )

    def test_unreviewed_sentence_blocks_completion(self):
        payload = json.loads(self.review.read_text(encoding="utf-8"))
        payload["sentence_rows"][0]["subtitle_matches_dialogue"] = None
        write_json(self.review, payload)
        with self.assertRaisesRegex(ValueError, "subtitle_matches_dialogue"):
            finalize_factory_export(
                output_dir=self.run,
                export=self.export,
                ui_log=self.ui_log,
                human_review=self.review,
            )

    def test_missing_burned_subtitles_blocks_completion(self):
        (self.shared / "subtitles.ass").write_text("[Events]\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "subtitle"):
            finalize_factory_export(
                output_dir=self.run,
                export=self.export,
                ui_log=self.ui_log,
                human_review=self.review,
            )


if __name__ == "__main__":
    unittest.main()
