"""Centralized file I/O (Markdown uses utf-8-sig on Windows)."""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

ENCODING = "utf-8-sig"

# Windows 可能未安装 tzdata；paths.json 常用时区用固定偏移回退
_TZ_FALLBACK: dict[str, timezone] = {
    "Asia/Shanghai": timezone(timedelta(hours=8)),
    "Asia/Chongqing": timezone(timedelta(hours=8)),
    "Asia/Hong_Kong": timezone(timedelta(hours=8)),
    "UTC": timezone.utc,
}


def get_timezone(name: str):
    try:
        return ZoneInfo(name)
    except Exception:
        if name in _TZ_FALLBACK:
            return _TZ_FALLBACK[name]
        raise ValueError(f"unsupported timezone: {name}")


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding=ENCODING)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=ENCODING)
    if not path.is_file():
        raise OSError(f"write failed: {path}")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if not dst.is_file():
        raise OSError(f"copy failed: {dst}")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise OSError(f"mkdir failed: {path}")


def now_str(tz_name: str) -> str:
    tz = get_timezone(tz_name)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M")


def today_date(tz_name: str) -> str:
    tz = get_timezone(tz_name)
    return datetime.now(tz).strftime("%Y-%m-%d")


def timestamp_for_filename(tz_name: str) -> str:
    tz = get_timezone(tz_name)
    return datetime.now(tz).strftime("%Y%m%d_%H%M%S")


def truncate(text: str, max_len: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def is_placeholder_line(line: str) -> bool:
    s = line.strip()
    return s in ("（暂无）", "(暂无)", "（无）", "(无)")
