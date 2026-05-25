"""CLI entry point for daily task manager."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from app.archive import mark_done
from app.config import check_entries, load_paths
from app.list_tasks import format_list_tasks_text, list_tasks, result_to_payload
from app.planner import generate_today
from app.rollover import rollover
from app.storage import copy_file, ensure_dir, read_text, timestamp_for_filename
from app.reminders import cancel_reminder, fire_reminder, list_reminders
from app.task_capture import capture_task
from app.taie_reader import read_red_flags


def _print_text(lines: list[str]) -> None:
    for line in lines:
        try:
            print(line)
        except UnicodeEncodeError:
            # Windows 控制台可能非 UTF-8（标题含 emoji 时）
            enc = getattr(sys.stdout, "encoding", None) or "utf-8"
            safe = line.encode(enc, errors="replace").decode(enc, errors="replace")
            print(safe)


def _emit(payload: dict, as_json: bool, text_lines: list[str]) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_text(text_lines)


def cmd_check(paths, as_json: bool) -> int:
    entries = check_entries(paths)
    missing = [e for e in entries if not e["exists"]]
    if missing:
        payload = {"check_result": "failed", "missing": missing}
        text = ["check_result: failed"] + [f"missing: {m['key']} -> {m['path']}" for m in missing]
        _emit(payload, as_json, text)
        return 2
    payload = {"check_result": "ok", "entries": entries}
    _emit(payload, as_json, ["check_result: ok"])
    return 0


def cmd_paths(paths, as_json: bool) -> int:
    data = paths.as_dict()
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for key, value in data.items():
            print(f"{key}: {value}")
    return 0


def cmd_taie_red(paths, as_json: bool) -> int:
    status, items, err = read_red_flags(paths.taie_file, limit=None)
    if status != "ok":
        payload = {"taie_read_result": "failed", "error": err}
        _emit(payload, as_json, ["taie_read_result: failed", f"reason: {err}"])
        return 2

    payload = {"taie_read_result": "ok", "count": len(items), "items": items}
    text = ["taie_read_result: ok", f"count: {len(items)}"]
    for i, item in enumerate(items, start=1):
        path_part = f" [{item['path_short']}]" if item.get("path_short") else ""
        text.append(f"{i}. {item['title_short']}{path_part}")
    _emit(payload, as_json, text)
    return 0


def cmd_capture(paths, text: str, as_json: bool) -> int:
    result = capture_task(paths, text)
    payload = result.to_payload()
    if not result.ok:
        _emit(payload, as_json, [f"capture_result: failed", f"message: {result.message}"])
        return 2

    lines = [f"capture_result: ok", f"mode: {result.mode}", f"cron_required: {result.cron_required}"]
    if result.mode == "task_pool":
        lines.extend(
            [
                f"destination: {result.destination}",
                f"file: {result.file_path}",
                f"text: {result.text}",
            ]
        )
    elif result.mode == "timed_reminder":
        lines.extend(
            [
                f"reminder_id: {result.reminder_id}",
                f"trigger_at: {result.trigger_at}",
                f"timezone: {result.timezone}",
                f"cron_name: {result.cron_name}",
                f"cron_command: {result.cron_command}",
                f"text: {result.text}",
            ]
        )
        if result.assumed_date:
            lines.append(f"assumed_date: {result.assumed_date}")
        if result.message:
            lines.append(f"note: {result.message}")
    _emit(payload, as_json, lines)
    return 0


def cmd_list_reminders(paths, as_json: bool) -> int:
    items = list_reminders(paths)
    payload = {
        "list_reminders_result": "ok",
        "count": len(items),
        "reminders": [x.to_dict() for x in items],
    }
    lines = ["list_reminders_result: ok", f"count: {len(items)}"]
    for x in items:
        lines.append(f"- {x.id} | {x.status} | {x.trigger_at} | {x.text}")
    _emit(payload, as_json, lines)
    return 0


def cmd_fire_reminder(paths, reminder_id: str, as_json: bool) -> int:
    result = fire_reminder(paths, reminder_id)
    if not result.ok:
        payload = {
            "reminder_result": "failed",
            "message": result.message,
        }
        _emit(payload, as_json, ["reminder_result: failed", f"message: {result.message}"])
        return 2

    payload = {
        "reminder_result": "ok",
        "fired": result.fired,
        "status": result.status,
        "text": result.text,
        "deliver_line": result.deliver_line,
        "next_action": result.next_action,
    }
    if result.message:
        payload["message"] = result.message

    if as_json:
        _emit(payload, as_json, [])
    else:
        # Cron path: one line only — agent reads deliver: and replies or NO_REPLY.
        _print_text([f"deliver: {result.deliver_line}"])
    return 0


def cmd_cancel_reminder(paths, reminder_id: str, as_json: bool) -> int:
    ok, message, item = cancel_reminder(paths, reminder_id)
    if not ok:
        payload = {"cancel_reminder_result": "failed", "message": message}
        _emit(payload, as_json, [f"cancel_reminder_result: failed", f"message: {message}"])
        return 2
    payload = {
        "cancel_reminder_result": "ok",
        "reminder_id": reminder_id,
        "status": item.status if item else "cancelled",
        "message": message,
    }
    _emit(
        payload,
        as_json,
        [f"cancel_reminder_result: ok", f"reminder_id: {reminder_id}", f"message: {message}"],
    )
    return 0


def cmd_list_tasks(paths, scope: str, as_json: bool) -> int:
    result = list_tasks(paths, scope)
    payload = result_to_payload(result)
    if not result.ok:
        _emit(payload, as_json, format_list_tasks_text(result))
        return 2
    _emit(payload, as_json, format_list_tasks_text(result))
    return 0


def cmd_today(paths, as_json: bool) -> int:
    result = generate_today(paths)
    if not result.ok:
        payload = {"today_result": "failed", "message": result.message}
        _emit(payload, as_json, ["today_result: failed", f"message: {result.message}"])
        return 2

    payload = {
        "today_result": "ok",
        "file": result.file_path,
        "energy_mode": result.energy_mode,
        "next_step": result.next_step,
        "taie_synced": result.taie_synced,
        "taie_removed": result.taie_removed,
    }
    lines = [
        "today_result: ok",
        f"file: {result.file_path}",
        f"energy_mode: {result.energy_mode}",
        f"taie_synced: {result.taie_synced}",
        f"taie_removed: {result.taie_removed}",
        f"next_step: {result.next_step}",
    ]
    _emit(payload, as_json, lines)
    return 0


def cmd_done(paths, text: str, as_json: bool) -> int:
    result = mark_done(paths, text)
    if not result.ok:
        payload = {"done_result": "failed", "message": result.message}
        _emit(payload, as_json, ["done_result: failed", f"message: {result.message}"])
        return 2

    payload = {
        "done_result": "ok",
        "found": result.found,
        "task": result.task_title,
        "source_section": result.source_section,
        "archive_file": result.archive_file,
        "message": result.message,
    }
    lines = [
        "done_result: ok",
        f"found: {'yes' if result.found else 'no'}",
        f"task: {result.task_title}",
        f"source_section: {result.source_section}",
        f"archive_file: {result.archive_file}",
    ]
    if result.message:
        lines.append(f"message: {result.message}")
    _emit(payload, as_json, lines)
    return 0


def cmd_rollover(paths, as_json: bool) -> int:
    result = rollover(paths)
    payload = {
        "rollover_result": "ok",
        "moved_tomorrow": result.moved_tomorrow,
        "moved_scheduled_today": result.moved_scheduled_today,
        "moved_overdue": result.moved_overdue,
    }
    lines = [
        "rollover_result: ok",
        f"moved_tomorrow: {result.moved_tomorrow}",
        f"moved_scheduled_today: {result.moved_scheduled_today}",
        f"moved_overdue: {result.moved_overdue}",
    ]
    _emit(payload, as_json, lines)
    return 0


def cmd_backup(paths, as_json: bool) -> int:
    ensure_dir(paths.backup_dir)
    ts = timestamp_for_filename(paths.timezone)
    copied: list[dict[str, str]] = []
    for src in (paths.tasks_file, paths.today_file, paths.backlog_file):
        if not src.is_file():
            continue
        dst = paths.backup_dir / f"{src.stem}_{ts}{src.suffix}"
        copy_file(src, dst)
        copied.append({"source": str(src), "backup": str(dst)})

    if not copied:
        payload = {"backup_result": "failed", "message": "no files to backup"}
        _emit(payload, as_json, ["backup_result: failed", "message: no files to backup"])
        return 2

    payload = {"backup_result": "ok", "files": copied}
    lines = ["backup_result: ok"] + [f"backup: {c['backup']}" for c in copied]
    _emit(payload, as_json, lines)
    return 0


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Output JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily task manager for OpenClaw")
    parser.add_argument("--config", required=True, help="Path to config/paths.json")

    sub = parser.add_subparsers(dest="command", required=True)

    for name in (
        "check",
        "paths",
        "taie-red",
        "today",
        "rollover",
        "backup",
        "list-reminders",
    ):
        _add_json_flag(sub.add_parser(name))

    p_capture = sub.add_parser("capture", help="Capture a task or reminder")
    p_capture.add_argument("--text", required=True, help="Task text")
    _add_json_flag(p_capture)

    p_done = sub.add_parser("done", help="Mark task done and archive")
    p_done.add_argument("--text", required=True, help="Keyword to match task")
    _add_json_flag(p_done)

    p_fire = sub.add_parser("fire-reminder", help="Fire a timed reminder")
    p_fire.add_argument("--id", required=True, dest="reminder_id", help="Reminder id")
    _add_json_flag(p_fire)

    p_cancel = sub.add_parser("cancel-reminder", help="Cancel a timed reminder")
    p_cancel.add_argument("--id", required=True, dest="reminder_id", help="Reminder id")
    _add_json_flag(p_cancel)

    p_list_tasks = sub.add_parser("list-tasks", help="List tasks by scope")
    p_list_tasks.add_argument(
        "--scope",
        required=True,
        choices=sorted(
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
        ),
        help="Task scope to list",
    )
    _add_json_flag(p_list_tasks)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    as_json = getattr(args, "json", False)
    config_path = Path(args.config)
    if not config_path.is_file():
        msg = f"config not found: {config_path}"
        if as_json:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(msg)
        return 2

    try:
        paths = load_paths(config_path)
    except (KeyError, json.JSONDecodeError, OSError) as exc:
        msg = f"config load failed: {exc}"
        if as_json:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(msg)
        return 2

    handlers = {
        "check": lambda: cmd_check(paths, as_json),
        "paths": lambda: cmd_paths(paths, as_json),
        "taie-red": lambda: cmd_taie_red(paths, as_json),
        "capture": lambda: cmd_capture(paths, args.text, as_json),
        "today": lambda: cmd_today(paths, as_json),
        "done": lambda: cmd_done(paths, args.text, as_json),
        "rollover": lambda: cmd_rollover(paths, as_json),
        "backup": lambda: cmd_backup(paths, as_json),
        "list-reminders": lambda: cmd_list_reminders(paths, as_json),
        "fire-reminder": lambda: cmd_fire_reminder(paths, args.reminder_id, as_json),
        "cancel-reminder": lambda: cmd_cancel_reminder(paths, args.reminder_id, as_json),
        "list-tasks": lambda: cmd_list_tasks(paths, args.scope, as_json),
    }

    try:
        return handlers[args.command]()
    except ValueError as exc:
        msg = f"error: {exc}"
        if as_json:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(msg)
        return 2
    except OSError as exc:
        msg = f"error: {exc}"
        if as_json:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(msg)
        return 2


if __name__ == "__main__":
    sys.exit(main())
