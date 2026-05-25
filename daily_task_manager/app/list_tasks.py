"""List tasks by scope from TASKS.md and BACKLOG.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import Paths
from app.storage import read_text
from app.task_query import (
    TASK_SECTIONS,
    TaskBlock,
    iter_task_blocks,
    parse_backlog_section,
    parse_tasks_md,
)

VALID_SCOPES = frozenset(
    {
        "unfinished",
        "active",
        "today",
        "tomorrow",
        "next",
        "backlog",
        "overdue",
        "waiting",
        "scheduled",
        "all",
    }
)

SCOPE_SECTIONS: dict[str, list[str]] = {
    "today": ["Today / Active", "Overdue"],
    "active": ["Today / Active", "Overdue", "Next Round"],
    "tomorrow": ["Tomorrow"],
    "next": ["Next Round"],
    "overdue": ["Overdue"],
    "waiting": ["Waiting"],
    "scheduled": ["Scheduled"],
    "unfinished": [
        "Today / Active",
        "Overdue",
        "Next Round",
        "Tomorrow",
        "Waiting",
        "Deferred",
        "Scheduled",
    ],
    "backlog": ["Backlog"],
    "all": [
        "Today / Active",
        "Overdue",
        "Next Round",
        "Tomorrow",
        "Waiting",
        "Deferred",
        "Scheduled",
        "Backlog",
    ],
}

SCOPE_DISPLAY_ORDER: dict[str, list[str]] = {
    "unfinished": [
        "Today / Active",
        "Overdue",
        "Next Round",
        "Tomorrow",
        "Waiting",
        "Deferred",
        "Scheduled",
    ],
    "all": [
        "Today / Active",
        "Overdue",
        "Next Round",
        "Tomorrow",
        "Waiting",
        "Deferred",
        "Scheduled",
        "Backlog",
    ],
}


@dataclass
class ListTasksResult:
    ok: bool
    scope: str
    total: int = 0
    sections: dict[str, Any] = field(default_factory=dict)
    message: str = ""


def _pending_titles(blocks: list[TaskBlock]) -> list[str]:
    return [b.title for b in blocks if not b.checked]


def _pending_from_lines(lines: list[str]) -> list[str]:
    return _pending_titles(iter_task_blocks(lines))


def _build_sections_data(
    doc,
    backlog_body: list[str],
    section_names: list[str],
) -> dict[str, Any]:
    sections: dict[str, Any] = {}
    for name in section_names:
        if name == "Scheduled":
            scheduled: dict[str, list[str]] = {}
            for date_key in sorted(doc.scheduled.keys()):
                titles = _pending_from_lines(doc.scheduled[date_key])
                if titles:
                    scheduled[date_key] = titles
            if scheduled:
                sections["Scheduled"] = scheduled
        elif name == "Backlog":
            titles = _pending_from_lines(backlog_body)
            if titles:
                sections["Backlog"] = titles
        else:
            titles = _pending_from_lines(doc.sections.get(name, []))
            if titles:
                sections[name] = titles
    return sections


def _count_sections(sections: dict[str, Any]) -> int:
    total = 0
    for key, value in sections.items():
        if key == "Scheduled" and isinstance(value, dict):
            for titles in value.values():
                total += len(titles)
        elif isinstance(value, list):
            total += len(value)
    return total


def _format_numbered(titles: list[str]) -> list[str]:
    return [f"{i}. {title}" for i, title in enumerate(titles, start=1)]


def _display_order(scope: str, sections: dict[str, Any]) -> list[str]:
    if scope in SCOPE_DISPLAY_ORDER:
        return [name for name in SCOPE_DISPLAY_ORDER[scope] if name in sections]
    order = [s for s in TASK_SECTIONS if s in sections]
    if "Backlog" in sections:
        order.append("Backlog")
    return order


def format_list_tasks_text(result: ListTasksResult) -> list[str]:
    lines = [
        "list_tasks_result: ok" if result.ok else "list_tasks_result: failed",
        f"scope: {result.scope}",
    ]
    if not result.ok:
        if result.message:
            lines.append(f"message: {result.message}")
        return lines

    lines.append(f"total: {result.total}")
    lines.append("")

    for name in _display_order(result.scope, result.sections):
        value = result.sections[name]
        lines.append(f"## {name}")
        if name == "Scheduled" and isinstance(value, dict):
            for date_key in sorted(value.keys()):
                lines.append(f"### {date_key}")
                lines.extend(_format_numbered(value[date_key]))
                lines.append("")
            if lines and lines[-1] == "":
                lines.pop()
        else:
            lines.extend(_format_numbered(value))
        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()
    return lines


def list_tasks(paths: Paths, scope: str) -> ListTasksResult:
    scope = scope.strip().lower()
    if scope not in VALID_SCOPES:
        return ListTasksResult(
            ok=False,
            scope=scope,
            message=f"invalid scope: {scope}; valid: {', '.join(sorted(VALID_SCOPES))}",
        )

    doc = parse_tasks_md(read_text(paths.tasks_file))
    backlog_body = parse_backlog_section(read_text(paths.backlog_file))
    section_names = SCOPE_SECTIONS[scope]
    sections = _build_sections_data(doc, backlog_body, section_names)
    total = _count_sections(sections)

    return ListTasksResult(ok=True, scope=scope, total=total, sections=sections)


def result_to_payload(result: ListTasksResult) -> dict[str, Any]:
    if not result.ok:
        return {
            "list_tasks_result": "failed",
            "scope": result.scope,
            "message": result.message,
        }

    payload_sections: dict[str, Any] = {}
    for name in SCOPE_SECTIONS.get(result.scope, []):
        if name == "Scheduled":
            scheduled = result.sections.get("Scheduled", {})
            if scheduled:
                payload_sections["Scheduled"] = scheduled
        elif name == "Backlog":
            backlog = result.sections.get("Backlog", [])
            if backlog:
                payload_sections["Backlog"] = backlog
        else:
            items = result.sections.get(name, [])
            if items:
                payload_sections[name] = items

    return {
        "list_tasks_result": "ok",
        "scope": result.scope,
        "total": result.total,
        "sections": payload_sections,
    }
