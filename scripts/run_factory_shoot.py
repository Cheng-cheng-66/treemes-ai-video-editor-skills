#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from skills.factory_shoot.completion import (
    finalize_factory_export,
)
from skills.factory_shoot.runner import FactoryRenderRequest, run
from skills.factory_shoot.workflow import prepare_complete


def _add_render_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--captions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bgm", type=Path)


def _render(args: argparse.Namespace) -> dict[str, Path]:
    return run(
        FactoryRenderRequest(
            plan=args.plan,
            captions=args.captions,
            output_dir=args.output_dir,
            bgm=args.bgm,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the factory-shoot workflow")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser(
        "prepare",
        help="prepare the complete workflow, launch Jianying, then require UI and human gates",
    )
    _add_render_arguments(prepare)
    preview = commands.add_parser(
        "preview",
        help="explicitly render a technical NOT_DELIVERABLE preview",
    )
    _add_render_arguments(preview)
    finalize = commands.add_parser(
        "finalize",
        help="validate the real Jianying export and all completion evidence",
    )
    finalize.add_argument("--output-dir", type=Path, required=True)
    finalize.add_argument("--jianying-export", type=Path, required=True)
    finalize.add_argument("--ui-log", type=Path, required=True)
    finalize.add_argument("--human-review", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "finalize":
            result = finalize_factory_export(
                output_dir=args.output_dir,
                export=args.jianying_export,
                ui_log=args.ui_log,
                human_review=args.human_review,
            )
            payload = {
                "status": "COMPLETE",
                "final_video": str(result["final_video"]),
                "quality_report": str(result["quality_report"]),
                "final_delivery_manifest": str(result["final_delivery_manifest"]),
            }
        elif args.command == "preview":
            result = _render(args)
            payload = {
                "status": "NOT_DELIVERABLE_TECHNICAL_PREVIEW",
                "deliverable_video": None,
                "technical_preview": str(result["technical_preview"]),
                "quality_report": str(result["quality_report"]),
                "warning": (
                    "This file has not completed Jianying noise reduction, BGM, "
                    "sentence review, or final listening/viewing."
                ),
            }
        else:
            prepared = prepare_complete(
                FactoryRenderRequest(
                    plan=args.plan,
                    captions=args.captions,
                    output_dir=args.output_dir,
                    bgm=args.bgm,
                )
            )
            payload = {
                "status": prepared["status"],
                "deliverable_video": None,
                "technical_preview_is_not_deliverable": True,
                "completion_request": str(prepared["completion_request"]),
                "jianying_session": str(prepared["jianying_session"]),
                "jianying_application": prepared["jianying_application"],
                "next_action": prepared["next_action"],
            }
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
