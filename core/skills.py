from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str
    name: str
    status: str
    enabled: bool
    entrypoint: str | None
    path: Path
    manifest: dict[str, Any]

    def load_entrypoint(self) -> Callable[..., Any]:
        if not self.enabled or not self.entrypoint:
            raise RuntimeError(f"skill is not enabled: {self.skill_id}")
        module_name, separator, attribute = self.entrypoint.partition(":")
        if not separator:
            raise ValueError(f"invalid entrypoint: {self.entrypoint}")
        module = importlib.import_module(module_name)
        callback = getattr(module, attribute)
        if not callable(callback):
            raise TypeError(f"entrypoint is not callable: {self.entrypoint}")
        return callback


def discover_skills(project_root: Path) -> dict[str, SkillDefinition]:
    discovered: dict[str, SkillDefinition] = {}
    for manifest_path in sorted((project_root / "skills").glob("*/skill.json")):
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        skill_id = str(payload["id"])
        if skill_id in discovered:
            raise ValueError(f"duplicate skill id: {skill_id}")
        if manifest_path.parent.name != skill_id:
            raise ValueError(
                f"skill directory {manifest_path.parent.name} does not match id {skill_id}"
            )
        discovered[skill_id] = SkillDefinition(
            skill_id=skill_id,
            name=str(payload["name"]),
            status=str(payload["status"]),
            enabled=bool(payload["enabled"]),
            entrypoint=payload.get("entrypoint"),
            path=manifest_path.parent,
            manifest=payload,
        )
    return discovered


def find_boundary_violations(project_root: Path) -> list[str]:
    violations: list[str] = []
    skills_root = project_root / "skills"
    pattern = re.compile(r"(?:from|import)\s+skills\.([a-z_][a-z0-9_]*)")
    for source in skills_root.glob("*/*.py"):
        # External macOS volumes can materialize binary AppleDouble metadata as
        # `._name.py`. It is not Python source and must never enter source scans.
        if source.name.startswith("._"):
            continue
        owner = source.parent.name
        for line_number, line in enumerate(
            source.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            for match in pattern.finditer(line):
                target = match.group(1)
                if target != owner:
                    violations.append(
                        f"{source.relative_to(project_root)}:{line_number}: "
                        f"{owner} imports {target}"
                    )
    return violations
