# Jianying complete factory workflow

Use this procedure after `scripts/run_factory_shoot.py prepare` returns
`BLOCKED_PENDING_JIANYING_UI_AND_HUMAN_REVIEW`.

## Required control surface

Use Codex Desktop's `computer-use:computer-use` Skill to operate Jianying. If computer control is
not available, stop and report `BLOCKED_JIANYING_UI_CONTROL_UNAVAILABLE`. Do not return the
technical preview as a substitute. Fixed coordinates alone are forbidden; confirm visible or
accessibility state after every critical action.

## Timeline

1. Confirm the launched app has bundle ID `com.lemon.lvpro` and version `7.9.0`.
2. Create or copy a clean project without changing the approved picture timeline.
3. Import the absolute paths from `completion_request.json`:
   - V1: `picture_master_no_audio.mp4`;
   - A1: `dialogue_raw.wav`;
   - A2: `ambience.wav`;
   - A3: `bgm.wav`.
4. Put all four assets at 00:00:00. Confirm V1 contains no source audio.
5. Confirm the burned title and subtitles are visible. Do not generate Jianying captions.
6. Select A1 and enable Jianying native audio noise reduction. Preserve a screenshot showing the
   enabled state.
7. Set the factory initial mix to A2 `-24 dB` and A3 `-20 dB`. If A3 is silent because no licensed
   local BGM was supplied, select a licensed BGM inside the logged-in Jianying account, record its
   displayed identity, and keep it clearly below dialogue.
8. Listen at the beginning, a middle speech cut, and the end. Confirm there is no metallic,
   watery, robotic, clipped, or noise-floor jump artifact.
9. Export a real stereo master under `RUN/jianying/exports/`. Do not overwrite source media.
10. Preserve screenshots named or mapped as `timeline`, `subtitles`, `native_denoise`, `bgm_mix`,
    and `export_complete`.

## Action log

Write `RUN/jianying/ui_action_log.json` with schema version 1, the bundle ID, displayed version,
and confirmed events:

```json
{
  "schema_version": 1,
  "application_bundle_id": "com.lemon.lvpro",
  "application_version": "7.9.0",
  "events": [
    {"id": "app_opened", "status": "confirmed"},
    {"id": "tracks_imported", "status": "confirmed"},
    {"id": "timeline_alignment_confirmed", "status": "confirmed"},
    {"id": "subtitles_visible", "status": "confirmed"},
    {"id": "native_denoise_enabled", "status": "confirmed"},
    {"id": "bgm_present", "status": "confirmed"},
    {"id": "audio_mix_confirmed", "status": "confirmed"},
    {"id": "export_completed", "status": "confirmed"}
  ],
  "screenshots": {
    "timeline": "ABSOLUTE_PATH",
    "subtitles": "ABSOLUTE_PATH",
    "native_denoise": "ABSOLUTE_PATH",
    "bgm_mix": "ABSOLUTE_PATH",
    "export_complete": "ABSOLUTE_PATH"
  }
}
```

## Final review and finalization

Fill the generated `human_listening_review.json` from actual playback. Every sentence must record
the heard dialogue, subtitle match, professional-term result, word loss, and visible-mouth sync.
Every whole-video protected field must be reviewed. Then run:

```bash
python3 scripts/run_factory_shoot.py finalize \
  --output-dir RUN \
  --jianying-export RUN/jianying/exports/FINAL.mp4 \
  --ui-log RUN/jianying/ui_action_log.json \
  --human-review RUN/human_listening_review.json
```

Only a `COMPLETE` response containing `final_video` is deliverable.
