import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills.case_study.source_analyzer import (
    build_source_manifest,
    sha256_file,
)


class CaseVideoSourceAnalyzerTests(unittest.TestCase):
    def test_sha256_is_content_based(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.bin"
            source.write_bytes(b"case-video-source")
            self.assertEqual(
                sha256_file(source),
                "9c515ac0deeb64bea2a5b3b215abefe68e2d776f29c484f75c1409cd4ec15232",
            )

    @patch("skills.case_study.source_analyzer.probe_media")
    def test_manifest_keeps_human_review_unset(self, probe):
        probe.return_value = {
            "duration_seconds": 644.447,
            "video": {
                "codec": "h264",
                "width": 1080,
                "height": 1920,
                "frame_rate": 60.0,
            },
            "audio": {"codec": "aac", "sample_rate": 44100, "channels": 2},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.mp4"
            source.write_bytes(b"source")
            manifest = build_source_manifest(source)
        self.assertEqual(manifest["duration_seconds"], 644.447)
        self.assertIsNone(manifest["human_source_identity_reviewed"])
        self.assertEqual(len(manifest["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
