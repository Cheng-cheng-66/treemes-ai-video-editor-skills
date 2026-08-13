import unittest

from skills.case_study.sync_zone_analyzer import classify_face_state, merge_samples


class CaseVideoSyncZoneTests(unittest.TestCase):
    def test_large_frontal_face_is_sync_locked(self):
        result = classify_face_state([(80, 90, 100, 100)], 270, 480)
        self.assertEqual(result["sync_zone"], "A_SYNC_LOCKED")
        self.assertTrue(result["mouth_visibility_candidate"])

    def test_no_face_is_audio_free_candidate_not_action_locked(self):
        result = classify_face_state([], 270, 480)
        self.assertEqual(result["sync_zone"], "C_AUDIO_FREE")
        self.assertFalse(result["mouth_visibility_candidate"])
        self.assertNotEqual(result["sync_zone"], "D_ACTION_LOCKED")

    def test_consecutive_samples_are_merged(self):
        samples = [
            {"time_seconds": 0.0, "sync_zone": "A_SYNC_LOCKED", "confidence": 0.8},
            {"time_seconds": 1.0, "sync_zone": "A_SYNC_LOCKED", "confidence": 0.7},
            {"time_seconds": 2.0, "sync_zone": "C_AUDIO_FREE", "confidence": 0.7},
        ]
        zones = merge_samples(samples, sample_interval_seconds=1.0)
        self.assertEqual(len(zones), 2)
        self.assertEqual(zones[0]["end_seconds"], 2.0)


if __name__ == "__main__":
    unittest.main()
