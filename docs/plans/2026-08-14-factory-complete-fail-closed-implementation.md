# Factory complete workflow fail-closed implementation plan

1. Add failing tests for installation dependency blocking, explicit preview mode, and complete
   finalization evidence.
2. Add factory complete preflight and finalization contracts.
3. Rename and gate the open preview; update CLI to explicit `prepare`, `preview`, and `finalize`
   stages with complete behavior as the documented default.
4. Add Jianying launch/preflight helper and low-freedom UI evidence instructions for Codex
   Desktop computer control.
5. Make the macOS installer bootstrap dependencies when Homebrew exists and fail before success
   when media dependencies remain missing.
6. Update Skill routing, presets, doctor, package validation, status, version, and release notes.
7. Run unit, smoke, Skill, clean-install, missing-dependency, and independent invocation tests.
8. Publish a new prerelease only after anonymous download and installed-copy verification pass.
