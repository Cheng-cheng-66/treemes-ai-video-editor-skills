import json
import unittest
from pathlib import Path

from skills.case_study.contract import validate_job_contract


ROOT = Path(__file__).resolve().parents[1]


class CaseVideoJobContractTests(unittest.TestCase):
    def test_schema_requires_source_story_review_and_release_state(self):
        schema = json.loads(
            (ROOT / "schemas/case_video_job.schema.json").read_text(encoding="utf-8")
        )
        required = set(schema["required"])
        self.assertTrue(
            {
                "job_id",
                "source",
                "story_units",
                "human_review",
                "release_state",
            }.issubset(required)
        )

    def test_unreviewed_human_fields_cannot_be_release_ready(self):
        payload = {
            "schema_version": 1,
            "job_id": "case_test",
            "source": {
                "path": "/tmp/source.mp4",
                "sha256": "a" * 64,
                "duration_seconds": 600.0,
            },
            "story_units": {
                key: {"status": "present", "evidence": ["source:0-10"]}
                for key in (
                    "customer_identity",
                    "industry_and_factory_context",
                    "problem_or_management_need",
                    "implementation_or_usage_evidence",
                    "role_specific_workflow",
                    "outcome_or_management_value",
                    "complete_closing",
                )
            },
            "human_review": {
                "transcript_pass": None,
                "professional_terms_pass": None,
                "story_pass": None,
                "playback_pass": None,
            },
            "release_state": "READY",
        }
        with self.assertRaisesRegex(ValueError, "human review"):
            validate_job_contract(payload)


if __name__ == "__main__":
    unittest.main()
