import unittest

from skills.video_diary.aspect_ratio import (
    parse_ffprobe_geometry,
    resolve_output_geometry,
)


class VideoDiaryAspectRatioTests(unittest.TestCase):
    def test_landscape_source_inherits_16_by_9(self):
        source = parse_ffprobe_geometry(
            {
                "streams": [
                    {
                        "width": 3840,
                        "height": 2160,
                        "sample_aspect_ratio": "1:1",
                    }
                ]
            }
        )

        resolved = resolve_output_geometry("source", source)

        self.assertEqual(source.orientation, "landscape")
        self.assertEqual(resolved["selection"], "inherited_from_source")
        self.assertEqual(resolved["output_aspect_ratio"], "16:9")
        self.assertEqual(
            (resolved["output_width"], resolved["output_height"]),
            (1920, 1080),
        )

    def test_rotation_metadata_changes_landscape_encoding_to_portrait_display(self):
        source = parse_ffprobe_geometry(
            {
                "streams": [
                    {
                        "width": 3840,
                        "height": 2160,
                        "sample_aspect_ratio": "1:1",
                        "side_data_list": [{"rotation": 90}],
                    }
                ]
            }
        )

        resolved = resolve_output_geometry("source", source)

        self.assertEqual(source.orientation, "portrait")
        self.assertEqual(source.rotation_degrees, 90)
        self.assertEqual(resolved["output_aspect_ratio"], "9:16")
        self.assertEqual(
            (resolved["output_width"], resolved["output_height"]),
            (1080, 1920),
        )

    def test_explicit_override_is_recorded_separately_from_inheritance(self):
        source = parse_ffprobe_geometry(
            {
                "streams": [
                    {
                        "width": 1920,
                        "height": 1080,
                        "sample_aspect_ratio": "1:1",
                    }
                ]
            }
        )

        resolved = resolve_output_geometry("9:16", source)

        self.assertEqual(resolved["selection"], "explicit_user_override")
        self.assertEqual(resolved["output_aspect_ratio"], "9:16")

    def test_square_source_requires_an_explicit_decision(self):
        with self.assertRaisesRegex(ValueError, "square"):
            parse_ffprobe_geometry(
                {
                    "streams": [
                        {
                            "width": 1080,
                            "height": 1080,
                            "sample_aspect_ratio": "1:1",
                        }
                    ]
                }
            )


if __name__ == "__main__":
    unittest.main()
