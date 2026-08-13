import json
import unittest
from pathlib import Path

from scripts.validate_github_release import (
    REQUIRED_SKILL_ENTRIES,
    ROOT,
    SKILLS,
    parse_skill_frontmatter,
    scan_file,
    validate_manifest,
)


class GitHubReleasePackageTests(unittest.TestCase):
    def test_actual_version_is_beta(self):
        self.assertEqual((ROOT / "VERSION").read_text().strip(), "0.10.0-beta.1")
        config = json.loads((ROOT / "configs/default.json").read_text())
        self.assertEqual(config["channel"], "beta")

    def test_three_skill_packages_are_self_describing(self):
        for skill in SKILLS:
            root = ROOT / "skills" / skill
            for entry in REQUIRED_SKILL_ENTRIES:
                self.assertTrue((root / entry).exists(), f"{skill}/{entry}")
            parse_skill_frontmatter(root / "SKILL.md")
            manifest = validate_manifest(root / "skill.json")
            self.assertEqual(manifest["id"], skill)

    def test_factory_skill_remains_disabled(self):
        manifest = validate_manifest(ROOT / "skills/factory_shoot/skill.json")
        self.assertFalse(manifest["enabled"])
        self.assertIsNone(manifest["entrypoint"])

    def test_release_sources_have_no_media_or_machine_paths(self):
        for relative in (
            "core/config.py",
            "README.md",
            "skills/video_diary/SKILL.md",
            "skills/factory_shoot/SKILL.md",
            "skills/case_study/SKILL.md",
        ):
            self.assertEqual(scan_file(ROOT / relative), [], relative)


if __name__ == "__main__":
    unittest.main()
