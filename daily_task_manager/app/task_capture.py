"""Capture tasks from natural-language text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from app.config import Paths
from app.reminders import (
    build_cron_command,
    build_cron_message,
    build_cron_prompt,
    build_cron_spec,
    create_timed_reminder,
    trigger_at_to_cron_at,
)
from app.storage import now_str, read_text, write_text
from app.task_query import TasksDocument, parse_tasks_md
from app.time_parser import has_explicit_clock, is_recurring_request, parse_reminder_time

TODAY_KW = ("今天", "今晚")
TOMORROW_KW = ("明天",)
NEXT_ROUND_KW = ("下午", "等会", "等会儿", "一会", "一会儿", "稍后", "下次", "下一轮")
WAITING_KW = ("等待", "等回复", "等消息")
DATE_ISO_RE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
DATE_CN_RE = re.compile(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日")
REMIND_KW = ("提醒", "记得", "别忘", "要做", "处理", "报修", "联系", "买", "取", "还", "交", "办")


@dataclass
class CaptureResult:
    ok: bool
    mode: str = "task_pool"
    destination: str = ""
    file_path: str = ""
    text: str = ""
    message: str = ""
    cron_required: bool = False
    recurring_required: bool = False
    reminder_id: str = ""
    trigger_at: str = ""
    timezone: str = ""
    cron_name: str = ""
    cron_command: str = ""
    cron_prompt: str = ""
    cron_message: str = ""
    cron_at: str = ""
    cron_spec: dict[str, Any] = field(default_factory=dict)
    assumed_date: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "capture_result": "ok" if self.ok else "failed",
            "mode": self.mode,
            "cron_required": self.cron_required,
            "recurring_required": self.recurring_required,
        }
        if self.message:
            payload["message"] = self.message
        if self.mode == "task_pool" and self.ok:
            payload["destination"] = self.destination
            payload["file"] = self.file_path
            payload["text"] = self.text
        if self.mode == "timed_reminder" and self.ok:
            payload["reminder_id"] = self.reminder_id
            payload["trigger_at"] = self.trigger_at
            payload["timezone"] = self.timezone
            payload["text"] = self.text
            payload["cron_name"] = self.cron_name
            payload["cron_command"] = self.cron_command
            payload["cron_prompt"] = self.cron_prompt
            payload["cron_message"] = self.cron_message
            payload["cron_at"] = self.cron_at
            payload["cron_spec"] = self.cron_spec
            payload["cron_created"] = False
            if self.assumed_date:
                payload["assumed_date"] = self.assumed_date
        if self.recurring_required:
            payload["text"] = self.text
        payload.update(self.extra)
        return payload


def _normalize_date(year: int, month: int, day: int) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}"


def _extract_scheduled_date(text: str, default_year: int) -> Optional[str]:
    m = DATE_ISO_RE.search(text)
    if m:
        return _normalize_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = DATE_CN_RE.search(text)
    if m:
        return _normalize_date(default_year, int(m.group(1)), int(m.group(2)))
    return None


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(k in text for k in keywords)


def _is_vague_daypart_only(text: str) -> bool:
    """下午提醒我 / 等会提醒我 — no explicit clock."""
    if has_explicit_clock(text):
        return False
    vague = ("下午", "上午", "晚上", "今晚", "等会", "等会儿", "一会", "一会儿", "稍后", "下次", "下一轮")
    return any(v in text for v in vague) and ("提醒" in text or "记得" in text)


def classify_capture(text: str, year: int) -> tuple[str, str]:
    if _contains_any(text, TODAY_KW):
        return "tasks", "Today / Active"
    if _contains_any(text, TOMORROW_KW):
        return "tasks", "Tomorrow"
    if _contains_any(text, WAITING_KW):
        return "tasks", "Waiting"
    if _is_vague_daypart_only(text) or _contains_any(text, NEXT_ROUND_KW):
        return "tasks", "Next Round"
    scheduled = _extract_scheduled_date(text, year)
    if scheduled and not has_explicit_clock(text):
        return "tasks_scheduled", scheduled
    if _contains_any(text, REMIND_KW) or "任务" in text:
        return "backlog", "待办事项"
    return "backlog", "待办事项"


def _build_task_block(text: str, recorded_at: str) -> list[str]:
    return [
        f"- [ ] {text}",
        "  - 来源：OpenClaw/Python capture",
        "  - 类型：任务",
        "  - 状态：pending",
        f"  - 记录时间：{recorded_at}",
    ]


def _append_to_section(lines: list[str], block: list[str]) -> list[str]:
    cleaned = [ln for ln in lines if not ln.strip().startswith("（暂无）")]
    if cleaned and cleaned[-1].strip():
        cleaned.append("")
    cleaned.extend(block)
    return cleaned


def _append_backlog(content: str, block: list[str]) -> str:
    lines = content.splitlines()
    out: list[str] = []
    inserted = False
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if re.match(r"^##\s+待办事项\s*$", line):
            i += 1
            section_body: list[str] = []
            while i < len(lines) and not lines[i].startswith("## "):
                if not lines[i].strip().startswith("（暂无）"):
                    section_body.append(lines[i])
                i += 1
            section_body = [ln for ln in section_body if ln.strip() or section_body]
            if section_body and section_body[-1].strip():
                section_body.append("")
            section_body.extend(block)
            out.extend(section_body)
            inserted = True
            continue
        i += 1
    if not inserted:
        if out and out[-1].strip():
            out.append("")
        out.extend(["## 待办事项", ""] + block)
    return "\n".join(out).rstrip() + "\n"


def _capture_task_pool(paths: Paths, text: str, recorded: str) -> CaptureResult:
    year = int(recorded[:4])
    kind, target = classify_capture(text, year)
    block = _build_task_block(text, recorded)

    if kind == "backlog":
        content = read_text(paths.backlog_file)
        write_text(paths.backlog_file, _append_backlog(content, block))
        return CaptureResult(
            ok=True,
            mode="task_pool",
            destination="BACKLOG.md -> 待办事项",
            file_path=str(paths.backlog_file),
            text=text,
            cron_required=False,
        )

    doc = parse_tasks_md(read_text(paths.tasks_file))
    if kind == "tasks_scheduled":
        date_key = target
        existing = doc.scheduled.get(date_key, [])
        doc.scheduled[date_key] = _append_to_section(existing, block)
        dest = f"TASKS.md -> Scheduled ({date_key})"
    else:
        existing = doc.sections.get(target, [])
        doc.sections[target] = _append_to_section(existing, block)
        dest = f"TASKS.md -> {target}"

    write_text(paths.tasks_file, doc.render())
    return CaptureResult(
        ok=True,
        mode="task_pool",
        destination=dest,
        file_path=str(paths.tasks_file),
        text=text,
        cron_required=False,
    )


def capture_task(paths: Paths, text: str) -> CaptureResult:
    text = text.strip()
    if not text:
        return CaptureResult(ok=False, mode="task_pool", message="empty text")

    recorded = now_str(paths.timezone)

    if is_recurring_request(text):
        parsed = parse_reminder_time(text, paths.timezone)
        return CaptureResult(
            ok=False,
            mode="recurring_confirm",
            recurring_required=True,
            cron_required=False,
            text=parsed.reminder_text or text,
            message="检测到重复提醒（如每天/每周），需用户确认后再创建，未写入任务池",
        )

    if has_explicit_clock(text):
        parsed = parse_reminder_time(text, paths.timezone)
        if parsed.recurring_required:
            return CaptureResult(
                ok=False,
                mode="recurring_confirm",
                recurring_required=True,
                cron_required=False,
                text=parsed.reminder_text or text,
                message=parsed.message,
            )
        if not parsed.ok or not parsed.trigger_at:
            return CaptureResult(
                ok=False,
                mode="timed_reminder",
                cron_required=False,
                text=text,
                message=parsed.message or "时间解析失败",
            )
        record = create_timed_reminder(
            paths,
            original_text=text,
            reminder_text=parsed.reminder_text,
            trigger_at=parsed.trigger_at,
            assumed_date=parsed.assumed_date,
        )
        cmd = build_cron_command(paths, record.id)
        prompt = build_cron_prompt(
            paths, record.id, record.cron_name, record.trigger_at, record.timezone
        )
        message = build_cron_message(paths, record.id)
        spec = build_cron_spec(
            paths, record.id, record.cron_name, record.trigger_at, record.timezone
        )
        return CaptureResult(
            ok=True,
            mode="timed_reminder",
            text=record.text,
            cron_required=True,
            reminder_id=record.id,
            trigger_at=record.trigger_at,
            timezone=record.timezone,
            cron_name=record.cron_name,
            cron_command=cmd,
            cron_prompt=prompt,
            cron_message=message,
            cron_at=trigger_at_to_cron_at(record.trigger_at, record.timezone),
            cron_spec=spec,
            assumed_date=record.assumed_date or "",
            message="已写入 timed reminders；需 OpenClaw 创建一次性 cron（Python 未创建 cron）",
        )

    return _capture_task_pool(paths, text, recorded)
