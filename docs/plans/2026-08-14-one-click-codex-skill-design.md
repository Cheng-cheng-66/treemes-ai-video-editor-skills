# One-click Codex Skill distribution design

Date: 2026-08-14

## Goal

Publish the repository as one installable Codex Skill. A user should be able to paste one
GitHub installation request into Codex, start a new turn, and invoke
`$ai-video-editing-skills` without cloning the repository or understanding its Python package
layout.

## Decision

Use the repository root as a single umbrella Skill. The root already contains the shared
`core/`, `presets/`, `scripts/`, `schemas/`, and the three scene workflows. Installing each
scene directory independently is invalid because those directories depend on shared root
resources. Duplicating the runtime into three packages would increase drift and maintenance
risk. The official Skill installer supports installing repository path `.` with an explicit
name, so the root package can remain the only distribution unit.

## Behavior

The installed Skill routes a request to video diary, factory shoot, or case study. It resolves
all files relative to its own installed directory and never assumes the user's current working
directory. On first use it runs the bundled doctor and, when needed, the bundled platform
bootstrap. Factory shoot remains disabled for unattended production; case study retains model,
fact, privacy, and director gates.

## Verification

Release validation must require the root `SKILL.md`, `agents/openai.yaml`, shared runtime,
scene Skill manifests, and entry scripts. Acceptance uses the official installer against the
public tag into an empty destination, runs Skill validation and the strict doctor outside the
repository, and confirms anonymous homepage, API, archive, and clone access. The fix is released
as `v0.10.0-beta.2`; the previous tag remains immutable.
