#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.case_study.source_analyzer import probe_media
from skills.case_study.sync_zone_analyzer import (
    analyze_sync_zones,
    write_sync_zones,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-fps", type=float, default=1.0)
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    duration = probe_media(source)["duration_seconds"]
    payload = analyze_sync_zones(
        source,
        duration,
        sample_fps=args.sample_fps,
    )
    write_sync_zones(args.output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
