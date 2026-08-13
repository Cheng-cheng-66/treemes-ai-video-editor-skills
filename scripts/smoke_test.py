#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import load_config
from core.process import run_command
from core.qc import CheckStatus, full_decode, probe_video
from skills.video_diary.runner import RenderRequest, render


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ai-video-editor-smoke-") as temp_dir:
        root = Path(temp_dir)
        source = root / "source.mp4"
        generated = run_command(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=540x960:rate=30:duration=1.5",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000:duration=1.5",
                "-vf",
                "setparams=color_primaries=bt2020:color_trc=arib-std-b67:colorspace=bt2020nc",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-color_primaries",
                "bt2020",
                "-color_trc",
                "arib-std-b67",
                "-colorspace",
                "bt2020nc",
                "-c:a",
                "aac",
                "-shortest",
                str(source),
            ],
            timeout=120,
        )
        if generated.returncode != 0:
            print(f"FAIL: synthetic input generation - {generated.stderr}")
            return 1

        plan = root / "plan.json"
        captions = root / "captions.json"
        output = root / "data" / "outputs" / "smoke.mp4"
        plan.write_text(
            json.dumps(
                {
                    "version": 1,
                    "source": str(source),
                    "source_duration_seconds": 1.5,
                    "speed": 1.0,
                    "title": "视频日记迁移技术样片",
                    "cover_title_lines": [
                        "视频日记",
                        "迁移技术样片",
                    ],
                    "remove": [],
                    "image_treatment": {
                        "mode": "none",
                        "reason": "合成技术样片不执行额外画面处理",
                        "manual_visual_review": "NOT_APPLICABLE",
                    },
                    "audio_treatment": {
                        "class": "A",
                        "reason": "合成正弦音只验证渲染链路",
                        "manual_listening_review": "NOT_APPLICABLE",
                    },
                    "bgm_mode": "off",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        captions.write_text(
            json.dumps(
                [{"start": 0.1, "end": 1.2, "text": "迁移技术样片"}],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        environment = dict(os.environ)
        environment["AI_VIDEO_EDITOR_DATA_ROOT"] = str(root / "data")
        config = load_config(environment=environment)
        try:
            render(
                RenderRequest(
                    plan=plan,
                    captions=captions,
                    output=output,
                    date="2026/07/25",
                    day="Day0",
                ),
                config,
            )
            probe = probe_video(output)
            video = next(
                stream
                for stream in probe["streams"]
                if stream["codec_type"] == "video"
            )
            if not (
                video.get("width") == 1080
                and video.get("height") == 1920
                and video.get("r_frame_rate") == "30/1"
            ):
                print(f"FAIL: unexpected smoke output: {video}")
                return 2
            decoded = full_decode(output)
            if decoded.status != CheckStatus.PASS:
                print(f"FAIL: {decoded.detail}")
                return 3
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            print(f"FAIL: smoke render - {exc}")
            return 4
    print("PASS: synthetic video-diary sample rendered and fully decoded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
