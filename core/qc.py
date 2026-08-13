from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from core.process import run_command


class CheckStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    status: CheckStatus
    detail: str
    evidence: dict[str, Any] | None = None


def overall_status(checks: Iterable[CheckResult]) -> CheckStatus:
    values = [check.status for check in checks]
    if CheckStatus.FAIL in values:
        return CheckStatus.FAIL
    if CheckStatus.MANUAL_REVIEW_REQUIRED in values:
        return CheckStatus.MANUAL_REVIEW_REQUIRED
    return CheckStatus.PASS


def write_report(path: Path, checks: list[CheckResult], **metadata: Any) -> Path:
    payload = {
        **metadata,
        "status": overall_status(checks),
        "checks": [asdict(check) for check in checks],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def probe_video(path: Path, ffprobe: str = "ffprobe") -> dict[str, Any]:
    result = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,"
            "sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"ffprobe failed for {path}")
    return json.loads(result.stdout)


def full_decode(path: Path, ffmpeg: str = "ffmpeg") -> CheckResult:
    result = run_command(
        [ffmpeg, "-hide_banner", "-v", "error", "-i", str(path), "-f", "null", "-"],
        timeout=600,
    )
    if result.returncode == 0:
        return CheckResult("full_decode", CheckStatus.PASS, "full decode completed")
    return CheckResult(
        "full_decode",
        CheckStatus.FAIL,
        result.stderr.strip() or "FFmpeg decode failed",
    )
