from __future__ import annotations

from typing import Any


STORY_KEYWORDS = {
    "customer_identity": ("客户", "公司", "实业", "开关", "工厂"),
    "industry_and_factory_context": ("行业", "车间", "产线", "工厂", "设备"),
    "problem_or_management_need": (
        "以前",
        "问题",
        "漏单",
        "异常",
        "浪费",
        "看不到",
        "不透明",
    ),
    "implementation_or_usage_evidence": (
        "上线",
        "MES",
        "三色灯",
        "看板",
        "联网",
        "系统",
    ),
    "role_specific_workflow": (
        "员工",
        "操作员",
        "主管",
        "经理",
        "老板",
        "PMC",
        "报工",
        "派工",
    ),
    "outcome_or_management_value": (
        "现在",
        "改善",
        "提高",
        "降低",
        "透明",
        "价值",
        "效果",
    ),
    "complete_closing": ("谢谢", "总结", "完整案例", "最后", "评价"),
}


def analyze_story_units(segments: list[dict[str, Any]]) -> dict[str, Any]:
    timeline_end = max((segment["to_ms"] for segment in segments), default=0)
    closing_window_start = timeline_end * 0.75
    units: dict[str, dict[str, Any]] = {}
    for unit, keywords in STORY_KEYWORDS.items():
        evidence = []
        for index, segment in enumerate(segments):
            if unit == "complete_closing" and segment["from_ms"] < closing_window_start:
                continue
            matched = [keyword for keyword in keywords if keyword in segment["text"]]
            if matched:
                evidence.append(
                    {
                        "segment_index": index,
                        "from_ms": segment["from_ms"],
                        "to_ms": segment["to_ms"],
                        "text": segment["text"],
                        "matched_keywords": matched,
                    }
                )
        units[unit] = {
            "status": "present" if evidence else "missing",
            "evidence": evidence,
            "human_verified": False,
        }
    missing = [key for key, value in units.items() if not value["evidence"]]
    return {
        "schema_version": 1,
        "status": "complete_candidate" if not missing else "incomplete",
        "units": units,
        "missing_units": missing,
        "machine_analysis_only": True,
        "human_story_review_pass": None,
    }
