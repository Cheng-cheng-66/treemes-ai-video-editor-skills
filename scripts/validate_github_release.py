#!/usr/bin/env python3
"""Validate a media-free GitHub release candidate and write its manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SKILLS = ("video_diary", "factory_shoot", "case_study")
ROOT_SKILL_REQUIRED = (
    "SKILL.md",
    "agents/openai.yaml",
    "core/config.py",
    "scripts/doctor.py",
    "scripts/build_downloadable_skill_package.py",
    "scripts/run_video_diary.py",
    "scripts/run_case_study.py",
    "安装.command",
    "presets/video_diary/cover.yaml",
    "presets/factory_demo_hybrid/editorial.yaml",
    "presets/case_video/editorial.yaml",
)
REQUIRED_SKILL_ENTRIES = (
    "SKILL.md",
    "README.md",
    "presets",
    "schemas",
    "tests",
    "examples",
    "skill.json",
)
FORBIDDEN_SUFFIXES = {
    ".mp4", ".mov", ".mkv", ".avi", ".m4a", ".mp3", ".wav", ".aac",
    ".db", ".sqlite", ".pem", ".key", ".p12",
}
FORBIDDEN_PARTS = {
    ".git", ".venv", "__pycache__", "outputs", "runs", "logs", "cache",
    "caches", "models", "weights", "checkpoints", "experiments", "work",
    "reports", "JianyingPro", "CapCut", "drafts", "User Data", "Cache",
}
MACHINE_PREFIXES = ("/" + "Users/", "/" + "Volumes/")
HIGH_CONFIDENCE_SECRETS = (
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{20,}"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    values = [value for value in completed.stdout.split(b"\0") if value]
    return sorted(ROOT / value.decode("utf-8") for value in values)


def parse_skill_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"invalid SKILL.md frontmatter: {path.relative_to(ROOT)}")
    payload: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"invalid SKILL.md metadata line: {line}")
        payload[key.strip()] = value.strip()
    if set(payload) != {"name", "description"}:
        raise ValueError(f"SKILL.md must contain only name and description: {path}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", payload["name"]):
        raise ValueError(f"invalid Skill name: {payload['name']}")
    if not payload["description"]:
        raise ValueError(f"empty Skill description: {path}")
    return payload


def validate_manifest(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema_version", "id", "name", "status", "enabled", "entrypoint",
        "requires", "models",
    }
    missing = required - set(payload)
    if missing:
        raise ValueError(f"manifest missing {sorted(missing)}: {path}")
    if payload["schema_version"] != 1 or not isinstance(payload["enabled"], bool):
        raise ValueError(f"invalid manifest types: {path}")
    if payload["id"] != path.parent.name:
        raise ValueError(f"manifest id/directory mismatch: {path}")
    if not isinstance(payload["requires"], list) or not isinstance(payload["models"], list):
        raise ValueError(f"manifest requires/models must be arrays: {path}")
    if not payload["enabled"] and payload["entrypoint"] is not None:
        raise ValueError(f"disabled Skill must not expose an entrypoint: {path}")
    return payload


def validate_json_files(files: list[Path]) -> None:
    for path in files:
        if path.suffix.lower() != ".json":
            continue
        json.loads(path.read_text(encoding="utf-8"))
    for path in (ROOT / "schemas").glob("*.schema.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "$schema" not in payload or payload.get("type") != "object":
            raise ValueError(f"invalid JSON Schema envelope: {path}")


def validate_examples() -> None:
    from skills.case_study.contract import validate_job_contract
    from skills.video_diary.runner import validate_edit_plan

    validate_edit_plan(
        json.loads(
            (ROOT / "skills/video_diary/examples/edit_plan.json").read_text(
                encoding="utf-8"
            )
        )
    )
    validate_job_contract(
        json.loads(
            (ROOT / "skills/case_study/examples/job.json").read_text(
                encoding="utf-8"
            )
        )
    )


def scan_file(path: Path) -> list[str]:
    relative = path.relative_to(ROOT)
    errors: list[str] = []
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        errors.append(f"forbidden suffix: {relative}")
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        errors.append(f"forbidden path: {relative}")
    if path.stat().st_size > 5 * 1024 * 1024:
        errors.append(f"file exceeds 5 MiB: {relative}")
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return errors
    if any(prefix in text for prefix in MACHINE_PREFIXES):
        errors.append(f"machine absolute path: {relative}")
    if any(pattern.search(text) for pattern in HIGH_CONFIDENCE_SECRETS):
        errors.append(f"high-confidence secret pattern: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs/github_release/PACKAGE_MANIFEST.json",
    )
    args = parser.parse_args()

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if re.fullmatch(r"\d+\.\d+\.\d+-(?:alpha|beta|rc)\.\d+", version) is None:
        print(f"FAIL: release candidate must be a prerelease version; found {version}")
        return 1

    manifests = {}
    errors: list[str] = []
    for relative in ROOT_SKILL_REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing root Skill entry: {relative}")
    try:
        root_skill = parse_skill_frontmatter(ROOT / "SKILL.md")
        if root_skill.get("name") != "ai-video-editing-skills":
            errors.append("root Skill name must be ai-video-editing-skills")
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    for skill in SKILLS:
        root = ROOT / "skills" / skill
        for entry in REQUIRED_SKILL_ENTRIES:
            if not (root / entry).exists():
                errors.append(f"missing Skill entry: skills/{skill}/{entry}")
        try:
            parse_skill_frontmatter(root / "SKILL.md")
            manifests[skill] = validate_manifest(root / "skill.json")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))

    files = candidate_files()
    try:
        validate_json_files(files)
        validate_examples()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    for path in files:
        errors.extend(scan_file(path))

    if manifests.get("factory_shoot", {}).get("enabled") is not False:
        errors.append("factory_shoot must remain disabled in this release")

    if errors:
        for error in sorted(set(errors)):
            print(f"FAIL: {error}")
        return 1

    rows = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    ]
    payload = {
        "schema_version": 1,
        "version": version,
        "release_channel": "beta",
        "skills": {
            key: {"status": value["status"], "enabled": value["enabled"]}
            for key, value in manifests.items()
        },
        "contains_real_media": False,
        "file_count": len(rows),
        "files": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: {len(rows)} release files validated")
    print(f"PASS: manifest written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
