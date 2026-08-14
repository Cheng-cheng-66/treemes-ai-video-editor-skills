# Downloadable macOS Skill package design

Date: 2026-08-14

## Goal

Let a non-technical macOS user install the public AI video-editing Skill from GitHub without
copying a Codex prompt or running a Terminal command. The supported path is:

1. Download the release ZIP.
2. Unzip it.
3. Double-click `安装.command`.
4. Reopen Codex and describe the video task.

Codex does not automatically discover arbitrary ZIP files in Downloads, so a literal
download-only install is not a reliable product behavior. The double-click installer is the
smallest deterministic GitHub-only interaction.

## Package format

Each release asset is named
`AI-Video-Editing-Skill-macOS-v<VERSION>.zip` and contains exactly one top-level directory:
`ai-video-editing-skills/`. That directory contains the complete root Skill, including
`SKILL.md`, `agents/openai.yaml`, the shared runtime and scene workflows, plus
`安装.command`.

The package is built only from Git-tracked files. Runtime media, credentials, models, caches,
logs, reports and local configuration remain excluded. A SHA-256 sidecar is published beside
the ZIP.

## Installer behavior

`安装.command` resolves its own unpacked directory and installs it to
`${CODEX_HOME:-$HOME/.codex}/skills/ai-video-editing-skills`. It validates the source structure,
refuses an unexpected or symbolic-link destination, copies into a temporary staging directory,
and preserves any prior installation as a timestamped backup before activating the new copy.

After installation it runs the bundled strict doctor. Missing FFmpeg, Node.js, Jianying access,
models or account entitlements remain explicit setup or human gates; installation must not turn
them into false success claims.

## Verification

Automated tests build and inspect the ZIP, require one top-level directory, verify required
Skill files and executable mode, validate the checksum, and install into an isolated temporary
`CODEX_HOME`. Release acceptance additionally downloads the published asset anonymously,
checks its checksum, installs it into another empty destination, validates the installed Skill,
and runs the strict doctor.

This change is released as `v0.10.0-beta.3`; earlier tags remain immutable.
