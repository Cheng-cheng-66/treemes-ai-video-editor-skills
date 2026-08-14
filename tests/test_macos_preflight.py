import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.macos_preflight import install_missing_with_homebrew, verify


class MacosPreflightTests(unittest.TestCase):
    @patch("scripts.macos_preflight.find_jianying", return_value=Path("/Applications/Fake.app"))
    @patch("scripts.macos_preflight.missing_commands", return_value=[])
    @patch("scripts.macos_preflight.platform.system", return_value="Darwin")
    def test_complete_dependencies_pass_when_all_are_present(self, _system, _missing, _app):
        ready = verify(install_missing=False, require_jianying=True)
        self.assertIn("ffmpeg", ready)
        self.assertIn("jianying", ready)

    @patch("scripts.macos_preflight.missing_commands", return_value=["ffmpeg", "ffprobe"])
    @patch("scripts.macos_preflight.platform.system", return_value="Darwin")
    def test_missing_ffmpeg_fails_closed(self, _system, _missing):
        with self.assertRaisesRegex(RuntimeError, "ffmpeg"):
            verify(install_missing=False, require_jianying=False)

    @patch("scripts.macos_preflight.shutil.which", return_value=None)
    def test_no_homebrew_never_silently_ignores_missing_tools(self, _which):
        with self.assertRaisesRegex(RuntimeError, "Homebrew"):
            install_missing_with_homebrew(["ffmpeg"])

    @patch("scripts.macos_preflight.find_jianying", return_value=None)
    @patch("scripts.macos_preflight.missing_commands", return_value=[])
    @patch("scripts.macos_preflight.platform.system", return_value="Darwin")
    def test_missing_jianying_fails_complete_mode(self, _system, _missing, _app):
        with self.assertRaisesRegex(RuntimeError, "剪映"):
            verify(install_missing=False, require_jianying=True)


if __name__ == "__main__":
    unittest.main()
