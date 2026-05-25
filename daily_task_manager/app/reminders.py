"""Timed reminders storage and operations."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.config import Paths
from app.storage import ensure_dir, get_timezone, now_str, read_text, write_text


def _load_store(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"reminders": []}
    return json.loads(read_text(path) or '{"reminders": []}')


def _save_store(path: Path, data: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    if not path.is_file():
        raise OSError(f"write failed: {path}")


def _new_id() -> str:
    return f"rem_{uuid.uuid4().hex[:12]}"


def _cron_name(reminder_id: str) -> str:
    return f"dtm_{reminder_id}"


@dataclass
class ReminderRecord:
    id: str
    text: str
    original_text: str
    trigger_at: str
    timezone: str
    type: str
    status: str
    created_at: str
    source: str
    cron_required: bool
    cron_created: bool
    cron_name: str
    assumed_date: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "text": self.text,
            "original_text": self.original_text,
            "trigger_at": self.trigger_at,
            "timezone": self.timezone,
            "type": self.type,
            "status": self.status,
            "created_at": self.created_at,
            "source": self.source,
            "cron_required": self.cron_required,
            "cron_created": self.cron_created,
            "cron_name": self.cron_name,
        }
        if self.assumed_date:
            d["assumed_date"] = self.assumed_date
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReminderRecord":
        return cls(
            id=str(d["id"]),
            text=str(d["text"]),
            original_text=str(d["original_text"]),
            trigger_at=str(d["trigger_at"]),
            timezone=str(d["timezone"]),
            type=str(d.get("type", "one_time")),
            status=str(d.get("status", "pending")),
            created_at=str(d["created_at"]),
            source=str(d.get("source", "OpenClaw/Python capture")),
            cron_required=bool(d.get("cron_required", True)),
            cron_created=bool(d.get("cron_created", False)),
            cron_name=str(d.get("cron_name", "")),
            assumed_date=d.get("assumed_date"),
        )


def create_timed_reminder(
    paths: Paths,
    original_text: str,
    reminder_text: str,
    trigger_at: datetime,
    assumed_date: Optional[str] = None,
) -> ReminderRecord:
    rid = _new_id()
    created = now_str(paths.timezone)
    trigger_str = trigger_at.strftime("%Y-%m-%d %H:%M:%S")
    record = ReminderRecord(
        id=rid,
        text=reminder_text or original_text,
        original_text=original_text,
        trigger_at=trigger_str,
        timezone=paths.timezone,
        type="one_time",
        status="pending",
        created_at=created,
        source="OpenClaw/Python capture",
        cron_required=True,
        cron_created=False,
        cron_name=_cron_name(rid),
        assumed_date=assumed_date,
    )
    store = _load_store(paths.timed_reminders_file)
    store.setdefault("reminders", []).append(record.to_dict())
    _save_store(paths.timed_reminders_file, store)
    return record


def list_reminders(paths: Paths, status: Optional[str] = None) -> list[ReminderRecord]:
    store = _load_store(paths.timed_reminders_file)
    items = [ReminderRecord.from_dict(x) for x in store.get("reminders", [])]
    if status:
        items = [x for x in items if x.status == status]
    return sorted(items, key=lambda x: x.trigger_at)


def get_reminder(paths: Paths, reminder_id: str) -> Optional[ReminderRecord]:
    for item in list_reminders(paths):
        if item.id == reminder_id:
            return item
    return None


def _update_reminder(paths: Paths, reminder_id: str, **fields: Any) -> Optional[ReminderRecord]:
    store = _load_store(paths.timed_reminders_file)
    updated: Optional[ReminderRecord] = None
    for i, raw in enumerate(store.get("reminders", [])):
        if raw.get("id") == reminder_id:
            raw.update(fields)
            store["reminders"][i] = raw
            updated = ReminderRecord.from_dict(raw)
            break
    if updated:
        _save_store(paths.timed_reminders_file, store)
    return updated


def cancel_reminder(paths: Paths, reminder_id: str) -> tuple[bool, str, Optional[ReminderRecord]]:
    item = get_reminder(paths, reminder_id)
    if not item:
        return False, "reminder not found", None
    if item.status == "cancelled":
        return True, "already cancelled", item
    updated = _update_reminder(paths, reminder_id, status="cancelled")
    return True, "cancelled", updated


def _append_log(paths: Paths, line: str) -> None:
    ensure_dir(paths.log_dir)
    log_path = paths.log_dir / "reminders.log"
    with log_path.open("a", encoding="utf-8-sig") as f:
        f.write(line + "\n")


def build_cron_command(paths: Paths, reminder_id: str) -> str:
    run_cmd = paths.root / "scripts" / "run.cmd"
    return f'"{run_cmd}" fire-reminder --id {reminder_id}'


def trigger_at_to_cron_at(trigger_at: str, timezone: str) -> str:
    naive = datetime.strptime(trigger_at, "%Y-%m-%d %H:%M:%S")
    aware = naive.replace(tzinfo=get_timezone(timezone))
    return aware.isoformat()


def build_deliver_line(task_text: str, *, notify: bool = True) -> str:
    if not notify:
        return "NO_REPLY"
    t = " ".join(task_text.split())
    if len(t) > 60:
        t = t[:57] + "…"
    return f"提醒到点：{t}。已记录触发。"


def build_cron_message(paths: Paths, reminder_id: str) -> str:
    cmd = build_cron_command(paths, reminder_id)
    return (
        "【DTM定时提醒·极简】只允许 exec 工具。执行下面这一条命令（禁止加 --json，禁止 today，禁止读文件）：\n"
        f"{cmd}\n"
        "读取 stdout 中以 deliver: 开头的行。"
        "若值为 NO_REPLY，最终回复必须是 NO_REPLY。"
        "否则去掉 deliver: 前缀，把剩余文字作为唯一回复，禁止其他内容。"
    )


def build_cron_spec(
    paths: Paths,
    reminder_id: str,
    cron_name: str,
    trigger_at: str,
    timezone: str,
) -> dict[str, Any]:
    return {
        "name": cron_name,
        "sessionTarget": "isolated",
        "wakeMode": "now",
        "deleteAfterRun": True,
        "schedule": {
            "kind": "at",
            "at": trigger_at_to_cron_at(trigger_at, timezone),
        },
        "payload": {
            "kind": "agentTurn",
            "message": build_cron_message(paths, reminder_id),
            "lightContext": True,
            "toolsAllow": ["exec"],
            "timeoutSeconds": 90,
        },
        "failureAlert": False,
        "delivery": {
            "mode": "announce",
            "_note": "创建 cron 时填入当前会话的 channel / to / accountId",
        },
    }


def build_cron_prompt(
    paths: Paths,
    reminder_id: str,
    cron_name: str,
    trigger_at: str,
    timezone: str,
) -> str:
    cron_at = trigger_at_to_cron_at(trigger_at, timezone)
    return (
        "创建 OpenClaw 一次性 cron。必须：session=isolated、lightContext=true、"
        "toolsAllow=[exec]、failureAlert=false、deleteAfterRun=true。\n"
        f"name={cron_name}\n"
        f"at={cron_at}\n"
        f"fire_command={build_cron_command(paths, reminder_id)}\n"
        "到点 cron message 用 capture JSON 的 cron_message 原样填入。"
        "delivery 指向当前用户会话。禁止在 fire_command 后加 --json。"
    )


@dataclass
class FireReminderResult:
    ok: bool
    fired: bool
    reminder_id: str
    text: str
    deliver_line: str
    status: str
    next_action: str
    message: str = ""


def _short_fire_text(task_text: str) -> str:
    t = " ".join(task_text.split())
    if len(t) <= 40:
        return f"现在该处理：{t}"
    return "现在该处理任务了。"


def fire_reminder(paths: Paths, reminder_id: str) -> FireReminderResult:
    next_action = f'可手动运行 "{paths.root / "scripts" / "run.cmd"}" today 查看当前计划。'
    item = get_reminder(paths, reminder_id)
    if not item:
        return FireReminderResult(
            ok=False,
            fired=False,
            reminder_id=reminder_id,
            text="",
            deliver_line="",
            status="missing",
            next_action=next_action,
            message="reminder not found",
        )
    if item.status != "pending":
        deliver = build_deliver_line(item.text, notify=False)
        return FireReminderResult(
            ok=True,
            fired=False,
            reminder_id=reminder_id,
            text=_short_fire_text(item.text),
            deliver_line=deliver,
            status=item.status,
            next_action="",
            message=f"reminder already {item.status}",
        )

    fired_at = now_str(paths.timezone)
    _update_reminder(
        paths,
        reminder_id,
        status="fired",
        fired_at=fired_at,
    )
    _append_log(paths, f"{fired_at} | fired | {reminder_id} | {item.text}")

    deliver = build_deliver_line(item.text, notify=True)
    return FireReminderResult(
        ok=True,
        fired=True,
        reminder_id=reminder_id,
        text=_short_fire_text(item.text),
        deliver_line=deliver,
        status="fired",
        next_action=next_action,
        message="",
    )
