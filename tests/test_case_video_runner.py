import unittest

import tempfile
from pathlib import Path

from skills.case_study.runner import (
    build_job_contract,
    transcription_cache_key,
)


class CaseVideoRunnerTests(unittest.TestCase):
    def test_analysis_contract_is_not_release_ready(self):
        units = {
            key: {
                "status": "present",
                "evidence": [{"from_ms": 0, "to_ms": 1000, "text": key}],
                "human_verified": False,
            }
            for key in (
                "customer_identity",
                "industry_and_factory_context",
                "problem_or_management_need",
                "implementation_or_usage_evidence",
                "role_specific_workflow",
                "outcome_or_management_value",
                "complete_closing",
            )
        }
        contract = build_job_contract(
            "case_test",
            {
                "path": "/tmp/source.mp4",
                "sha256": "a" * 64,
                "duration_seconds": 600.0,
            },
            {"units": units},
        )
        self.assertEqual(contract["release_state"], "ANALYSIS")
        self.assertTrue(
            all(value is None for value in contract["human_review"].values())
        )

    def test_transcription_cache_changes_when_prompt_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model = Path(temp_dir) / "model.bin"
            model.write_bytes(b"model")
            first = transcription_cache_key(
                source_sha256="a" * 64,
                audio_size_bytes=123,
                model=model,
                initial_prompt="MES系统",
            )
            second = transcription_cache_key(
                source_sha256="a" * 64,
                audio_size_bytes=123,
                model=model,
                initial_prompt="MES系统，三色灯",
            )
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
