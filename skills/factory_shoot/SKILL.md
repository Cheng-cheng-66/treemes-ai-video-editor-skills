---
name: factory-shoot
description: Analyze and execute Beta factory-floor and product-promotion edits using narrative completeness, protected lip-sync and action zones, continuous ambience, professional-term safeguards, deterministic picture timelines, four-track assets, fallback rendering, Jianying audio finishing, and honest quality gates. Use for factory demonstrations, shop-floor interviews, tablets, dashboards, equipment, and production-line footage.
---

# Factory shoot

Treat the directory containing this file as the scene Skill directory and the repository root as
two parents above it. Read `skill.json` and both `presets/factory_demo/` and
`presets/factory_demo_hybrid/` before planning.

## Execute the Beta workflow

1. Inspect the source read-only, inherit its aspect ratio, and select one complete topic with a
   clear premise, product evidence, and conclusion. Do not begin with a dangling reference such
   as “these three problems” unless all three problems remain in the edit.
2. Transcribe the intended retained speech verbatim. Correct recognition errors only against
   actual audio; protect customer, product, protocol, MES and factory terms.
3. Classify every selected picture range:
   - `A_SYNC_LOCKED`: visible frontal speech; lock picture to voice.
   - `B_SYNC_FLEX`: distant or unclear mouth; allow limited compression and restore sync before A.
   - `C_AUDIO_FREE`: tablet, dashboard, equipment or production line; compress voice while keeping picture continuous.
   - `D_ACTION_LOCKED`: tap, swipe, page transition or equipment action; never cut through the action.
4. Write a plan matching `examples/edit_plan.json` and final-timeline captions matching
   `examples/captions.json`. Set `title.approved=true` only after the title wording is selected;
   a title may summarize, but captions may not.
5. Run complete preflight: `python3 scripts/doctor.py --strict --workflow factory_shoot
   --complete`. Stop on every failure.
6. Run `python3 scripts/run_factory_shoot.py prepare --plan PLAN --captions CAPTIONS
   --output-dir RUN`. Add `--bgm FILE` only when the music is licensed and locally available.
   This command generates four-track assets and launches Jianying, but returns no deliverable.
7. Read `references/jianying_complete_workflow.md` completely. Use Codex Desktop computer control
   to import V1/A1/A2/A3, enable native dialogue noise reduction, confirm subtitles, add/confirm
   BGM, mix, export, and retain visual evidence. Do not stop after merely opening Jianying.
8. Complete the generated sentence review and whole-video listening/viewing review from actual
   playback.
9. Run the documented `finalize` command. Only its `COMPLETE` response and `final_video` path may
   be delivered.

## Hard rules

- Never cut picture at every audio pause.
- Never break a complete click, swipe or page transition.
- Never paraphrase synchronous subtitles.
- Never mark lip sync, word loss or perceptual continuity as passed without human review.
- Never turn unreviewed word match, lip sync, action completeness, denoise quality, BGM balance,
  story completeness, or perceptual continuity from `null` into a pass.
- Never deliver `technical_preview_NOT_DELIVERABLE.mp4` as a finished or usable final video.
- Never switch to ChatCut, an open preview, or another renderer merely because FFmpeg or Jianying
  is missing.

## Fallback

Preview mode exists only for a user who explicitly asks for a technical preview. Run the `preview`
subcommand and label its result `NOT_DELIVERABLE`. If the user asked for the complete workflow,
missing FFmpeg, Jianying, login, entitlement, BGM, computer control, export, subtitles, or review
must block completion; never substitute the preview.
