---
name: video-diary
description: Analyze and render branded video-diary footage with source-aspect inheritance, fixed cover and persistent header templates, verbatim synchronized captions, pause cleanup, Jianying audio finishing, and explicit automatic plus human quality gates. Use for MES diary or other recurring branded diary videos.
---

# Video diary

## Workflow

1. Probe the source with ffprobe; inherit landscape or portrait unless conversion is explicitly authorized.
2. Transcribe and protect the speaker's exact words and professional terms.
3. Build a traceable edit plan; shorten only judged pauses and keep playback speed at 1.00 unless approved.
4. Apply the locked opening cover and persistent header. Change only declared variables such as date and Day.
5. Render single-line captions inside the configured safe area. Split long speech at a real semantic pause; never paraphrase or auto-shrink.
6. Render the deterministic picture timeline and run automatic QC.
7. Apply the Jianying voice-only and BGM contract when the entitled desktop environment is available.
8. Watch and listen to the entire final export. Keep unreviewed fields unset.

## Inputs and outputs

- Inputs: read-only source video, `edit_plan.json`, verbatim caption JSON, date and Day.
- Outputs: rendered video, actual plan, caption asset and quality report under a runtime directory.
- Presets: follow `presets/README.md` in this Skill.

## Hard rules

- Do not rewrite, summarize, shorten, reorder or invent spoken words.
- Do not mix factory-shoot or case-study presets into this Skill.
- Do not convert aspect ratio without a recorded user authorization.
- Do not treat automatic decode, width or black-frame checks as human approval.
- Do not package Jianying account state or licensed BGM media.

## Failure and fallback

- Unknown/square orientation: block rendering and request an explicit target.
- Missing Jianying entitlement: deliver only the correctly named no-Jianying-audio candidate and mark the audio stage blocked.
- Subtitle or audio uncertainty: retain `MANUAL_REVIEW_REQUIRED`; do not invent zero errors.

Run `scripts/doctor.py --strict`, then use `scripts/run_video_diary.py`.
