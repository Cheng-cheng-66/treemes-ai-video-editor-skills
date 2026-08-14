# Factory Shoot Beta Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the disabled factory-shoot placeholder with a validated, deterministic hybrid
Beta workflow that builds four-track assets, a fallback preview, and honest quality evidence.

**Architecture:** Keep editorial judgment in a JSON plan and deterministic media operations in
Python/FFmpeg. Validate sync-zone and action invariants before any render, then generate shared
assets, an open preview, and separate automatic/human-review reports.

**Tech Stack:** Python 3.11+, FFmpeg/ffprobe, Pillow, unittest, Codex Skill manifests.

---

### Task 1: Define the executable factory contract

**Files:**
- Create: `skills/factory_shoot/contract.py`
- Create: `tests/test_factory_shoot_contract.py`

1. Write failing tests for ordered picture ranges, source hash, all required action fields,
   A-zone exact source sync, C-zone independent dialogue ranges, return anchors, and protected
   D-action ranges.
2. Run `python3 -m unittest tests.test_factory_shoot_contract -v`; expect failures because the
   contract module does not exist.
3. Implement normalized dataclasses/dictionaries and explicit validation errors.
4. Re-run the focused tests; expect all to pass.
5. Commit the contract and tests.

### Task 2: Build deterministic four-track assets

**Files:**
- Create: `skills/factory_shoot/renderer.py`
- Create: `tests/test_factory_shoot_renderer.py`

1. Write a synthetic FFmpeg fixture and failing test for portrait/landscape inheritance,
   continuous C-zone picture, A-zone structural sync, three-frame title overlay, ASS captions,
   PCM dialogue/ambience/BGM assets, and stereo fallback preview.
2. Implement FFmpeg filter graphs that trim/concatenate picture independently from dialogue,
   use 20–60 ms dialogue crossfades, pad each dialogue segment to its picture duration, loop a
   declared speech-free ambience sample, and optionally convert BGM.
3. Generate `title.png` and measure captions with the configured font before rendering.
4. Run the focused test and fully decode every generated media file.
5. Commit the renderer and tests.

### Task 3: Produce planning and quality evidence

**Files:**
- Create: `skills/factory_shoot/quality.py`
- Create: `tests/test_factory_shoot_quality.py`

1. Write failing tests that require the five planning files, shared contract assets,
   `quality_report.json`, and a review template with protected fields set to `null`.
2. Implement technical probes, duration/channel/geometry checks, black-frame and isolated-flash
   detection, subtitle overflow counts, source hash evidence, action/sync structural checks, and
   full decode.
3. Keep word match, professional terms, actual lip sync, story completeness, Jianying audio, and
   perceptual continuity as human fields; never infer them from automatic checks.
4. Run focused tests and commit.

### Task 4: Enable and route the Skill

**Files:**
- Create: `skills/factory_shoot/runner.py`
- Create: `scripts/run_factory_shoot.py`
- Modify: `skills/factory_shoot/skill.json`
- Modify: `skills/factory_shoot/SKILL.md`
- Modify: `SKILL.md`
- Modify: `agents/openai.yaml`
- Modify: `scripts/doctor.py`
- Modify: `README.md`
- Modify: existing release tests

1. Add failing discovery/CLI/doctor tests that expect `enabled=true` and a callable entrypoint.
2. Implement `run(request)` and CLI arguments for plan, captions, output directory, optional BGM,
   and candidate rendering.
3. Route factory requests to the executable Beta workflow and document supervised Jianying
   finishing instead of blocking the job.
4. Validate root and nested `SKILL.md`, regenerate UI metadata, and run all tests.
5. Commit.

### Task 5: Package and publish beta.4

**Files:**
- Modify: `VERSION`, `CHANGELOG.md`, `CURRENT_STATUS.md`, release/acceptance docs
- Create: `docs/releases/v0.10.0-beta.4.md`

1. Set `0.10.0-beta.4`, update the package validator and download documentation.
2. Run the full suite, synthetic factory render, video-diary smoke, release scan, and Skill
   validation.
3. Build the macOS ZIP and checksum, install into an isolated `CODEX_HOME`, and run the factory
   CLI from the installed copy.
4. Forward-test a factory request against the installed Skill without exposing the intended
   answer; review that it selects the executable route and retains human gates.
5. Push the branch, fast-forward `main`, tag and publish the pre-release assets.
6. Download anonymously, verify checksum, install, execute the synthetic factory workflow, and
   report the exact public links and remaining human gates.
