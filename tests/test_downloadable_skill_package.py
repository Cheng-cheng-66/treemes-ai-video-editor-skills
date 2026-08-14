import hashlib
import os
import stat
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = "ai-video-editing-skills"


class DownloadableSkillPackageTests(unittest.TestCase):
    def build(self, directory: Path) -> Path:
        completed = subprocess.run(
            [
                "python3",
                str(ROOT / "scripts/build_downloadable_skill_package.py"),
                "--output-dir",
                str(directory),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        return directory / f"AI-Video-Editing-Skill-macOS-v{version}.zip"

    def test_archive_shape_required_files_mode_and_checksum(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = self.build(Path(temp))
            checksum_path = archive_path.with_suffix(".zip.sha256")
            self.assertTrue(archive_path.is_file())
            self.assertTrue(checksum_path.is_file())
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
                self.assertTrue(names)
                self.assertEqual({name.split("/", 1)[0] for name in names}, {TOP_LEVEL})
                for relative in (
                    "SKILL.md",
                    "agents/openai.yaml",
                    "core/config.py",
                    "presets/video_diary/cover.yaml",
                    "scripts/doctor.py",
                    "scripts/smoke_test_factory_shoot.py",
                    "安装.command",
                ):
                    self.assertIn(f"{TOP_LEVEL}/{relative}", names)
                install_info = archive.getinfo(f"{TOP_LEVEL}/安装.command")
                mode = (install_info.external_attr >> 16) & 0o777
                self.assertTrue(mode & stat.S_IXUSR)
                self.assertFalse(
                    any(
                        Path(name).suffix.lower()
                        in {".mp4", ".mov", ".wav", ".mp3", ".m4a", ".db"}
                        for name in names
                    )
                )
            digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
            self.assertEqual(checksum_path.read_text().split()[0], digest)

    def test_extracted_package_installs_into_isolated_codex_home(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            archive_path = self.build(temp_root)
            extract_root = temp_root / "extract"
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(extract_root)
            installer = extract_root / TOP_LEVEL / "安装.command"
            installer.chmod(installer.stat().st_mode | stat.S_IXUSR)
            codex_home = temp_root / "codex-home"
            environment = dict(os.environ)
            environment.update(
                {
                    "CODEX_HOME": str(codex_home),
                    "AI_VIDEO_SKILL_NONINTERACTIVE": "1",
                    "AI_VIDEO_SKILL_SKIP_DOCTOR": "1",
                }
            )
            completed = subprocess.run(
                [str(installer)],
                cwd=extract_root,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            installed = codex_home / "skills" / TOP_LEVEL
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "agents/openai.yaml").is_file())
            self.assertTrue((installed / "scripts/doctor.py").is_file())
            self.assertTrue(
                (installed / "scripts/smoke_test_factory_shoot.py").is_file()
            )
            self.assertFalse(any(installed.rglob("._*")))
            (installed / "previous-install-marker.txt").write_text(
                "preserve me", encoding="utf-8"
            )
            second = subprocess.run(
                [str(installer)],
                cwd=extract_root,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            backups = sorted(
                (codex_home / "skills").glob(
                    "ai-video-editing-skills.backup-*"
                )
            )
            self.assertEqual(len(backups), 1)
            self.assertEqual(
                (backups[0] / "previous-install-marker.txt").read_text(
                    encoding="utf-8"
                ),
                "preserve me",
            )


if __name__ == "__main__":
    unittest.main()
