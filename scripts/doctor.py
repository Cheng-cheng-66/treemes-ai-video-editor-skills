#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import AppConfig, create_runtime_dirs, load_config
from core.process import executable_path, first_version_line
from core.qc import CheckResult, CheckStatus, overall_status
from core.skills import discover_skills, find_boundary_violations
from skills.factory_shoot.completion import (
    find_jianying_application,
    inspect_jianying_application,
)


def _result(
    check_id: str,
    passed: bool,
    pass_detail: str,
    fail_detail: str,
) -> CheckResult:
    return CheckResult(
        check_id,
        CheckStatus.PASS if passed else CheckStatus.FAIL,
        pass_detail if passed else fail_detail,
    )


def _font_paths(config: AppConfig) -> list[Path]:
    profile = str(config.video_diary.get("font_profile", "auto"))
    if profile == "auto":
        profile = "windows" if platform.system() == "Windows" else "macos"
    fonts = config.video_diary.get("fonts", {}).get(profile, {})
    return [Path(str(value)).expanduser() for value in fonts.values()]


def collect_checks(
    config: AppConfig,
    *,
    workflow: str | None = None,
    complete: bool = False,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    system = platform.system()
    checks.append(
        _result(
            "operating_system",
            system in {"Darwin", "Windows"},
            f"supported operating system: {system} {platform.release()}",
            f"unsupported operating system: {system}",
        )
    )
    checks.append(
        _result(
            "python",
            sys.version_info >= (3, 11),
            f"Python {platform.python_version()}",
            f"Python 3.11+ required; found {platform.python_version()}",
        )
    )

    ffmpeg = str(config.video_diary.get("ffmpeg_command", "ffmpeg"))
    ffprobe = str(config.video_diary.get("ffprobe_command", "ffprobe"))
    node = str(config.video_diary.get("node_command", "node"))
    for check_id, command, args in [
        ("ffmpeg", ffmpeg, ("-version",)),
        ("ffprobe", ffprobe, ("-version",)),
        ("node", node, ("--version",)),
    ]:
        version = first_version_line(command, *args)
        checks.append(
            _result(
                check_id,
                version is not None,
                version or "",
                f"required command not available: {command}",
            )
        )

    requirements = PROJECT_ROOT / "requirements.lock"
    checks.append(
        _result(
            "python_dependencies",
            requirements.is_file(),
            "locked dependency file is present",
            f"missing dependency lock: {requirements}",
        )
    )
    checks.append(
        _result(
            "pillow",
            importlib.util.find_spec("PIL") is not None,
            "Pillow runtime is available for factory title and subtitle metrics",
            "Pillow runtime is missing; run the platform installer/bootstrap",
        )
    )

    try:
        directories = create_runtime_dirs(config)
        for directory in directories:
            with tempfile.NamedTemporaryFile(dir=directory, delete=True):
                pass
        directory_detail = ", ".join(str(item) for item in directories)
        checks.append(
            CheckResult(
                "runtime_directories",
                CheckStatus.PASS,
                f"read/write checks passed: {directory_detail}",
            )
        )
    except OSError as exc:
        checks.append(
            CheckResult("runtime_directories", CheckStatus.FAIL, str(exc))
        )

    free_bytes = shutil.disk_usage(config.paths.data_root).free
    free_gib = free_bytes / (1024**3)
    disk_status = (
        CheckStatus.PASS
        if free_gib >= 10
        else CheckStatus.MANUAL_REVIEW_REQUIRED
        if free_gib >= 5
        else CheckStatus.FAIL
    )
    checks.append(
        CheckResult(
            "disk_space",
            disk_status,
            f"{free_gib:.1f} GiB free; 10 GiB recommended minimum",
        )
    )

    required_models = [str(item) for item in config.models.get("required", [])]
    missing_models = [
        model
        for model in required_models
        if not (config.paths.models_dir / model).exists()
    ]
    checks.append(
        _result(
            "models",
            not missing_models,
            (
                "video_diary requires no external model"
                if not required_models
                else f"required models present: {', '.join(required_models)}"
            ),
            f"missing required models: {', '.join(missing_models)}",
        )
    )

    fonts = _font_paths(config)
    missing_fonts = [str(path) for path in fonts if not path.is_file()]
    checks.append(
        _result(
            "fonts",
            not missing_fonts,
            f"configured fonts are readable ({len(fonts)})",
            f"missing configured fonts: {', '.join(missing_fonts)}",
        )
    )

    try:
        skills = discover_skills(PROJECT_ROOT)
        video_diary = skills["video_diary"]
        video_diary.load_entrypoint()
        preset_paths = [
            PROJECT_ROOT / str(path)
            for path in video_diary.manifest.get("presets", [])
        ]
        missing_presets = [str(path) for path in preset_paths if not path.is_file()]
        if missing_presets:
            raise FileNotFoundError(", ".join(missing_presets))
        checks.append(
            CheckResult(
                "video_diary_skill",
                CheckStatus.PASS,
                "skill manifest, entrypoint, and preset paths load successfully",
            )
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        checks.append(
            CheckResult("video_diary_skill", CheckStatus.FAIL, str(exc))
        )

    try:
        skills = discover_skills(PROJECT_ROOT)
        factory = skills["factory_shoot"]
        factory.load_entrypoint()
        preset_paths = [
            PROJECT_ROOT / str(path)
            for path in factory.manifest.get("presets", [])
        ]
        missing_presets = [str(path) for path in preset_paths if not path.is_file()]
        if missing_presets:
            raise FileNotFoundError(", ".join(missing_presets))
        checks.append(
            CheckResult(
                "factory_shoot_skill",
                CheckStatus.PASS,
                "factory supervised-Beta entrypoint and preset paths load successfully",
            )
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        checks.append(
            CheckResult("factory_shoot_skill", CheckStatus.FAIL, str(exc))
        )

    if workflow == "factory_shoot" and complete:
        try:
            application_path = find_jianying_application()
            if application_path is None:
                raise FileNotFoundError(
                    "Jianying Pro is required for the complete factory workflow"
                )
            application = inspect_jianying_application(application_path)
            if application["version"] != "7.9.0":
                raise ValueError(
                    "factory workflow is locked to Jianying 7.9.0; found "
                    + (application["version"] or "unknown")
                )
            checks.append(
                CheckResult(
                    "factory_complete_jianying",
                    CheckStatus.PASS,
                    (
                        f"{application['display_name']} {application['version']} "
                        f"({application['bundle_id']})"
                    ),
                )
            )
        except (FileNotFoundError, OSError, RuntimeError, TypeError, ValueError) as exc:
            checks.append(
                CheckResult("factory_complete_jianying", CheckStatus.FAIL, str(exc))
            )

    violations = find_boundary_violations(PROJECT_ROOT)
    checks.append(
        _result(
            "skill_boundaries",
            not violations,
            "no cross-skill imports detected",
            "; ".join(violations),
        )
    )
    checks.append(
        _result(
            "configuration",
            config.channel in {"stable", "beta"},
            (
                f"channel={config.channel}; local_config="
                f"{config.local_path or 'defaults/environment only'}"
            ),
            f"invalid channel: {config.channel}",
        )
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Check production readiness")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat manual-review results as a non-zero exit",
    )
    parser.add_argument(
        "--workflow",
        choices=("video_diary", "factory_shoot", "case_study"),
    )
    parser.add_argument(
        "--complete",
        action="store_true",
        help="require external applications needed for a complete workflow",
    )
    args = parser.parse_args()
    environment = dict(os.environ)
    if args.config:
        environment["AI_VIDEO_EDITOR_CONFIG"] = str(args.config)
    config = load_config(environment=environment)
    checks = collect_checks(
        config,
        workflow=args.workflow,
        complete=args.complete,
    )
    status = overall_status(checks)
    if args.as_json:
        print(
            json.dumps(
                {
                    "status": status,
                    "checks": [asdict(check) for check in checks],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for check in checks:
            print(f"{check.status}: {check.check_id} - {check.detail}")
        print(f"OVERALL: {status}")
    if status == CheckStatus.FAIL:
        return 1
    if args.strict and status == CheckStatus.MANUAL_REVIEW_REQUIRED:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
