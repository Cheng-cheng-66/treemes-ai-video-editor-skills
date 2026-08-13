from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts import build_video_editing_full_migration_package as migration


class FullMigrationPackageTests(unittest.TestCase):
    def test_selected_files_cover_current_workflows_without_media(self) -> None:
        selected = {
            path.relative_to(migration.PROJECT_ROOT).as_posix()
            for path in migration.collect_files()
        }
        self.assertIn("configs/default.json", selected)
        self.assertIn("presets/video_diary/bgm.yaml", selected)
        self.assertIn("presets/factory_demo_hybrid/editorial.yaml", selected)
        self.assertIn("skills/video_diary/runner.py", selected)
        self.assertIn("skills/factory_shoot/skill.json", selected)
        self.assertNotIn("work/factory_demo/prepare_jianying_hybrid_template.py", selected)
        self.assertFalse(
            any(Path(value).suffix.lower() in migration.FORBIDDEN_SUFFIXES for value in selected)
        )
        self.assertNotIn("configs/local.json", selected)

    def test_audio_contract_matches_latest_confirmed_values(self) -> None:
        config = json.loads(
            (migration.PROJECT_ROOT / "configs/default.json").read_text(
                encoding="utf-8"
            )
        )
        audio = config["video_diary"]["jianying_audio"]
        bgm = config["video_diary"]["bgm"]
        self.assertIs(audio["voice_separation_enabled"], True)
        self.assertEqual(audio["voice_separation_mode"], "keep_voice_only")
        self.assertEqual(audio["voice_volume_db"], 10.0)
        self.assertEqual(bgm["jianying_initial_volume_db"], -8.0)

    def test_builder_emits_verifiable_archive_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory(prefix="migration-package-test-") as temp:
            output_root = Path(temp)
            self.assertEqual(
                migration.main_for_output(output_root),
                0,
            )
            archive = output_root / f"{migration.PACKAGE_ID}.zip"
            checksum = output_root / f"{archive.name}.sha256"
            self.assertTrue(archive.is_file())
            self.assertTrue(checksum.is_file())
            self.assertTrue(
                checksum.read_text(encoding="utf-8").startswith(
                    migration.sha256(archive)
                )
            )
            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())
                prefix = f"{migration.PACKAGE_ID}/"
                self.assertIn(f"{prefix}DEPLOY_MACOS.sh", names)
                self.assertIn(f"{prefix}MIGRATION_MANIFEST.json", names)
                self.assertIn(f"{prefix}verify_migration.py", names)
                deployer = bundle.read(f"{prefix}DEPLOY_MACOS.sh").decode("utf-8")
                self.assertLess(
                    deployer.index("python3 verify_migration.py"),
                    deployer.index("./scripts/install_macos.sh"),
                )
                self.assertFalse(
                    any(
                        Path(name).suffix.lower() in migration.FORBIDDEN_SUFFIXES
                        for name in names
                    )
                )


if __name__ == "__main__":
    unittest.main()
