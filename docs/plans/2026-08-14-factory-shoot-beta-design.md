# Factory Shoot Beta execution design

Date: 2026-08-14

## Context and decision

The public package incorrectly exposes factory shooting as `planned`, `enabled=false`, with no
entrypoint. That state was a packaging safeguard, not a user decision, and conflicts with the
requested three-workflow product. Three fixes were considered: flip the flag only; bundle a
fully automatic ASR/CV stack; or publish the already-proven hybrid route as a deterministic Beta
runner. A flag-only change would advertise a callable workflow that still cannot execute. A
large model stack would add new dependencies and repeat unaccepted research. The selected option
is the hybrid runner: Codex performs editorial analysis and writes a traceable plan; Python and
FFmpeg validate it, build the picture/dialogue/ambience/BGM assets, render an open-tool fallback
preview, and produce automatic and human-review reports. Jianying remains the supervised native
audio finishing stage and may not change the approved picture timeline, captions, or title.

## Contract and data flow

The input is a source movie, a JSON edit plan, and verbatim final-timeline captions. Every
picture segment declares its source range, sync zone, dialogue source ranges, visual type,
speaker, mouth visibility, next sync anchor, reason, risk, and confidence. `A_SYNC_LOCKED`
requires identical picture and dialogue ranges. `B_SYNC_FLEX` permits bounded dialogue
compression only when a later A anchor exists. `C_AUDIO_FREE` permits independent dialogue
pause removal while keeping one continuous picture range. Declared `D_ACTION_LOCKED` anchors
must sit wholly inside one continuous picture segment and may not cross a picture cut.

The run writes the five required planning artifacts and the shared hybrid assets:
`picture_master_no_audio.mp4`, `dialogue_raw.wav`, `ambience.wav`, `bgm.wav`, `subtitles.ass`,
`title.png`, `edit_plan.json`, `sync_zones.json`, and `action_anchors.json`. It also writes a
stereo `fallback_preview.mp4`, a Jianying four-track import manifest, a sentence-by-sentence
review form, and `quality_report.json`. Source media is read-only and outputs stay under the
selected run directory.

## Acceptance boundary

Automatic checks validate source hash, edit-plan structure, aspect inheritance, three title
frames, single-line subtitle width using the real font, full decode, A-zone structural sync,
action-anchor coverage, track durations, stereo output, black frames, and isolated flash frames.
They may produce a renderable Beta candidate, but they must not fill human fields such as actual
word match, professional terminology, perceptual continuity, denoise naturalness, lip sync, or
story completeness. Those remain `null` until reviewed. A Jianying export is never claimed from
the open fallback render. Enabling the Skill therefore means “the workflow executes and produces
a candidate plus evidence,” not “every human acceptance gate is automatically passed.”
