---
name: ai-video-editing-skills
description: Install, diagnose, and run the bundled AI video-editing workflows for video diaries, factory footage, product demonstrations, and MES customer case studies. Use when Codex must analyze footage, plan or render an edit, preserve verbatim speech and professional terms, create Chinese or English subtitles, apply approved templates, coordinate Jianying audio finishing, or produce automatic and human-review quality reports.
---

# AI Video Editing Skills

Treat the directory containing this file as `SKILL_ROOT`. Resolve every bundled path from
`SKILL_ROOT`; never assume the current working directory is the repository.

## First use

1. Read `VERSION`. Use `SKILL_ROOT/.venv/bin/python` when it exists; otherwise use `python3`.
2. For a complete factory request, run `scripts/doctor.py --strict --workflow factory_shoot
   --complete` before analyzing or rendering. Missing FFmpeg, ffprobe, subtitles, or Jianying is a
   blocker; never silently select another renderer.
3. On macOS, repair missing media commands with `scripts/macos_preflight.py --install-missing
   --require-jianying`, then run `scripts/install_macos.sh` and repeat the complete doctor.
4. For other workflows, run `scripts/doctor.py --strict` and follow their scene instructions.
5. Report any missing external application, model, account entitlement, or human review as a
   blocker. Do not invent completion.

## Route exactly one workflow

- Video diary: read `skills/video_diary/SKILL.md` and `skill.json`; this Beta route is enabled.
- Factory shoot or product demonstration: read `skills/factory_shoot/SKILL.md` and
  `skill.json`; complete mode is the default. It must continue through actual Jianying UI audio
  processing, export, evidence, and review. Technical preview is allowed only when the user
  explicitly requests a preview and may never be returned as the final video.
- Customer case study: read `skills/case_study/SKILL.md` and `skill.json`; analysis is enabled,
  while rendering, facts, privacy, models, translation, and director acceptance retain their
  declared gates.

If no scene matches, request classification instead of combining presets.

## Universal rules

1. Keep source media read-only and put runtime data under the configured runtime directory.
2. Produce a traceable edit plan before rendering or shortening content.
3. Never rewrite spoken meaning, professional terms, customer facts, or authorization status.
4. Use only the selected workflow's presets; never mix scene templates.
5. Run automatic QC, then preserve listening, viewing, fact, privacy, lip-sync, and language
   review as separate human gates.
6. Do not claim Jianying processing unless the entitled desktop application actually completed
   and exported the file.
7. Do not return any path containing `NOT_DELIVERABLE` as a completed video.
