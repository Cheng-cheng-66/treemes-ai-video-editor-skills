# Standard real-source acceptance

No real source path is stored in Git. Provide an authorized, read-only source at runtime:

```bash
export VIDEO_DIARY_STANDARD_SOURCE=/mounted/read-only/source.mov
python3 acceptance/run_acceptance_checks.py
```

Before running, record file size, SHA-256, ffprobe JSON, read permission, modification time and
the authorization boundary in an ignored local report. Verify the source SHA-256 is unchanged
after the test. Never copy, overwrite or modify the source.
