#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.case_study.audio_aligner import build_audio_anchors
from skills.case_study.runner import write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-wav", required=True, type=Path)
    parser.add_argument("--reference-wav", required=True, type=Path)
    parser.add_argument("--transcript-alignment", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--anchor-step", type=float)
    parser.add_argument("--downsample-factor", type=int, default=1)
    args = parser.parse_args()
    transcript_alignment = json.loads(
        args.transcript_alignment.read_text(encoding="utf-8")
    )
    result = build_audio_anchors(
        args.source_wav,
        args.reference_wav,
        transcript_alignment,
        anchor_step_seconds=args.anchor_step,
        downsample_factor=args.downsample_factor,
    )
    write_json(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
