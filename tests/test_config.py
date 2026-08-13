import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import create_runtime_dirs, load_config


class ConfigTests(unittest.TestCase):
    def test_default_runtime_paths_are_portable_and_data_scoped(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_root = Path(temp_dir) / "production-data"
            with patch.dict(os.environ, {"AI_VIDEO_EDITOR_DATA_ROOT": str(data_root)}):
                config = load_config(local_path=Path(temp_dir) / "missing.json")

            self.assertEqual(config.paths.data_root, data_root.resolve())
            self.assertEqual(config.paths.input_dir, (data_root / "inputs").resolve())
            self.assertEqual(config.paths.output_dir, (data_root / "outputs").resolve())
            machine_prefix = "/" + "Users/"
            self.assertNotIn(machine_prefix, json.dumps(config.raw))

    def test_local_config_overrides_defaults_without_replacing_other_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            local = root / "local.json"
            local.write_text(
                json.dumps({"channel": "beta", "paths": {"logs": "custom-logs"}}),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"AI_VIDEO_EDITOR_DATA_ROOT": str(root / "data")}):
                config = load_config(local_path=local)

            self.assertEqual(config.channel, "beta")
            self.assertEqual(
                config.paths.logs_dir,
                (root / "data" / "custom-logs").resolve(),
            )
            self.assertEqual(config.paths.cache_dir, (root / "data" / "cache").resolve())

    def test_create_runtime_dirs_never_requires_media_to_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"AI_VIDEO_EDITOR_DATA_ROOT": temp_dir}):
                config = load_config()
                created = create_runtime_dirs(config)

            self.assertTrue(created)
            self.assertTrue(all(path.is_dir() for path in created))


if __name__ == "__main__":
    unittest.main()
