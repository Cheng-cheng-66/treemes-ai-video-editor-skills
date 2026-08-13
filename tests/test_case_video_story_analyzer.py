import unittest

from skills.case_study.story_analyzer import analyze_story_units


class CaseVideoStoryAnalyzerTests(unittest.TestCase):
    def test_incomplete_story_cannot_pass(self):
        result = analyze_story_units(
            [
                {
                    "from_ms": 0,
                    "to_ms": 10000,
                    "text": "这是客户工厂，我们使用MES查看生产进度。",
                }
            ]
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("complete_closing", result["missing_units"])

    def test_all_story_units_require_traceable_evidence(self):
        segments = [
            {"from_ms": 0, "to_ms": 1000, "text": "这是九沣开关工厂。"},
            {"from_ms": 1000, "to_ms": 2000, "text": "以前订单容易漏单。"},
            {"from_ms": 2000, "to_ms": 3000, "text": "上线MES和三色灯。"},
            {"from_ms": 3000, "to_ms": 4000, "text": "员工报工，主管查看进度。"},
            {"from_ms": 4000, "to_ms": 5000, "text": "现在生产透明，管理得到改善。"},
            {"from_ms": 5000, "to_ms": 6000, "text": "这就是完整案例，谢谢。"},
        ]
        result = analyze_story_units(segments)
        self.assertEqual(result["status"], "complete_candidate")
        for unit in result["units"].values():
            self.assertTrue(unit["evidence"])
            self.assertFalse(unit["human_verified"])


if __name__ == "__main__":
    unittest.main()
