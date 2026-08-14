# Beta release acceptance matrix

Version: `0.10.0-beta.4`

Automatic status uses `NOT_RUN`, `PASS`, `FAIL` or `BLOCKED`. Human status uses
`NOT_REVIEWED`, `PASS`, `FAIL` or `NOT_APPLICABLE`.

| Gate | Required for beta tag | Evidence |
|---|---:|---|
| bootstrap | PASS | generated local test report |
| doctor --strict | PASS | generated local test report |
| full automatic tests | PASS | generated local test report |
| Skill manifest and schema checks | PASS | GitHub release validator |
| synthetic render and full decode | PASS | smoke test |
| security and large-file scan | PASS | generated security report |
| clean clone/install | PASS | generated clean-install report |
| downloadable ZIP shape/checksum/install | PASS | package tests and isolated CODEX_HOME |
| real video-diary listening | manual gate | may remain NOT_REVIEWED in beta |
| factory-shoot synthetic candidate | PASS | four tracks, fallback preview, QC and full decode |
| factory-shoot Jianying + human acceptance | manual gate | must remain NOT_REVIEWED until executed |
| case-study first formal render | pending | must not be represented as approved |

A beta tag is allowed only when every automatic gate passes and every remaining manual gate is
disclosed. A stable tag, default production update or unattended enablement remains prohibited.
