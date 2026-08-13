import unittest

from skills.case_study.edit_planner import validate_edit_plan


class CaseVideoEditPlanTests(unittest.TestCase):
    def test_every_action_requires_reason_and_evidence(self):
        plan = {
            "source": "/tmp/source.mp4",
            "source_sha256": "a" * 64,
            "actions": [
                {
                    "source_start_seconds": 0.0,
                    "source_end_seconds": 10.0,
                    "operation": "keep",
                    "story_unit": "customer_identity",
                    "sync_zone": "A_SYNC_LOCKED",
                    "reason": "",
                    "evidence": [],
                    "risk": "low",
                    "confidence": 0.9,
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "reason"):
            validate_edit_plan(plan)

    def test_action_locked_cannot_be_trimmed_internally(self):
        plan = {
            "source": "/tmp/source.mp4",
            "source_sha256": "a" * 64,
            "actions": [
                {
                    "source_start_seconds": 5.0,
                    "source_end_seconds": 8.0,
                    "operation": "trim_inside",
                    "story_unit": "implementation_or_usage_evidence",
                    "sync_zone": "D_ACTION_LOCKED",
                    "reason": "压缩动作",
                    "evidence": ["source:5-8"],
                    "risk": "high",
                    "confidence": 0.8,
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "D_ACTION_LOCKED"):
            validate_edit_plan(plan)


if __name__ == "__main__":
    unittest.main()
