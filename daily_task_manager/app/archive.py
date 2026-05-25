"""Mark tasks done and archive to daily_done."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import Paths
from app.storage import now_str, read_text, today_date, write_text
from app.task_query import TaskBlock, find_task_in_document, parse_tasks_md


@dataclass
class DoneResult:
    ok: bool
    found: bool
    task_title: str
    source_section: str
    archive_file: str
    message: str = ""


def _parse_source_from_block(block: TaskBlock) -> str:
    for line in block.lines:
        m = re.match(r"^\s+-\s+来源：(.+)$", line)
        if m:
            return m.group(1).strip()
    return "未知"


def _append_archive(path, date_str: str, entry_lines: list[str]) -> None:
    header = f"# {date_str} 每日完成归档"
    if path.is_file():
        content = read_text(path)
        if header not in content:
            content = content.rstrip() + "\n\n" + header + "\n\n## 已完成任务\n"
    else:
        content = header + "\n\n## 已完成任务\n"

    if not content.endswith("\n"):
        content += "\n"
    content += "\n".join(entry_lines) + "\n"
    write_text(path, content)


def mark_done(paths: Paths, keyword: str) -> DoneResult:
    keyword = keyword.strip()
    if not keyword:
        return DoneResult(
            ok=False,
            found=False,
            task_title="",
            source_section="",
            archive_file="",
            message="empty keyword",
        )

    doc = parse_tasks_md(read_text(paths.tasks_file))
    section, date_key, block, doc = find_task_in_document(doc, keyword)

    date_str = today_date(paths.timezone)
    finished_at = now_str(paths.timezone)
    archive_path = paths.daily_done_dir / f"{date_str}.md"

    if block is None:
        entry = [
            f"- [x] 临时完成记录：{keyword}",
            "  - 来源：未在 TASKS.md 匹配",
            "  - 完成证据：done 命令",
            f"  - 完成时间：{finished_at}",
            "  - 备注：关键词未找到对应任务，仍记录以免丢失",
        ]
        _append_archive(archive_path, date_str, entry)
        return DoneResult(
            ok=True,
            found=False,
            task_title=keyword,
            source_section="临时完成记录",
            archive_file=str(archive_path),
            message="task not found in TASKS.md; recorded as temporary completion",
        )

    write_text(paths.tasks_file, doc.render())

    source = _parse_source_from_block(block)
    loc = section or ""
    if date_key:
        loc = f"{section} ({date_key})"

    entry = [
        f"- [x] {block.title}",
        f"  - 来源：{source}（原位置：{loc}）",
        "  - 完成证据：done 命令",
        f"  - 完成时间：{finished_at}",
        "  - 备注：",
    ]
    _append_archive(archive_path, date_str, entry)

    return DoneResult(
        ok=True,
        found=True,
        task_title=block.title,
        source_section=loc,
        archive_file=str(archive_path),
    )
