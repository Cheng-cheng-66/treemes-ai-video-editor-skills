#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.case_study.pause_analyzer import extract_token_pauses
from skills.case_study.runner import write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--whisper-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--minimum-gap", type=float, default=0.25)
    args = parser.parse_args()
    result = extract_token_pauses(
        args.whisper_json,
        minimum_gap_seconds=args.minimum_gap,
    )
    write_json(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
