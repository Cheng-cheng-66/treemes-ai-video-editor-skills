import unittest

from skills.case_study.renderer import build_filter_complex


class CaseVideoRendererTests(unittest.TestCase):
    def test_reordered_segments_keep_audio_and_video_together(self):
        filters, video_label, audio_label = build_filter_complex(
            [
                {"source_start_seconds": 0.0, "source_end_seconds": 10.0},
                {"source_start_seconds": 30.0, "source_end_seconds": 40.0},
                {"source_start_seconds": 10.0, "source_end_seconds": 20.0},
            ]
        )
        self.assertIn("trim=start=30.000:end=40.000", filters)
        self.assertIn("atrim=start=30.000:end=40.000", filters)
        self.assertIn("concat=n=3:v=1:a=1", filters)
        self.assertEqual(video_label, "[vout]")
        self.assertEqual(audio_label, "[aout]")

    def test_empty_plan_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "segment"):
            build_filter_complex([])


if __name__ == "__main__":
    unittest.main()
