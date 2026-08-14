from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import AppConfig
from skills.factory_shoot.completion import (
    find_jianying_application,
    inspect_jianying_application,
    launch_jianying,
)
from skills.factory_shoot.runner import FactoryRenderRequest, run


def prepare_complete(
    request: FactoryRenderRequest,
    config: AppConfig | None = None,
    *,
    launch_application: bool = True,
) -> dict[str, Any]:
    app = find_jianying_application()
    if app is None:
        raise FileNotFoundError(
            "剪映专业版未安装；完整工厂工作流已停止。"
            "如仅需技术预览，必须由用户明确授权 preview 模式。"
        )
    application = inspect_jianying_application(app)
    if application["version"] != "7.9.0":
        raise ValueError(
            "完整工厂工作流锁定剪映7.9.0；当前版本为"
            + (application["version"] or "未知")
        )
    rendered = run(request, config)
    session: Path | None = None
    if launch_application:
        session = launch_jianying(request.output_dir)
    return {
        "status": "BLOCKED_PENDING_JIANYING_UI_AND_HUMAN_REVIEW",
        "deliverable_video": None,
        "technical_preview_is_not_deliverable": True,
        "completion_request": rendered["completion_request"],
        "jianying_session": session,
        "jianying_application": application,
        "rendered_assets": rendered,
        "next_action": (
            "Use Codex Desktop computer control to complete every UI event in "
            "completion_request.json, then run the finalize command."
        ),
    }
