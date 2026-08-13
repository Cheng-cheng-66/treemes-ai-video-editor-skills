from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESET = ROOT / "presets/case_video"
REFERENCES = ROOT / "references/case_video"


class CaseVideoPresetTests(unittest.TestCase):
    def test_required_preset_files_exist(self) -> None:
        required = {
            "README.md",
            "editorial.yaml",
            "sync_rules.yaml",
            "subtitle.yaml",
            "title.yaml",
            "audio.yaml",
            "quality_rules.yaml",
            "professional_terms.yaml",
        }
        self.assertEqual(
            required,
            {path.name for path in PRESET.iterdir() if path.is_file()},
        )

    def test_editorial_is_long_form_and_evidence_grounded(self) -> None:
        text = (PRESET / "editorial.yaml").read_text(encoding="utf-8")
        self.assertIn("content_type: long_form_customer_case", text)
        self.assertIn("content_completeness_before_duration: true", text)
        self.assertIn("invent_customer_claims: false", text)
        self.assertIn("number_requires_explicit_source: true", text)

    def test_subtitles_are_verbatim(self) -> None:
        text = (PRESET / "subtitle.yaml").read_text(encoding="utf-8")
        self.assertIn("source_of_truth: final_audio", text)
        self.assertIn("verbatim_required: true", text)
        self.assertIn("paraphrase: false", text)
        self.assertIn("shorten_professional_term: false", text)

    def test_case_title_has_no_persistent_header(self) -> None:
        text = (PRESET / "title.yaml").read_text(encoding="utf-8")
        self.assertIn("default_frames: 3", text)
        self.assertIn("persistent_header: false", text)

    def test_human_review_fields_default_to_null(self) -> None:
        text = (PRESET / "quality_rules.yaml").read_text(encoding="utf-8")
        self.assertIn("audio_subtitle_mismatch_count: null", text)
        self.assertIn("customer_claim_accuracy_pass: null", text)
        self.assertIn("final_case_story_pass: null", text)
        self.assertIn("technical_qc_alone_is_release_ready: false", text)

    @unittest.skipUnless(
        (REFERENCES / "library_inventory.json").is_file(),
        "private case reference inventory is not distributed",
    )
    def test_library_inventory_and_candidate_counts(self) -> None:
        inventory = json.loads(
            (REFERENCES / "library_inventory.json").read_text(
                encoding="utf-8",
            ),
        )
        summary = json.loads(
            (REFERENCES / "classification_summary.json").read_text(
                encoding="utf-8",
            ),
        )
        golden = json.loads(
            (REFERENCES / "golden_set_v0.json").read_text(
                encoding="utf-8",
            ),
        )
        self.assertEqual(249, inventory["observed_media_count"])
        self.assertEqual(0, inventory["probe_failure_count"])
        self.assertEqual(
            55,
            summary["full_case_golden_candidate_count"],
        )
        self.assertEqual(11, len(golden["candidates"]))

    @unittest.skipUnless(
        (REFERENCES / "transcripts/transcripts.json").is_file(),
        "private case reference transcripts are not distributed",
    )
    def test_all_reference_transcriptions_completed(self) -> None:
        transcripts = json.loads(
            (
                REFERENCES / "transcripts/transcripts.json"
            ).read_text(encoding="utf-8"),
        )
        self.assertEqual("transcription_complete", transcripts["status"])
        self.assertEqual(11, transcripts["completed_count"])
        self.assertEqual(0, transcripts["failure_count"])
        self.assertTrue(
            all(
                item["asr_human_reviewed"] is False
                for item in transcripts["items"]
            ),
        )


if __name__ == "__main__":
    unittest.main()
