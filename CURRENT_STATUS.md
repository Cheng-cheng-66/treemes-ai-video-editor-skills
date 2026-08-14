# Current status

Updated: 2026-08-14

## Release identity

- Version: `0.10.0-beta.3`
- Channel: `beta`
- Stable release: not created
- Release decision: `PRE_RELEASE_ONLY`

## Skill status

- `video_diary`: enabled Beta; source aspect inheritance, fixed templates, verbatim captions,
  Jianying voice-only `+10 dB` and BGM `-8 dB` contracts are present.
- `factory_shoot`: planned/experimental and disabled. Product-promotion videos map to this
  Skill. Presets and workflow rules are included; historical customer-specific prototypes are
  excluded from the release snapshot.
- `case_study`: enabled Beta analysis. Source analysis, transcript alignment, sync zones,
  pause analysis and story planning are present; first formal render acceptance remains open.

## Release boundaries

- The repository root is the only supported Codex installation unit. Installing an individual
  scene directory is unsupported because shared runtime modules and presets live at the root.
- The public macOS ZIP provides a double-click installer; package structure, checksum,
  executable mode, isolated installation and installed strict-doctor execution are required
  release checks. The official Skill-installer remains an optional maintainer path.
- No raw media, rendered video, customer image, audio, model, Jianying draft, runtime report,
  credential, login state or machine-local configuration is included.
- Automatic technical checks do not replace complete human listening, subtitle, lip-sync,
  terminology, privacy, fact and narrative review.
- Unreviewed human fields remain `null`, `NOT_REVIEWED`, or
  `MANUAL_REVIEW_REQUIRED`.
- A beta tag may be created only after package validation, full tests, synthetic decode,
  security scan and clean-install verification pass.

## Known gates

- Another physical Mac installation and real-source shadow test: `NOT_REVIEWED`.
- Video-diary final listening and peak safety for each export: manual gate.
- Factory-shoot production entrypoint: disabled.
- Case-study first production render and director approval: pending.
