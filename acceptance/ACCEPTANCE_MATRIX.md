# Beta release acceptance matrix

Version: `0.10.0-beta.1`

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
| real video-diary listening | manual gate | may remain NOT_REVIEWED in beta |
| factory-shoot production entrypoint | disabled | must not be represented as ready |
| case-study first formal render | pending | must not be represented as approved |

A beta tag is allowed only when every automatic gate passes and every remaining manual gate is
disclosed. A stable tag, default production update or unattended enablement remains prohibited.
