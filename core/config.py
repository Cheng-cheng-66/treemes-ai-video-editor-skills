from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RuntimePaths:
    data_root: Path
    input_dir: Path
    output_dir: Path
    cache_dir: Path
    logs_dir: Path
    models_dir: Path


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    channel: str
    paths: RuntimePaths
    video_diary: dict[str, Any]
    models: dict[str, Any]
    raw: dict[str, Any]
    local_path: Path | None


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, Mapping)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON config {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"config must contain a JSON object: {path}")
    return value


def _resolve_under(base: Path, value: str) -> Path:
    candidate = Path(value).expanduser()
    return candidate.resolve() if candidate.is_absolute() else (base / candidate).resolve()


def load_config(
    *,
    project_root: Path | None = None,
    local_path: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> AppConfig:
    root = (project_root or PROJECT_ROOT).resolve()
    default_path = root / "configs" / "default.json"
    raw = _read_json(default_path)

    selected_local = local_path
    if selected_local is None:
        configured = (environment or os.environ).get("AI_VIDEO_EDITOR_CONFIG")
        selected_local = Path(configured) if configured else root / "configs" / "local.json"
    selected_local = selected_local.expanduser().resolve()
    if selected_local.exists():
        raw = _deep_merge(raw, _read_json(selected_local))
        active_local: Path | None = selected_local
    else:
        active_local = None

    env = dict(os.environ if environment is None else environment)
    channel = env.get("AI_VIDEO_EDITOR_CHANNEL", str(raw.get("channel", "stable")))
    if channel not in {"stable", "beta"}:
        raise ValueError(f"unsupported update channel: {channel}")

    path_config = raw.get("paths", {})
    data_value = env.get(
        "AI_VIDEO_EDITOR_DATA_ROOT",
        str(path_config.get("data_root", "var")),
    )
    data_root = _resolve_under(root, data_value)

    def runtime_path(env_key: str, config_key: str, default: str) -> Path:
        value = env.get(env_key, str(path_config.get(config_key, default)))
        return _resolve_under(data_root, value)

    paths = RuntimePaths(
        data_root=data_root,
        input_dir=runtime_path("AI_VIDEO_EDITOR_INPUT_DIR", "inputs", "inputs"),
        output_dir=runtime_path("AI_VIDEO_EDITOR_OUTPUT_DIR", "outputs", "outputs"),
        cache_dir=runtime_path("AI_VIDEO_EDITOR_CACHE_DIR", "cache", "cache"),
        logs_dir=runtime_path("AI_VIDEO_EDITOR_LOG_DIR", "logs", "logs"),
        models_dir=runtime_path("AI_VIDEO_EDITOR_MODEL_DIR", "models", "models"),
    )
    return AppConfig(
        project_root=root,
        channel=channel,
        paths=paths,
        video_diary=dict(raw.get("video_diary", {})),
        models=dict(raw.get("models", {})),
        raw=raw,
        local_path=active_local,
    )


def create_runtime_dirs(config: AppConfig) -> list[Path]:
    directories = [
        config.paths.data_root,
        config.paths.input_dir,
        config.paths.output_dir,
        config.paths.cache_dir,
        config.paths.logs_dir,
        config.paths.models_dir,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    return directories


def write_local_config_template(
    config: AppConfig,
    destination: Path | None = None,
) -> Path:
    target = destination or config.project_root / "configs" / "local.json"
    if target.exists():
        return target
    try:
        portable_data_root = str(config.paths.data_root.relative_to(config.project_root))
    except ValueError:
        portable_data_root = str(config.paths.data_root)

    payload = {
        "schema_version": 1,
        "channel": config.channel,
        "paths": {
            # Keep an in-project runtime directory relative so a validated staged
            # installation can be moved into its final Codex Skill directory.
            "data_root": portable_data_root,
        },
        "video_diary": {
            "font_profile": "auto",
        },
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target
