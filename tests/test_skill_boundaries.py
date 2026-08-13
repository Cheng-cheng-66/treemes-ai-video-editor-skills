import json
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
        self.assertFalse(skills["factory_shoot"].enabled)
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


if __name__ == "__main__":
    unittest.main()
