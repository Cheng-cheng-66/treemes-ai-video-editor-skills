#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from skills.factory_shoot.runner import FactoryRenderRequest, run


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic factory-shoot hybrid Beta workflow"
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--captions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bgm", type=Path)
    args = parser.parse_args()
    try:
        result = run(
            FactoryRenderRequest(
                plan=args.plan,
                captions=args.captions,
                output_dir=args.output_dir,
                bgm=args.bgm,
            )
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "RENDERED_BETA_CANDIDATE_MANUAL_REVIEW_REQUIRED",
                "fallback_preview": str(result["fallback_preview"]),
                "quality_report": str(result["quality_report"]),
                "jianying_manifest": str(result["jianying_manifest"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
