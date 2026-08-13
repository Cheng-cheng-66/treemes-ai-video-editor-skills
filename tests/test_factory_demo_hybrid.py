from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from work.factory_demo import build_factory_hybrid_assets as hybrid
except ModuleNotFoundError as exc:
    if exc.name not in {"PIL", "work", "work.factory_demo"}:
        raise
    hybrid = None
    HYBRID_IMPORT_SKIP_REASON = (
        "customer-specific factory prototype is excluded from the release package"
    )
else:
    HYBRID_IMPORT_SKIP_REASON = ""


class FactorySubtitlePresetContractTests(unittest.TestCase):
    def test_factory_subtitle_presets_are_large_and_spaced(self) -> None:
        for relative_path in (
            "presets/factory_demo/subtitle.yaml",
            "presets/factory_demo_hybrid/subtitle.yaml",
        ):
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn("size_px: 96", text, relative_path)
            self.assertIn("letter_spacing_px: 4", text, relative_path)
            self.assertIn("baseline_y: 1280", text, relative_path)
            self.assertIn("auto_shrink: false", text, relative_path)


@unittest.skipUnless(hybrid is not None, HYBRID_IMPORT_SKIP_REASON)
class FactoryDemoHybridTests(unittest.TestCase):
    def test_video_diary_presets_are_not_hybrid_inheritance(self) -> None:
        for path in (ROOT / "presets/factory_demo_hybrid").glob("*.yaml"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("presets/video_diary", text)

    def test_protected_manual_fields_remain_null(self) -> None:
        quality = json.loads(
            (
                ROOT
                / "experiments/factory_ab_img5667_20260724_01"
                / "route_b_jianying/quality_report.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIsNone(
            quality["zero_tolerance"]["audio_subtitle_mismatch_count"]
        )
        self.assertIsNone(quality["zero_tolerance"]["word_loss_count"])
        self.assertIsNone(
            quality["zero_tolerance"]["visible_lip_sync_error_count"]
        )
        self.assertIsNone(quality["perceptual_continuity_pass"])

    def test_user_confirmed_denoise_fields_only(self) -> None:
        quality = json.loads(
            (
                ROOT
                / "experiments/factory_ab_img5667_20260724_01"
                / "route_b_jianying/quality_report.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIs(quality["denoise_effective"], True)
        self.assertIs(quality["denoise_human_review_pass"], True)

    def test_edit_plan_validation(self) -> None:
        valid, errors = hybrid.validate_edit_plan()
        self.assertTrue(valid, errors)

    def test_hybrid_manual_review_fields_are_unreviewed(self) -> None:
        quality = json.loads(
            (
                ROOT
                / "experiments/factory_ab_img5667_20260724_01"
                / "hybrid/quality_report.json"
            ).read_text(encoding="utf-8")
        )
        for field, value in quality["manual_review"].items():
            self.assertIsNone(value, field)

    def test_title_is_exactly_three_frames(self) -> None:
        title = hybrid.title_frame_contract()
        self.assertEqual(title["detected_frames"], 3)
        self.assertIs(title["pixel_detection_pass"], True)


@unittest.skipUnless(
    (
        ROOT
        / "runs/factory_demo_hybrid_c_audio_free_20260727/quality_report.json"
    ).is_file(),
    "local C_AUDIO_FREE evidence package is not present",
)
class FactoryDemoCAudioFreeTests(unittest.TestCase):
    RUN = ROOT / "runs/factory_demo_hybrid_c_audio_free_20260727"

    def load(self, name: str) -> dict:
        return json.loads((self.RUN / name).read_text(encoding="utf-8"))

    def test_c_picture_is_one_continuous_source_range(self) -> None:
        plan = self.load("edit_plan.json")
        evidence = plan["C_AUDIO_FREE_evidence"]
        self.assertEqual(evidence["continuous_picture_range_count"], 1)
        self.assertEqual(evidence["picture_cut_at_removed_audio_pause_count"], 0)
        self.assertGreaterEqual(evidence["qualifying_removed_pause_count"], 2)

    def test_action_locked_ranges_are_explicit_and_complete(self) -> None:
        zones = self.load("sync_zones.json")["zones"]
        action_zones = [row for row in zones if row["zone"] == "D_ACTION_LOCKED"]
        self.assertEqual(len(action_zones), 2)
        self.assertTrue(all(row["confidence"] >= 0.9 for row in action_zones))
        anchors = self.load("shared/action_anchors.json")["anchors"]
        locked = [row for row in anchors if row.get("must_remain_complete")]
        self.assertEqual(len(locked), 2)
        self.assertTrue(all(row["cut_inside_action"] is False for row in locked))

    def test_return_sync_anchor_is_present(self) -> None:
        continuity = self.load("continuity_report.json")
        self.assertIs(continuity["return_sync_anchor_present"], True)
        self.assertEqual(continuity["return_sync_anchor_time"], 19.456)

    def test_automatic_quality_passes_but_completion_is_false(self) -> None:
        quality = self.load("quality_report.json")
        self.assertIs(quality["automatic_pass"], True)
        self.assertIs(quality["C_AUDIO_FREE_technical_pass"], True)
        self.assertIs(quality["completion_pass"], False)
        self.assertTrue(quality["go_no_go"].startswith("NO_GO"))

    def test_protected_human_fields_remain_null(self) -> None:
        quality = self.load("quality_report.json")
        for field in (
            "audio_subtitle_mismatch_count",
            "paraphrased_subtitle_count",
            "professional_term_rewrite_count",
            "word_loss_count",
            "visible_lip_sync_error_count",
            "perceptual_continuity_pass",
        ):
            self.assertIsNone(quality["manual_review"][field], field)

    def test_all_three_delivery_videos_exist(self) -> None:
        delivery = self.RUN / "delivery"
        expected = [
            "01_C_AUDIO_FREE_剪映原生母版.mp4",
            "02_C_AUDIO_FREE_响度标准化发布版.mp4",
            "03_C_AUDIO_FREE_路线A降级预览版.mp4",
        ]
        for name in expected:
            path = delivery / name
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 1_000_000, path)

    def test_jianying_repeatability_gate_passes(self) -> None:
        report = self.load("jianying/repeatability_report.json")
        self.assertEqual(report["trials_completed"], 10)
        self.assertEqual(report["technical_success_count"], 10)
        self.assertGreaterEqual(report["production_target_pass_count"], 9)
        self.assertIs(report["repeatability_gate_pass"], True)


if __name__ == "__main__":
    unittest.main()
