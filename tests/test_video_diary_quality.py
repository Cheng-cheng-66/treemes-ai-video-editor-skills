import unittest

from skills.video_diary.quality import parse_ebur128_summary


class VideoDiaryQualityTests(unittest.TestCase):
    def test_parse_ebur128_uses_final_summary(self):
        stderr = """
        t: 1.0 I: -17.2 LUFS TPK: -1.4 dBFS
        Summary:
          Integrated loudness:
            I: -16.9 LUFS
          True peak:
            Peak: -1.4 dBFS
        """

        self.assertEqual(
            parse_ebur128_summary(stderr),
            {
                "integrated_loudness_lufs": -16.9,
                "true_peak_dbtp": -1.4,
            },
        )

    def test_parse_ebur128_rejects_incomplete_output(self):
        with self.assertRaises(ValueError):
            parse_ebur128_summary("no summary")


if __name__ == "__main__":
    unittest.main()
