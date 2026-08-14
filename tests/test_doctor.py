import tempfile
import unittest
from unittest.mock import patch

from core.config import load_config
from core.qc import CheckStatus
from scripts.doctor import collect_checks


class DoctorTests(unittest.TestCase):
    def test_doctor_checks_required_environment_and_video_diary_loading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(
                "os.environ",
                {"AI_VIDEO_EDITOR_DATA_ROOT": temp_dir},
            ):
                checks = collect_checks(load_config())

        check_ids = {check.check_id for check in checks}
        self.assertIn("operating_system", check_ids)
        self.assertIn("python", check_ids)
        self.assertIn("ffmpeg", check_ids)
        self.assertIn("ffprobe", check_ids)
        self.assertIn("models", check_ids)
        self.assertIn("fonts", check_ids)
        self.assertIn("runtime_directories", check_ids)
        self.assertIn("disk_space", check_ids)
        self.assertIn("video_diary_skill", check_ids)
        self.assertIn("factory_shoot_skill", check_ids)
        self.assertIn("pillow", check_ids)
        self.assertNotIn(CheckStatus.FAIL, {check.status for check in checks})


if __name__ == "__main__":
    unittest.main()
