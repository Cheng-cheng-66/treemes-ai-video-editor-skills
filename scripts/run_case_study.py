#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.case_study.runner import (
    DEFAULT_CASE_PROMPT,
    AnalyzeRequest,
    analyze,
    render_draft,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Case-video analysis and rendering")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--job-id", required=True)
    analyze_parser.add_argument("--source", required=True, type=Path)
    analyze_parser.add_argument("--output-dir", required=True, type=Path)
    analyze_parser.add_argument(
        "--whisper-model",
        type=Path,
        default=ROOT / "var/models/ggml-small-q5_1.bin",
    )
    analyze_parser.add_argument("--whisper-command", default="whisper-cli")
    analyze_parser.add_argument("--prompt", default=DEFAULT_CASE_PROMPT)

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--plan", required=True, type=Path)
    render_parser.add_argument("--output", required=True, type=Path)
    render_parser.add_argument("--draft", action="store_true")

    args = parser.parse_args()
    if args.command == "analyze":
        result = analyze(
            AnalyzeRequest(
                job_id=args.job_id,
                source=args.source,
                output_dir=args.output_dir,
                whisper_model=args.whisper_model,
                whisper_command=args.whisper_command,
                initial_prompt=args.prompt,
            )
        )
    else:
        result = render_draft(
            args.plan,
            args.output,
            allow_unreviewed=args.draft,
        )
    print(f"PASS: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
