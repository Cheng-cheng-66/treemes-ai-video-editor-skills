#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.case_study.reference_aligner import align_reference_to_source
from skills.case_study.source_analyzer import build_source_manifest
from skills.case_study.story_analyzer import analyze_story_units
from skills.case_study.transcript_pipeline import load_whisper_segments
from skills.case_study.visual_analyzer import build_contact_sheet, detect_scene_changes


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a long case source against a human-edited reference"
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--source-asr", required=True, type=Path)
    parser.add_argument("--reference-asr", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--alignment-only", action="store_true")
    args = parser.parse_args()

    output = args.output_dir.resolve()
    reports = output / "reports"
    frames = output / "frames"

    if args.alignment_only:
        source_manifest = json.loads(
            (reports / "source_manifest.json").read_text(encoding="utf-8")
        )
        reference_manifest = json.loads(
            (reports / "reference_manifest.json").read_text(encoding="utf-8")
        )
    else:
        source_manifest = build_source_manifest(args.source)
        reference_manifest = build_source_manifest(args.reference)
        write_json(reports / "source_manifest.json", source_manifest)
        write_json(reports / "reference_manifest.json", reference_manifest)

    source_segments = load_whisper_segments(args.source_asr)
    reference_segments = load_whisper_segments(args.reference_asr)
    write_json(
        reports / "transcript.machine.json",
        {
            "schema_version": 1,
            "source": {
                "path": str(args.source.resolve()),
                "segments": source_segments,
            },
            "reference": {
                "path": str(args.reference.resolve()),
                "segments": reference_segments,
            },
            "verbatim_release_subtitles": False,
            "human_listening_review_completed": False,
        },
    )

    source_story = analyze_story_units(source_segments)
    reference_story = analyze_story_units(reference_segments)
    write_json(
        reports / "story_analysis.json",
        {
            "schema_version": 1,
            "source_story": source_story,
            "reference_story": reference_story,
            "human_story_review_pass": None,
        },
    )

    alignment = align_reference_to_source(source_segments, reference_segments)
    write_json(reports / "reference_alignment.json", alignment)

    if args.alignment_only:
        return 0

    source_visual = build_contact_sheet(
        args.source.resolve(),
        source_manifest["duration_seconds"],
        output / "source_contact_sheet.jpg",
        frame_dir=frames / "source",
    )
    reference_visual = build_contact_sheet(
        args.reference.resolve(),
        reference_manifest["duration_seconds"],
        output / "reference_contact_sheet.jpg",
        frame_dir=frames / "reference",
    )
    source_visual["scene_detection"] = detect_scene_changes(args.source.resolve())
    reference_visual["scene_detection"] = detect_scene_changes(
        args.reference.resolve()
    )
    write_json(
        reports / "visual_analysis.json",
        {
            "schema_version": 1,
            "source": source_visual,
            "reference": reference_visual,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
