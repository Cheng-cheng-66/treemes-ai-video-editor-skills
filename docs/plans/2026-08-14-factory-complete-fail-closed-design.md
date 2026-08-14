# Factory complete workflow fail-closed design

Date: 2026-08-14

## Problem

The public Beta allowed `fallback_preview.mp4` to be delivered when FFmpeg setup, subtitles,
Jianying native noise reduction, BGM, export, and listening review were incomplete. The macOS
installer also activated the Skill after strict doctor failure. A recipient therefore received a
rough preview as if it were a complete factory edit.

## Decision

Use two explicit modes and make complete mode the default.

- `complete`: fail closed. Require FFmpeg/ffprobe, a non-empty caption timeline, Jianying 7.9.0,
  a real Jianying export, UI evidence, and completed human review before returning a deliverable.
- `preview`: opt-in only. Produce a watermarked/named technical preview and report it as
  `NOT_DELIVERABLE`; never call it a finished video.

The renderer continues to create deterministic picture and four-track assets. Codex Desktop must
then use visual/state-confirmed computer control to open Jianying, import V1/A1/A2/A3, enable
native noise reduction on A1, preserve burned subtitles and title, mix, export, and retain
screenshots plus an action log. A finalizer verifies the export and evidence before it can be
reported as complete.

## Installation and errors

The double-click installer must not print success when required media commands are absent. When
Homebrew is already installed it may install missing FFmpeg or Node automatically; otherwise it
must stop with a clear dependency blocker. Jianying absence is a complete-workflow blocker, not a
reason to silently fall back.

## Acceptance

- missing FFmpeg causes installation/preflight failure;
- default factory CLI never returns `fallback_preview` as a deliverable;
- preview requires an explicit flag and is named `technical_preview_NOT_DELIVERABLE.mp4`;
- complete finalization requires a decodable Jianying export, required screenshots/action log,
  non-empty subtitles, native denoise evidence, BGM evidence, and all human review fields;
- no final output path is emitted until every complete-workflow gate passes.
