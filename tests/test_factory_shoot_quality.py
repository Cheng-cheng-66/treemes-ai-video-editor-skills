import tempfile
import unittest
from pathlib import Path

from skills.factory_shoot.quality import (
    PROTECTED_HUMAN_FIELDS,
    build_human_review_report,
    write_planning_artifacts,
)
from tests.test_factory_shoot_contract import valid_captions, valid_plan
from skills.factory_shoot.contract import validate_captions, validate_edit_plan


class FactoryShootQualityTests(unittest.TestCase):
    def test_human_review_fields_remain_null_before_real_listening(self):
        plan = validate_edit_plan(valid_plan())
        captions = validate_captions(
            valid_captions(), final_duration_seconds=plan["final_duration_seconds"]
        )
        report = build_human_review_report(plan, captions)
        self.assertEqual(report["review_status"], "NOT_REVIEWED")
        for field in PROTECTED_HUMAN_FIELDS:
            self.assertIsNone(report["whole_video"][field], field)
        for row in report["sentence_rows"]:
            self.assertIsNone(row["actual_dialogue"])
            self.assertIsNone(row["subtitle_matches_dialogue"])

    def test_writes_all_required_planning_artifacts(self):
        plan = validate_edit_plan(valid_plan())
        captions = validate_captions(
            valid_captions(), final_duration_seconds=plan["final_duration_seconds"]
        )
        with tempfile.TemporaryDirectory(prefix="factory-quality-test-") as temp:
            paths = write_planning_artifacts(plan, captions, Path(temp))
            for name in (
                "visual_analysis",
                "transcript",
                "sync_zones",
                "edit_plan",
                "continuity_report",
                "action_anchors",
                "human_review",
            ):
                self.assertTrue(paths[name].is_file(), name)
            sync = paths["sync_zones"].read_text(encoding="utf-8")
            self.assertIn("C_AUDIO_FREE", sync)
            self.assertIn("speaker_return", sync)


if __name__ == "__main__":
    unittest.main()
