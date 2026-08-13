import unittest

import numpy as np

from skills.case_study.audio_aligner import normalized_cross_correlation_match


class CaseVideoAudioAlignerTests(unittest.TestCase):
    def test_finds_gain_changed_waveform_offset(self):
        rng = np.random.default_rng(7)
        source = rng.normal(0, 1, 20000).astype(np.float32)
        reference = source[7000:10000] * 0.45
        result = normalized_cross_correlation_match(source, reference)
        self.assertEqual(result["sample_offset"], 7000)
        self.assertGreater(result["score"], 0.99)


if __name__ == "__main__":
    unittest.main()
