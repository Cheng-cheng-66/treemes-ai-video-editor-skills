#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import load_config
from skills.video_diary.runner import RenderRequest, render


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a video diary")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--captions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--day", required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--template-only", action="store_true")
    args = parser.parse_args()
    environment = dict(os.environ)
    if args.config:
        environment["AI_VIDEO_EDITOR_CONFIG"] = str(args.config)
    request = RenderRequest(
        plan=args.plan,
        captions=args.captions,
        output=args.output,
        date=args.date,
        day=args.day,
        template_only=args.template_only,
    )
    output = render(request, load_config(environment=environment))
    print(f"PASS: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
