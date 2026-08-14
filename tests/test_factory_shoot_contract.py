import copy
import unittest

from skills.factory_shoot.contract import validate_captions, validate_edit_plan


def valid_plan():
    return {
        "schema_version": 1,
        "job_id": "factory_contract_test",
        "source": "/tmp/factory-source.mp4",
        "source_sha256": "a" * 64,
        "source_duration_seconds": 8.0,
        "title": {
            "lines": [
                {"text": "三个难题", "color": "yellow"},
                {"text": "MES如何解决", "color": "white"},
            ],
            "approved": True,
        },
        "picture_segments": [
            {
                "id": "speaker_open",
                "picture_source": {"start": 0.0, "end": 2.0},
                "dialogue_source_ranges": [{"start": 0.0, "end": 2.0}],
                "sync_zone": "A_SYNC_LOCKED",
                "current_speaker": "speaker_1",
                "visual_type": "front_speaker",
                "mouth_visible": True,
                "hand_action": None,
                "next_sync_anchor": "speaker_open",
                "edit_reason": "complete problem opening",
                "risk_level": "high",
                "confidence": 0.96,
                "assignment_method": "automatic",
            },
            {
                "id": "tablet",
                "picture_source": {"start": 2.0, "end": 6.0},
                "dialogue_source_ranges": [
                    {"start": 2.0, "end": 3.0},
                    {"start": 4.0, "end": 5.0},
                ],
                "sync_zone": "C_AUDIO_FREE",
                "current_speaker": "speaker_1_voice_over",
                "visual_type": "continuous_tablet_operation",
                "mouth_visible": False,
                "hand_action": "tap_and_swipe",
                "next_sync_anchor": "speaker_return",
                "edit_reason": "match tablet function explanation",
                "risk_level": "medium",
                "confidence": 0.97,
                "assignment_method": "automatic",
            },
            {
                "id": "speaker_return",
                "picture_source": {"start": 6.0, "end": 8.0},
                "dialogue_source_ranges": [{"start": 6.0, "end": 8.0}],
                "sync_zone": "A_SYNC_LOCKED",
                "current_speaker": "speaker_1",
                "visual_type": "front_speaker_return",
                "mouth_visible": True,
                "hand_action": None,
                "next_sync_anchor": "speaker_return",
                "edit_reason": "restore visible-speaker sync",
                "risk_level": "high",
                "confidence": 0.96,
                "assignment_method": "automatic",
            },
        ],
        "action_anchors": [
            {
                "id": "tablet_tap",
                "segment_id": "tablet",
                "source_start": 2.5,
                "source_end": 3.2,
                "action": "complete tablet tap",
                "confidence": 0.97,
            }
        ],
        "ambience_source_ranges": [{"start": 3.0, "end": 3.5}],
        "image_treatment": {
            "brightness": 0.0,
            "contrast": 1.0,
            "saturation": 1.0,
            "sharpen": 0.0,
        },
        "human_review": {
            "transcript_pass": None,
            "professional_terms_pass": None,
            "story_pass": None,
            "playback_pass": None,
        },
    }


def valid_captions():
    return {
        "schema_version": 1,
        "source_of_truth": "final_edited_audio",
        "captions": [
            {"start": 0.0, "end": 1.8, "text": "如果有这三个难题"},
            {"start": 2.0, "end": 3.0, "text": "我就是解决方案"},
            {"start": 6.0, "end": 7.8, "text": "回到人物继续说明"},
        ],
        "human_review": {
            "audio_subtitle_match_pass": None,
            "professional_terms_pass": None,
        },
    }


class FactoryShootContractTests(unittest.TestCase):
    def test_valid_plan_supports_locked_audio_free_and_return_anchor(self):
        plan = validate_edit_plan(valid_plan())
        self.assertEqual(plan["picture_segments"][1]["sync_zone"], "C_AUDIO_FREE")
        self.assertEqual(plan["picture_segments"][1]["next_sync_anchor"], "speaker_return")
        self.assertEqual(plan["final_duration_seconds"], 8.0)

    def test_a_sync_locked_requires_identical_picture_and_dialogue_range(self):
        plan = valid_plan()
        plan["picture_segments"][0]["dialogue_source_ranges"][0]["end"] = 1.8
        with self.assertRaisesRegex(ValueError, "A_SYNC_LOCKED"):
            validate_edit_plan(plan)

    def test_audio_free_requires_future_anchor_when_returning_to_visible_speaker(self):
        plan = valid_plan()
        plan["picture_segments"][1]["next_sync_anchor"] = None
        with self.assertRaisesRegex(ValueError, "next_sync_anchor"):
            validate_edit_plan(plan)

    def test_action_anchor_cannot_cross_a_picture_cut(self):
        plan = valid_plan()
        plan["action_anchors"][0]["source_end"] = 6.2
        with self.assertRaisesRegex(ValueError, "action anchor"):
            validate_edit_plan(plan)

    def test_automatic_zone_assignment_respects_confidence_threshold(self):
        plan = valid_plan()
        plan["picture_segments"][1]["confidence"] = 0.80
        with self.assertRaisesRegex(ValueError, "confidence"):
            validate_edit_plan(plan)
        plan["picture_segments"][1]["assignment_method"] = "manual"
        self.assertEqual(validate_edit_plan(plan)["picture_segments"][1]["confidence"], 0.80)

    def test_title_must_be_explicitly_approved(self):
        plan = valid_plan()
        plan["title"]["approved"] = False
        with self.assertRaisesRegex(ValueError, "title.approved"):
            validate_edit_plan(plan)

    def test_captions_are_ordered_single_line_and_final_timeline_bounded(self):
        captions = validate_captions(valid_captions(), final_duration_seconds=8.0)
        self.assertEqual(len(captions["captions"]), 3)
        invalid = copy.deepcopy(valid_captions())
        invalid["captions"][1]["text"] = "第一行\n第二行"
        with self.assertRaisesRegex(ValueError, "single-line"):
            validate_captions(invalid, final_duration_seconds=8.0)


if __name__ == "__main__":
    unittest.main()
