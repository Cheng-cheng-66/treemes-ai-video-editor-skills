import hashlib
import platform
import tempfile
import unittest
from pathlib import Path

from core.config import load_config
from core.process import executable_path
from skills.video_diary.runner import RenderRequest, render


class TemplateCompatibilityTests(unittest.TestCase):
    @unittest.skipUnless(platform.system() == "Darwin", "macOS baseline hash")
    def test_release_templates_match_the_locked_v1_finalization_baseline(self):
        if executable_path("ffmpeg") is None or executable_path("node") is None:
            self.skipTest("FFmpeg and Node.js are required")
        fixture = Path("tests/fixtures/video_diary")
        with tempfile.TemporaryDirectory() as temp_dir:
            data_root = Path(temp_dir) / "data"
            config = load_config(
                environment={"AI_VIDEO_EDITOR_DATA_ROOT": str(data_root)}
            )
            render(
                RenderRequest(
                    plan=fixture / "standard_plan.json",
                    captions=fixture / "standard_captions.json",
                    output=data_root / "unused.mp4",
                    date="2026/07/23",
                    day="Day13",
                    template_only=True,
                ),
                config,
            )
            template_dir = data_root / "outputs" / "video_diary" / "templates"
            hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in template_dir.glob("*.png")
            }

        self.assertEqual(
            hashes["video_diary_cover_2026-07-23_day13_v5.png"],
            "8b6220775627082af82a4f97c11fe426137094398b4cf35344b2269da0fb700b",
        )
        self.assertEqual(
            hashes["video_diary_header_2026-07-23_day13_v5.png"],
            "8ebb83b0fafdf8cb9954e7cb38a152a4cb46471ade64fd8d83c2c37c30f5a2a2",
        )


if __name__ == "__main__":
    unittest.main()
