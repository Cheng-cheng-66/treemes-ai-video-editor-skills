# factory_demo_hybrid Jianying 7.9.0 template contract

## Environment contract

- Application: Jianying Pro
- Verified version: 7.9.0 build 366
- Template draft: configure with `JY_TEMPLATE_DRAFT_DIR` outside Git
- Output draft root: configure with `JY_PROJECTS_DIR` outside Git

Jianying draft metadata may be encrypted. Do not patch encrypted metadata or store login state.

## Fixed tracks

| Track | Slot | Setting |
|---|---|---|
| V1 | `media_slots/picture_master_no_audio.mp4` | locked picture, title and captions; no audio |
| A1 | `media_slots/dialogue_raw.wav` | native noise reduction on |
| A2 | `media_slots/ambience.wav` | initial volume -24 dB |
| A3 | `media_slots/bgm.wav` | initial volume -20 dB |

All tracks start at zero. Do not enable automatic captions, free-form titles, filters,
transitions or editorial changes.

The release repository does not include media slots, customer drafts or a last-run manifest.
After a supervised copy and media replacement, verify all four tracks, native audio settings,
export existence and full decode. Until then, keep `copied_draft_opened_in_jianying` unset.
