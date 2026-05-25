"""Read red-flag tasks from TAIE.xmind via zipfile + content.json."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from app.storage import truncate

_TITLE_PREFIXES = (
    "Current task：",
    "Current task:",
    "Current task（",
    "Current task(",
)


def simplify_taie_title(raw: str, max_len: int = 80) -> str:
    """First meaningful line (skip empty Current task: lines), truncate."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        for prefix in _TITLE_PREFIXES:
            if s.startswith(prefix):
                s = s[len(prefix) :].strip()
                break
        if s:
            return truncate(" ".join(s.split()), max_len)
    collapsed = " ".join(text.split())
    for prefix in _TITLE_PREFIXES:
        if collapsed.startswith(prefix):
            collapsed = collapsed[len(prefix) :].strip()
            break
    return truncate(collapsed, max_len) if collapsed else "（无标题）"


def simplify_taie_path(path: str, max_len: int = 50) -> str:
    parts = [p.strip() for p in path.split(" > ") if p.strip()]
    short_parts: list[str] = []
    for part in parts:
        sp = simplify_taie_title(part, max_len=36)
        if sp and sp != "（无标题）" and sp not in short_parts:
            short_parts.append(sp)
    if not short_parts:
        return ""
    branch = " > ".join(short_parts[-2:] if len(short_parts) > 2 else short_parts)
    return truncate(branch, max_len)


def enrich_taie_item(item: dict[str, str]) -> dict[str, str]:
    title = item.get("title", "")
    path = item.get("path", "")
    return {
        "title": title,
        "path": path,
        "title_short": simplify_taie_title(title),
        "path_short": simplify_taie_path(path),
    }


def format_taie_list_lines(items: list[dict[str, str]]) -> list[str]:
    lines: list[str] = []
    for i, item in enumerate(items, start=1):
        path_part = f" [{item['path_short']}]" if item.get("path_short") else ""
        lines.append(f"{i}. {item['title_short']}{path_part}")
    return lines


def _has_red_flag(node: dict[str, Any]) -> bool:
    markers = node.get("markers") or []
    for marker in markers:
        if isinstance(marker, dict) and marker.get("markerId") == "flag-red":
            return True
    return False


def _collect_red_nodes(
    node: dict[str, Any], path_titles: list[str], out: list[dict[str, str]]
) -> None:
    title = str(node.get("title", "")).strip()
    current_path = path_titles + ([title] if title else [])

    if _has_red_flag(node) and title:
        out.append({"title": title, "path": " > ".join(current_path)})

    children = node.get("children") or {}
    if not isinstance(children, dict):
        return

    attached = children.get("attached") or []
    if isinstance(attached, list):
        for child in attached:
            if isinstance(child, dict):
                _collect_red_nodes(child, current_path, out)

    for key, value in children.items():
        if key == "attached":
            continue
        if isinstance(value, list):
            for child in value:
                if isinstance(child, dict):
                    _collect_red_nodes(child, current_path, out)


def _walk_topic_tree(root: dict[str, Any], out: list[dict[str, str]]) -> None:
    _collect_red_nodes(root, [], out)


def read_red_flags(
    xmind_path: Path, limit: int | None = None
) -> tuple[str, list[dict[str, str]], str]:
    """
    Returns (status, items, error_message). Each item has title, path, title_short, path_short.
    limit=None returns all red flags.
    """
    if not xmind_path.is_file():
        return "failed", [], f"file not found: {xmind_path}"

    try:
        with zipfile.ZipFile(xmind_path, "r") as zf:
            names = zf.namelist()
            content_name = None
            for name in names:
                if name.endswith("content.json"):
                    content_name = name
                    break
            if not content_name:
                return "failed", [], "content.json not found in xmind archive"

            raw = zf.read(content_name).decode("utf-8")
            data = json.loads(raw)
    except zipfile.BadZipFile:
        return "failed", [], "invalid xmind zip file"
    except json.JSONDecodeError as exc:
        return "failed", [], f"content.json parse error: {exc}"
    except OSError as exc:
        return "failed", [], str(exc)

    found: list[dict[str, str]] = []
    sheets = data if isinstance(data, list) else [data]
    for sheet in sheets:
        if not isinstance(sheet, dict):
            continue
        root_topic = sheet.get("rootTopic")
        if isinstance(root_topic, dict):
            _walk_topic_tree(root_topic, found)
        topic = sheet.get("topic")
        if isinstance(topic, dict):
            _walk_topic_tree(topic, found)

    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for item in found:
        key = f"{item['title']}|{item['path']}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(enrich_taie_item(item))

    if limit is None:
        return "ok", unique, ""
    return "ok", unique[:limit], ""


def summarize_for_today(
    xmind_path: Path, limit: int | None = None, max_chars: int = 80
) -> tuple[str, list[str], str]:
    """Returns (status, summary_lines, error). Lists all red flags by default."""
    status, items, err = read_red_flags(xmind_path, limit=limit)
    if status != "ok":
        return status, [], err
    return "ok", format_taie_list_lines(items), ""
