#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.case_study.pause_analyzer import analyze_pauses
from skills.case_study.runner import write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--noise-db", type=float, default=-35.0)
    parser.add_argument("--minimum-duration", type=float, default=0.3)
    args = parser.parse_args()
    result = analyze_pauses(
        args.source,
        noise_db=args.noise_db,
        minimum_duration_seconds=args.minimum_duration,
    )
    write_json(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
