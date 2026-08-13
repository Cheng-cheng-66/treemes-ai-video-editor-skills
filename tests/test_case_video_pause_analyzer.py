import json
import tempfile
import unittest
from pathlib import Path

from skills.case_study.pause_analyzer import (
    extract_token_pauses,
    parse_silencedetect,
)


class CaseVideoPauseAnalyzerTests(unittest.TestCase):
    def test_parses_complete_silence_intervals(self):
        log = """
[silencedetect @ 0x1] silence_start: 1.2
[silencedetect @ 0x1] silence_end: 2.0 | silence_duration: 0.8
[silencedetect @ 0x1] silence_start: 4.0
[silencedetect @ 0x1] silence_end: 5.4 | silence_duration: 1.4
"""
        pauses = parse_silencedetect(log)
        self.assertEqual(len(pauses), 2)
        self.assertEqual(pauses[1]["duration_seconds"], 1.4)
        self.assertEqual(pauses[1]["class"], "long")

    def test_token_timestamps_detect_speech_gap_despite_background_audio(self):
        payload = {
            "transcription": [
                {
                    "tokens": [
                        {
                            "text": "工厂",
                            "offsets": {"from": 0, "to": 400},
                        },
                        {
                            "text": "MES",
                            "offsets": {"from": 1100, "to": 1500},
                        },
                    ]
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "asr.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = extract_token_pauses(path, minimum_gap_seconds=0.3)
        self.assertEqual(result["pause_count"], 1)
        self.assertEqual(result["pauses"][0]["duration_seconds"], 0.7)


if __name__ == "__main__":
    unittest.main()
