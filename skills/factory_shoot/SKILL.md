---
name: factory-shoot
description: Plan factory-floor and product-promotion edits using narrative completeness, protected lip-sync and action zones, continuous ambience, professional-term safeguards, deterministic picture timelines, and Jianying audio finishing. Use for factory demonstrations, shop-floor interviews, tablets, dashboards, equipment, and production-line footage; currently planned and disabled for unattended execution.
---

# Factory shoot

Read `skill.json` first. Because `enabled` is `false`, do not execute an unattended production
render or silently add an entrypoint.

## Planning workflow

1. Inventory long footage and select one complete topic with a clear opening, evidence and conclusion.
2. Classify every relevant range:
   - `A_SYNC_LOCKED`: visible frontal speech; lock picture to voice.
   - `B_SYNC_FLEX`: distant or unclear mouth; allow limited compression and restore sync before A.
   - `C_AUDIO_FREE`: tablet, dashboard, equipment or production line; compress voice while keeping picture continuous.
   - `D_ACTION_LOCKED`: tap, swipe, page transition or equipment action; never cut through the action.
3. Produce a deterministic shared edit plan, sync zones and action anchors.
4. Protect continuous ambience and use 20–60 ms voice crossfades at audio cuts.
5. Match the mentioned function to the correct system or equipment picture.
6. Generate the opening title only; do not import the video-diary persistent header.
7. Apply large, spaced, verbatim subtitles and protect all product names and MES terms.
8. When manually approved, use the four-track Jianying contract: picture, dialogue, ambience and BGM.
9. Run FFmpeg technical QC and full human listening/viewing.

## Hard rules

- Never cut picture at every audio pause.
- Never break a complete click, swipe or page transition.
- Never paraphrase synchronous subtitles.
- Never mark lip sync, word loss or perceptual continuity as passed without human review.
- Never enable this Skill merely because historical experimental evidence exists.

## Fallback

If the executable route or required evidence is unavailable, output only an edit plan and mark
the job `BLOCKED_DISABLED_SKILL`. Do not claim a finished production video.
