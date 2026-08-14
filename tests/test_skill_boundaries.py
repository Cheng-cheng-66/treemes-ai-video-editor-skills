import json
import tempfile
import unittest
from pathlib import Path

from core.config import PROJECT_ROOT
from core.skills import discover_skills, find_boundary_violations


class SkillBoundaryTests(unittest.TestCase):
    def test_three_skills_are_discoverable_and_case_study_beta_is_enabled(self):
        skills = discover_skills(PROJECT_ROOT)
        self.assertEqual(
            set(skills),
            {"video_diary", "factory_shoot", "case_study"},
        )
        self.assertTrue(skills["video_diary"].enabled)
        self.assertTrue(skills["factory_shoot"].enabled)
        self.assertTrue(callable(skills["factory_shoot"].load_entrypoint()))
        self.assertTrue(skills["case_study"].enabled)
        self.assertIn("beta", skills["case_study"].status)

    def test_manifests_do_not_contain_machine_absolute_paths(self):
        for manifest in (PROJECT_ROOT / "skills").glob("*/skill.json"):
            raw = manifest.read_text(encoding="utf-8")
            self.assertNotIn("/" + "Users/", raw)
            self.assertNotIn("\\Users\\", raw)
            json.loads(raw)

    def test_skills_do_not_import_each_other(self):
        self.assertEqual(find_boundary_violations(PROJECT_ROOT), [])

    def test_appledouble_sidecars_on_external_macos_volumes_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "skills/example"
            skill.mkdir(parents=True)
            (skill / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            (skill / "._module.py").write_bytes(b"\x00\x05\x16\x07\xb0\x00")
            self.assertEqual(find_boundary_violations(root), [])


if __name__ == "__main__":
    unittest.main()
