"""Daily rollover: move Tomorrow/Scheduled into appropriate sections."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Paths
from app.storage import read_text, today_date, write_text
from app.task_query import TasksDocument, iter_task_blocks, parse_tasks_md


@dataclass
class RolloverResult:
    ok: bool
    moved_tomorrow: int
    moved_scheduled_today: int
    moved_overdue: int
    message: str = ""


def _merge_lines(existing: list[str], incoming: list[str]) -> list[str]:
    if not incoming:
        return existing
    out = [ln for ln in existing if ln.strip() != "（暂无）"]
    if out and out[-1].strip():
        out.append("")
    out.extend(incoming)
    return out


def rollover(paths: Paths) -> RolloverResult:
    doc = parse_tasks_md(read_text(paths.tasks_file))
    today = today_date(paths.timezone)

    tomorrow_lines = doc.sections.get("Tomorrow", [])
    tomorrow_blocks = iter_task_blocks(tomorrow_lines)
    moved_tomorrow = len(tomorrow_blocks)

    active = doc.sections.get("Today / Active", [])
    active = _merge_lines(active, tomorrow_lines)
    doc.sections["Today / Active"] = active
    doc.sections["Tomorrow"] = []

    moved_scheduled_today = 0
    moved_overdue = 0
    overdue = doc.sections.get("Overdue", [])

    for date_key in sorted(list(doc.scheduled.keys())):
        if date_key == today:
            lines = doc.scheduled.pop(date_key, [])
            blocks = iter_task_blocks(lines)
            moved_scheduled_today += len(blocks)
            doc.sections["Today / Active"] = _merge_lines(
                doc.sections.get("Today / Active", []), lines
            )
        elif date_key < today:
            lines = doc.scheduled.pop(date_key, [])
            blocks = iter_task_blocks(lines)
            moved_overdue += len(blocks)
            overdue = _merge_lines(overdue, lines)

    doc.sections["Overdue"] = overdue

    write_text(paths.tasks_file, doc.render())

    return RolloverResult(
        ok=True,
        moved_tomorrow=moved_tomorrow,
        moved_scheduled_today=moved_scheduled_today,
        moved_overdue=moved_overdue,
    )
