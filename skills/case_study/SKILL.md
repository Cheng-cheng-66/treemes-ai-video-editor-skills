---
name: case-study
description: Analyze long customer-case videos into evidence-grounded chapters, transcript and pause maps, sync zones, story units, edit plans, bilingual subtitle packages, terminology checks, and quality reports. Use for MES customer interviews and case studies that require shortening while preserving facts and speaker meaning; rendering still requires first-case and director acceptance.
---

# Case study

## Workflow

1. Confirm authorization and keep the source read-only.
2. Build a source manifest, audio transcript, visual samples, pause map and sync-zone analysis.
3. Divide the narrative into problem, solution, implementation and result; retain evidence for every story unit.
4. Propose a target duration or shortening ratio without deleting necessary context.
5. Protect visible speech and complete actions; document every cut reason and risk.
6. Preserve customer names, figures and product claims only when verified. Mark uncertain facts for review.
7. Build Chinese captions from final audio verbatim. Translate English by actual context, speaker intent and MES terminology rather than literal word replacement.
8. Add the opening English title and bilingual layout without covering existing labels.
9. Run automatic QC, then perform director, customer-fact, privacy, full listening and language review.

## Outputs

Produce source analysis, transcript, pause analysis, sync zones, story analysis, edit plan, subtitle
assets and quality report in the job directory. Do not call an analysis-only result a final render.

## Hard rules

- Do not invent or normalize customer facts, figures, identities or product capabilities.
- Do not shorten by destroying the question–answer context or conclusion.
- Do not translate mechanically or replace professional terms with approximate words.
- Do not set human review fields to zero or true without actual review evidence.
- Do not publish without privacy and authorization approval.

## Failure and fallback

- Missing model or dependency: run `scripts/doctor_case_study.py` and report the exact blocker.
- Low-confidence transcript or fact: retain the original segment and request human confirmation.
- Render gate not accepted: deliver the plan/subtitle review package only and mark it non-final.

Use `scripts/run_case_study.py analyze` with a job matching the canonical schema.
