"""Load paths from config/paths.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Paths:
    timezone: str
    root: Path
    life_dir: Path
    taie_file: Path
    archive_dir: Path
    daily_done_dir: Path
    log_dir: Path
    backup_dir: Path
    timed_reminders_file: Path
    tasks_file: Path
    today_file: Path
    backlog_file: Path
    inbox_file: Path
    energy_log_file: Path
    shopping_file: Path
    relationships_file: Path
    weekly_reviews_file: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "timezone": self.timezone,
            "root": str(self.root),
            "life_dir": str(self.life_dir),
            "taie_file": str(self.taie_file),
            "archive_dir": str(self.archive_dir),
            "daily_done_dir": str(self.daily_done_dir),
            "log_dir": str(self.log_dir),
            "backup_dir": str(self.backup_dir),
            "timed_reminders_file": str(self.timed_reminders_file),
            "tasks_file": str(self.tasks_file),
            "today_file": str(self.today_file),
            "backlog_file": str(self.backlog_file),
            "inbox_file": str(self.inbox_file),
            "energy_log_file": str(self.energy_log_file),
            "shopping_file": str(self.shopping_file),
            "relationships_file": str(self.relationships_file),
            "weekly_reviews_file": str(self.weekly_reviews_file),
        }


def _path(value: str) -> Path:
    return Path(value)


def load_paths(config_path: Path) -> Paths:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return Paths(
        timezone=str(raw["timezone"]),
        root=_path(raw["root"]),
        life_dir=_path(raw["life_dir"]),
        taie_file=_path(raw["taie_file"]),
        archive_dir=_path(raw["archive_dir"]),
        daily_done_dir=_path(raw["daily_done_dir"]),
        log_dir=_path(raw["log_dir"]),
        backup_dir=_path(raw["backup_dir"]),
        timed_reminders_file=_path(raw["timed_reminders_file"]),
        tasks_file=_path(raw["tasks_file"]),
        today_file=_path(raw["today_file"]),
        backlog_file=_path(raw["backlog_file"]),
        inbox_file=_path(raw["inbox_file"]),
        energy_log_file=_path(raw["energy_log_file"]),
        shopping_file=_path(raw["shopping_file"]),
        relationships_file=_path(raw["relationships_file"]),
        weekly_reviews_file=_path(raw["weekly_reviews_file"]),
    )


def check_entries(paths: Paths) -> list[dict[str, Any]]:
    """Return list of {key, path, kind, exists} for health check."""
    entries: list[tuple[str, Path, str]] = [
        ("root", paths.root, "dir"),
        ("life_dir", paths.life_dir, "dir"),
        ("taie_file", paths.taie_file, "file"),
        ("archive_dir", paths.archive_dir, "dir"),
        ("daily_done_dir", paths.daily_done_dir, "dir"),
        ("log_dir", paths.log_dir, "dir"),
        ("backup_dir", paths.backup_dir, "dir"),
        ("timed_reminders_file", paths.timed_reminders_file, "file"),
        ("tasks_file", paths.tasks_file, "file"),
        ("today_file", paths.today_file, "file"),
        ("backlog_file", paths.backlog_file, "file"),
        ("inbox_file", paths.inbox_file, "file"),
        ("energy_log_file", paths.energy_log_file, "file"),
        ("shopping_file", paths.shopping_file, "file"),
        ("relationships_file", paths.relationships_file, "file"),
        ("weekly_reviews_file", paths.weekly_reviews_file, "file"),
    ]
    result: list[dict[str, Any]] = []
    for key, path, kind in entries:
        if kind == "dir":
            exists = path.is_dir()
        else:
            exists = path.is_file()
        result.append({"key": key, "path": str(path), "kind": kind, "exists": exists})
    return result
