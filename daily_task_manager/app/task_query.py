"""Parse and query TASKS.md / BACKLOG.md structures."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from app.storage import is_placeholder_line

TASK_SECTIONS = [
    "Today / Active",
    "Tomorrow",
    "Scheduled",
    "Next Round",
    "Waiting",
    "Deferred",
    "Overdue",
]

SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
SCHEDULED_DATE_RE = re.compile(r"^###\s+(\d{4}-\d{2}-\d{2})\s*$")
TASK_LINE_RE = re.compile(r"^-\s+\[([ xX])\]\s+(.+)$")
META_LINE_RE = re.compile(r"^(\s+)-\s+(.+)$")


@dataclass
class TaskBlock:
    lines: list[str]
    checked: bool = False
    title: str = ""

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def main_line(self) -> str:
        return self.lines[0] if self.lines else ""


@dataclass
class TasksDocument:
    preamble: list[str] = field(default_factory=list)
    sections: dict[str, list[str]] = field(default_factory=dict)
    scheduled: dict[str, list[str]] = field(default_factory=dict)
    tail: list[str] = field(default_factory=list)

    def render(self) -> str:
        out: list[str] = []
        out.extend(self.preamble)
        if out and out[-1].strip():
            out.append("")

        for name in TASK_SECTIONS:
            if name not in self.sections and name != "Scheduled":
                continue
            out.append(f"## {name}")
            if name == "Scheduled":
                body = [ln for ln in self.sections.get("Scheduled", []) if ln.strip()]
                if body:
                    out.extend(body)
                else:
                    out.append("指定日期任务。只有到当天才进入 Today / Active。")
                for date_key in sorted(self.scheduled.keys()):
                    out.append("")
                    out.append(f"### {date_key}")
                    out.extend(self.scheduled[date_key])
            else:
                body = [ln for ln in self.sections.get(name, []) if ln.strip()]
                if body:
                    out.extend(body)
                else:
                    out.append("（暂无）")
            out.append("")

        out.extend(self._tail_lines())
        text = "\n".join(out)
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        return text.rstrip() + "\n"

    def _tail_lines(self) -> list[str]:
        if not self.tail:
            return ["## Backlog Link", "无日期待办请放到 BACKLOG.md。"]
        return self.tail


def parse_tasks_md(content: str) -> TasksDocument:
    doc = TasksDocument()
    lines = content.splitlines()
    i = 0
    current_section: Optional[str] = None
    current_date: Optional[str] = None
    buffer: list[str] = []

    def flush_section() -> None:
        nonlocal buffer, current_section, current_date
        if current_section is None:
            if buffer:
                doc.preamble.extend(buffer)
            buffer = []
            return
        if current_section == "Scheduled":
            if current_date:
                doc.scheduled[current_date] = buffer[:]
            else:
                doc.sections.setdefault("Scheduled", []).extend(buffer)
        else:
            doc.sections[current_section] = buffer[:]
        buffer = []

    while i < len(lines):
        line = lines[i]
        m_sec = SECTION_RE.match(line)
        if m_sec:
            flush_section()
            name = m_sec.group(1).strip()
            if name in TASK_SECTIONS:
                current_section = name
                current_date = None
            elif name == "Backlog Link":
                flush_section()
                current_section = None
                doc.tail = lines[i:]
                break
            else:
                current_section = None
            i += 1
            continue

        m_date = SCHEDULED_DATE_RE.match(line)
        if m_date and current_section == "Scheduled":
            flush_section()
            current_date = m_date.group(1)
            buffer = []
            i += 1
            continue

        if current_section is None and not doc.tail:
            doc.preamble.append(line)
        else:
            buffer.append(line)
        i += 1

    flush_section()
    return doc


def section_items(lines: list[str]) -> list[str]:
    """Non-empty, non-placeholder task-related lines for display."""
    items: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        if is_placeholder_line(line):
            continue
        if line.strip().startswith("指定日期任务"):
            continue
        items.append(line)
    return items


def iter_task_blocks(lines: list[str]) -> list[TaskBlock]:
    blocks: list[TaskBlock] = []
    current: Optional[TaskBlock] = None
    for line in lines:
        m = TASK_LINE_RE.match(line)
        if m:
            if current:
                blocks.append(current)
            current = TaskBlock(
                lines=[line],
                checked=m.group(1).lower() == "x",
                title=m.group(2).strip(),
            )
        elif current and META_LINE_RE.match(line):
            current.lines.append(line)
        elif current and line.strip() == "":
            current.lines.append(line)
        elif current and line.startswith("  "):
            current.lines.append(line)
    if current:
        blocks.append(current)
    return blocks


def find_first_pending_task(
    lines: list[str], keyword: str
) -> tuple[Optional[TaskBlock], list[str]]:
    """Return (block, remaining_lines) after removing first matching pending task."""
    keyword_lower = keyword.lower()
    blocks = iter_task_blocks(lines)
    if not blocks:
        return None, lines

    new_lines: list[str] = []
    removed: Optional[TaskBlock] = None
    idx = 0
    pos = 0
    while pos < len(lines):
        if idx < len(blocks) and pos == _line_index(lines, blocks, idx):
            block = blocks[idx]
            if (
                removed is None
                and not block.checked
                and keyword_lower in block.title.lower()
            ):
                removed = block
                pos += len(block.lines)
                idx += 1
                continue
        new_lines.append(lines[pos])
        if idx < len(blocks) and pos == _line_index(lines, blocks, idx) + len(blocks[idx].lines) - 1:
            idx += 1
        pos += 1

    if removed is None:
        return None, lines
    return removed, _strip_trailing_blanks(new_lines)


def _line_index(lines: list[str], blocks: list[TaskBlock], block_idx: int) -> int:
    target = blocks[block_idx].lines[0]
    for i, line in enumerate(lines):
        if line == target:
            return i
    return 0


def _strip_trailing_blanks(lines: list[str]) -> list[str]:
    out = lines[:]
    while out and not out[-1].strip():
        out.pop()
    return out


def remove_block_from_lines(lines: list[str], block: TaskBlock) -> list[str]:
    start = -1
    for i, line in enumerate(lines):
        if line == block.lines[0]:
            start = i
            break
    if start < 0:
        return lines
    end = start + len(block.lines)
    new_lines = lines[:start] + lines[end:]
    return _strip_trailing_blanks(new_lines)


def find_task_in_document(
    doc: TasksDocument, keyword: str
) -> tuple[Optional[str], Optional[str], Optional[TaskBlock], TasksDocument]:
    keyword_lower = keyword.lower()
    search_order = [
        ("Today / Active", "section"),
        ("Overdue", "section"),
        ("Tomorrow", "section"),
        ("Next Round", "section"),
        ("Waiting", "section"),
        ("Deferred", "section"),
        ("Scheduled", "scheduled"),
    ]
    for name, kind in search_order:
        if kind == "section":
            lines = doc.sections.get(name, [])
            for block in iter_task_blocks(lines):
                if not block.checked and keyword_lower in block.title.lower():
                    doc.sections[name] = remove_block_from_lines(lines, block)
                    return name, None, block, doc
        else:
            for date_key, lines in list(doc.scheduled.items()):
                for block in iter_task_blocks(lines):
                    if not block.checked and keyword_lower in block.title.lower():
                        doc.scheduled[date_key] = remove_block_from_lines(lines, block)
                        if not doc.scheduled[date_key]:
                            del doc.scheduled[date_key]
                        return "Scheduled", date_key, block, doc
    return None, None, None, doc


def format_section_display(lines: list[str], max_tasks: Optional[int] = None) -> str:
    blocks = iter_task_blocks(lines)
    if not blocks:
        items = section_items(lines)
        return "\n".join(items) if items else "（暂无）"
    shown = blocks[:max_tasks] if max_tasks else blocks
    return "\n".join(b.text for b in shown)


def parse_backlog_section(content: str) -> list[str]:
    lines = content.splitlines()
    in_todo = False
    body: list[str] = []
    for line in lines:
        if re.match(r"^##\s+待办事项\s*$", line):
            in_todo = True
            continue
        if in_todo and line.startswith("## "):
            break
        if in_todo:
            body.append(line)
    return body
