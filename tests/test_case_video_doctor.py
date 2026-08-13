from pathlib import Path
import unittest

from scripts.doctor_case_study import build_report


class CaseVideoDoctorTests(unittest.TestCase):
    def test_current_case_environment_passes_or_blocks_on_unbundled_models(self):
        report = build_report()
        model_paths = [
            Path(report["checks"][key]["path"])
            for key in ("whisper_model", "face_model")
        ]
        if all(path.is_file() for path in model_paths):
            self.assertEqual(report["status"], "PASS")
        else:
            self.assertEqual(report["status"], "BLOCKED")
            self.assertTrue(
                all(
                    report["checks"][key]["status"] == "BLOCKED"
                    for key in ("whisper_model", "face_model")
                    if not Path(report["checks"][key]["path"]).is_file()
                )
            )


if __name__ == "__main__":
    unittest.main()
