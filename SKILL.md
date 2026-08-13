---
name: ai-video-editing-skills
description: Route AI-assisted video editing requests to the existing video-diary, factory-shoot, or case-study workflows. Use for installing, diagnosing, planning, rendering, quality-checking, updating, or rolling back this repository without changing approved editing behavior or exposing customer media.
---

# AI Video Editing Skills

1. Read `VERSION`, the selected Skill's `skill.json`, and its `SKILL.md`.
2. Refuse to enable a disabled Skill implicitly.
3. Keep source media read-only and store runtime data outside Git.
4. Produce an explicit edit plan before rendering.
5. Run automatic QC, then preserve all human review gates as separate states.
6. Never change spoken meaning, professional terms, customer facts, or authorization status.
7. Use `scripts/doctor.py --strict` before execution and after update or rollback.

Select exactly one scene Skill:

- `skills/video_diary/SKILL.md`
- `skills/factory_shoot/SKILL.md`
- `skills/case_study/SKILL.md`

If no scene matches, stop and request a classification decision. Do not combine presets across
Skills.
