import json
import tempfile
import unittest
from pathlib import Path

from core.config import load_config
from skills.video_diary.runner import (
    RenderRequest,
    build_renderer_environment,
    validate_edit_plan,
)


class VideoDiaryRunnerTests(unittest.TestCase):
    def test_renderer_environment_uses_request_and_runtime_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(
                environment={"AI_VIDEO_EDITOR_DATA_ROOT": str(root / "data")}
            )
            plan = root / "plan.json"
            captions = root / "captions.json"
            output = root / "data" / "outputs" / "result.mp4"
            plan.write_text(json.dumps({"source": "input.mov"}), encoding="utf-8")
            captions.write_text("[]", encoding="utf-8")
            request = RenderRequest(
                plan=plan,
                captions=captions,
                output=output,
                date="2026/07/25",
                day="Day14",
                template_only=True,
            )

            environment = build_renderer_environment(config, request)

            self.assertEqual(environment["VIDEO_DIARY_DATE"], "2026/07/25")
            self.assertEqual(environment["VIDEO_DIARY_DAY"], "Day14")
            self.assertEqual(
                environment["VIDEO_DIARY_FONT_COVER_TITLE"],
                "/System/Library/Fonts/Supplemental/Songti.ttc",
            )
            self.assertEqual(environment["VIDEO_DIARY_TEMPLATE_ONLY"], "1")
            self.assertTrue(
                environment["VIDEO_DIARY_WORK_DIR"].startswith(
                    str((root / "data").resolve())
                )
            )
            self.assertTrue(
                environment["VIDEO_DIARY_TEMPLATE_DIR"].startswith(
                    str((root / "data").resolve())
                )
            )

    def test_date_and_day_formats_are_rejected_before_render(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            request = RenderRequest(
                plan=root / "plan.json",
                captions=root / "captions.json",
                output=root / "out.mp4",
                date="25-07-2026",
                day="14",
            )
            with self.assertRaises(ValueError):
                request.validate_metadata()

    def test_edit_plan_defaults_to_normal_speed_and_requires_traceable_cuts(self):
        plan = validate_edit_plan(
            {
                "source": "input.mov",
                "source_duration_seconds": 12.0,
                "title": "工厂数字化和AI化，哪个更重要？",
                "cover_title_lines": ["工厂数字化和AI化", "哪个更重要？"],
                "remove": [
                    {
                        "start": 1.0,
                        "end": 2.0,
                        "reason": "拍摄开头无效画面，已确认删除",
                    }
                ],
                "image_treatment": {
                    "mode": "none",
                    "reason": "画面曝光和清晰度正常",
                    "manual_visual_review": "NOT_REVIEWED",
                },
                "audio_treatment": {
                    "class": "A",
                    "reason": "人声清晰，环境声不影响理解",
                    "manual_listening_review": "NOT_REVIEWED",
                },
                "bgm_mode": "off",
            }
        )

        self.assertEqual(plan["speed"], 1.0)
        self.assertEqual(plan["remove"][0]["reason"], "拍摄开头无效画面，已确认删除")

    def test_speed_above_one_requires_an_explicit_judgment(self):
        base = {
            "source": "input.mov",
            "source_duration_seconds": 12.0,
            "title": "测试标题",
            "remove": [],
            "image_treatment": {
                "mode": "none",
                "reason": "画面正常",
                "manual_visual_review": "NOT_REVIEWED",
            },
            "audio_treatment": {
                "class": "A",
                "reason": "音频干净",
                "manual_listening_review": "NOT_REVIEWED",
            },
            "bgm_mode": "off",
            "speed": 1.08,
        }
        with self.assertRaisesRegex(ValueError, "speed_assessment"):
            validate_edit_plan(base)

        base["speed_assessment"] = {
            "original_pace": "明显偏慢",
            "post_cut_pace": "删除无效停顿后仍然拖沓",
            "reason": "小幅加速后仍保持自然表达",
        }
        self.assertEqual(validate_edit_plan(base)["speed"], 1.08)

    def test_cover_title_is_limited_to_two_explicit_lines(self):
        plan = {
            "source": "input.mov",
            "source_duration_seconds": 12.0,
            "title": "测试标题",
            "cover_title_lines": ["第一行", "第二行", "第三行"],
            "remove": [],
            "image_treatment": {
                "mode": "none",
                "reason": "画面正常",
                "manual_visual_review": "NOT_REVIEWED",
            },
            "audio_treatment": {
                "class": "A",
                "reason": "音频干净",
                "manual_listening_review": "NOT_REVIEWED",
            },
            "bgm_mode": "off",
        }
        with self.assertRaisesRegex(ValueError, "one or two"):
            validate_edit_plan(plan)

    def test_aspect_ratio_defaults_to_source_and_override_requires_authorization(self):
        base = {
            "source": "input.mov",
            "source_duration_seconds": 12.0,
            "title": "测试标题",
            "remove": [],
            "image_treatment": {
                "mode": "none",
                "reason": "画面正常",
                "manual_visual_review": "NOT_REVIEWED",
            },
            "audio_treatment": {
                "class": "A",
                "reason": "音频干净",
                "manual_listening_review": "NOT_REVIEWED",
            },
            "bgm_mode": "off",
        }
        self.assertEqual(
            validate_edit_plan(base)["output_aspect_ratio"],
            "source",
        )

        base["output_aspect_ratio"] = "9:16"
        with self.assertRaisesRegex(ValueError, "authorized=true"):
            validate_edit_plan(base)

        base["aspect_ratio_override_authorized"] = True
        with self.assertRaisesRegex(ValueError, "override_reason"):
            validate_edit_plan(base)

        base["aspect_ratio_override_reason"] = "用户明确要求竖屏版本"
        self.assertEqual(
            validate_edit_plan(base)["output_aspect_ratio"],
            "9:16",
        )

    def test_default_bgm_records_the_jianying_track_without_a_cache_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(
                environment={"AI_VIDEO_EDITOR_DATA_ROOT": str(root / "data")}
            )
            request = RenderRequest(
                plan=root / "plan.json",
                captions=root / "captions.json",
                output=root / "out.mp4",
                date="2026/07/27",
                day="Day17",
                template_only=True,
            )
            environment = build_renderer_environment(config, request)

            self.assertEqual(
                environment["VIDEO_DIARY_DEFAULT_BGM_PROVIDER"],
                "jianying",
            )
            self.assertEqual(
                environment["VIDEO_DIARY_DEFAULT_BGM_MATERIAL_ID"],
                "7377866594003568681",
            )
            self.assertEqual(
                environment["VIDEO_DIARY_DEFAULT_BGM_NAME"],
                "科技主题  Global Technology Background",
            )
            self.assertEqual(environment["VIDEO_DIARY_DEFAULT_BGM_PATH"], "")
            self.assertEqual(
                environment["VIDEO_DIARY_JIANYING_VOICE_SEPARATION_ENABLED"],
                "1",
            )
            self.assertEqual(
                environment["VIDEO_DIARY_JIANYING_VOICE_SEPARATION_MODE"],
                "keep_voice_only",
            )
            self.assertEqual(
                environment["VIDEO_DIARY_JIANYING_VOICE_VOLUME_DB"],
                "10.0",
            )
            self.assertEqual(
                environment["VIDEO_DIARY_JIANYING_BGM_VOLUME_DB"],
                "-8.0",
            )


if __name__ == "__main__":
    unittest.main()
