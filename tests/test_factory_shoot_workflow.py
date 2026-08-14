import unittest
from pathlib import Path
from unittest.mock import patch

from skills.factory_shoot.runner import FactoryRenderRequest
from skills.factory_shoot.workflow import prepare_complete


class FactoryShootWorkflowTests(unittest.TestCase):
    @patch("skills.factory_shoot.workflow.run")
    @patch("skills.factory_shoot.workflow.inspect_jianying_application")
    @patch("skills.factory_shoot.workflow.find_jianying_application")
    def test_prepare_complete_returns_no_deliverable(
        self, find_app, inspect_app, render
    ):
        find_app.return_value = Path("/Applications/VideoFusion-macOS.app")
        inspect_app.return_value = {
            "application_path": "/Applications/VideoFusion-macOS.app",
            "bundle_id": "com.lemon.lvpro",
            "display_name": "剪映专业版",
            "version": "7.9.0",
            "build": "366",
        }
        render.return_value = {
            "completion_request": Path("/tmp/run/completion_request.json")
        }
        result = prepare_complete(
            FactoryRenderRequest(
                plan=Path("plan.json"),
                captions=Path("captions.json"),
                output_dir=Path("run"),
            ),
            launch_application=False,
        )
        self.assertIsNone(result["deliverable_video"])
        self.assertTrue(result["technical_preview_is_not_deliverable"])
        self.assertEqual(
            result["status"],
            "BLOCKED_PENDING_JIANYING_UI_AND_HUMAN_REVIEW",
        )

    @patch("skills.factory_shoot.workflow.find_jianying_application", return_value=None)
    def test_missing_jianying_blocks_before_render(self, _find_app):
        with patch("skills.factory_shoot.workflow.run") as render:
            with self.assertRaisesRegex(FileNotFoundError, "剪映"):
                prepare_complete(
                    FactoryRenderRequest(
                        plan=Path("plan.json"),
                        captions=Path("captions.json"),
                        output_dir=Path("run"),
                    ),
                    launch_application=False,
                )
            render.assert_not_called()


if __name__ == "__main__":
    unittest.main()
