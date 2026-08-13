import unittest

from skills.case_study.transcript_pipeline import (
    align_transcript_segments,
    normalize_spoken_text,
    professional_term_flags,
)


class CaseVideoTranscriptPipelineTests(unittest.TestCase):
    def test_normalization_does_not_replace_spoken_words(self):
        original = "智能三色灯通过交通灯协议，绕过每个设备协议。"
        normalized = normalize_spoken_text(original)
        self.assertIn("智能三色灯", normalized)
        self.assertIn("交通灯协议", normalized)
        self.assertIn("绕过每个设备协议", normalized)
        self.assertNotIn("智能采集灯", normalized)
        self.assertNotIn("通信协议", normalized)

    def test_professional_terms_are_flagged_for_review_not_rewritten(self):
        flags = professional_term_flags("三色灯连接MES，员工采用计件工资。")
        self.assertEqual(
            [item["term"] for item in flags],
            ["三色灯", "MES", "计件工资"],
        )
        self.assertTrue(all(item["human_review_required"] for item in flags))

    def test_alignment_detects_reference_reordering(self):
        source = [
            {"from_ms": 0, "to_ms": 10000, "text": "客户和工厂介绍"},
            {"from_ms": 10000, "to_ms": 20000, "text": "生产问题和订单管理"},
            {"from_ms": 20000, "to_ms": 30000, "text": "设备联网和三色灯"},
        ]
        reference = [
            {"from_ms": 0, "to_ms": 8000, "text": "客户和工厂介绍"},
            {"from_ms": 8000, "to_ms": 16000, "text": "设备联网和三色灯"},
            {"from_ms": 16000, "to_ms": 24000, "text": "生产问题和订单管理"},
        ]
        result = align_transcript_segments(source, reference)
        self.assertEqual(
            [item["source_segment_index"] for item in result["matches"]],
            [0, 2, 1],
        )
        self.assertTrue(result["reordering_detected"])


if __name__ == "__main__":
    unittest.main()
