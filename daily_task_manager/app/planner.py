"""Generate TODAY.md daily plan."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import Paths
from app.storage import read_text, today_date, write_text, now_str
from app.task_query import (
    TaskBlock,
    TasksDocument,
    format_section_display,
    iter_task_blocks,
    parse_backlog_section,
    parse_tasks_md,
)
from app.taie_reader import format_taie_list_lines, read_red_flags

LOW_ENERGY_KW = (
    "累",
    "压力",
    "崩",
    "睡眠差",
    "低能量",
    "疲劳",
    "焦虑",
)


@dataclass
class TodayPlanResult:
    ok: bool
    file_path: str
    next_step: str
    energy_mode: str
    taie_synced: int = 0
    taie_removed: int = 0
    message: str = ""


def _build_taie_task_block(item: dict[str, str], recorded_at: str) -> list[str]:
    lines = [
        f"- [ ] {item['title_short']}",
        "  - 来源：TAIE.xmind",
        f"  - TAIE路径：{item.get('path_short') or '—'}",
        "  - 类型：任务",
        "  - 状态：pending",
        f"  - 记录时间：{recorded_at}",
    ]
    return lines


def _append_to_section(lines: list[str], block: list[str]) -> list[str]:
    cleaned = [ln for ln in lines if not ln.strip().startswith("（暂无）")]
    if cleaned and cleaned[-1].strip():
        cleaned.append("")
    cleaned.extend(block)
    return cleaned


def _block_from_taie(block: TaskBlock) -> bool:
    return any("来源：TAIE.xmind" in line for line in block.lines)


def sync_taie_red_flags_to_active(
    paths: Paths, doc: TasksDocument
) -> tuple[TasksDocument, int, int, str, list[dict[str, str]]]:
    """
    Refresh TAIE red flags in TASKS.md Today / Active.
    Non-TAIE tasks are kept; all TAIE-sourced tasks are replaced from current xmind.
    Returns (doc, added_count, removed_count, error, items).
    """
    status, items, err = read_red_flags(paths.taie_file, limit=None)
    if status != "ok":
        return doc, 0, 0, err, []

    active = doc.sections.get("Today / Active", [])
    taie_blocks = [b for b in iter_task_blocks(active) if _block_from_taie(b)]
    non_taie_blocks = [b for b in iter_task_blocks(active) if not _block_from_taie(b)]
    removed = len(taie_blocks)

    active = []
    for block in non_taie_blocks:
        active = _append_to_section(active, block.lines)

    recorded = now_str(paths.timezone)
    added = 0
    for item in items:
        short = item.get("title_short", "").strip()
        if not short or short == "（无标题）":
            continue
        active = _append_to_section(active, _build_taie_task_block(item, recorded))
        added += 1

    doc.sections["Today / Active"] = active
    return doc, added, removed, "", items


def _detect_low_energy(energy_content: str) -> bool:
    return any(kw in energy_content for kw in LOW_ENERGY_KW)


def _pick_next_step(
    doc: TasksDocument,
    taie_lines: list[str],
    low_energy: bool,
    backlog_body: list[str],
) -> str:
    for section in ("Today / Active", "Overdue"):
        blocks = iter_task_blocks(doc.sections.get(section, []))
        for block in blocks:
            if not block.checked:
                return f"先处理 {section}：{block.title}"

    if taie_lines:
        first = taie_lines[0]
        m = re.match(r"^\d+\.\s+(.+)$", first)
        title = m.group(1) if m else first
        return f"从 TAIE 红旗中选 1 项主线：{title}"

    blocks = iter_task_blocks(doc.sections.get("Next Round", []))
    if blocks and not low_energy:
        return f"状态允许时处理 Next Round：{blocks[0].title}"

    blocks = iter_task_blocks(doc.sections.get("Waiting", []))
    if blocks:
        return f"跟进 Waiting：{blocks[0].title}"

    backlog_blocks = iter_task_blocks(backlog_body)
    if backlog_blocks:
        return f"可选处理 Backlog：{backlog_blocks[0].title}"

    return "今天没有紧急项，休息或只做一件小事即可。"


def _pending_count(lines: list[str]) -> int:
    return len([b for b in iter_task_blocks(lines) if not b.checked])


def _scheduled_pending_count(doc: TasksDocument) -> int:
    total = 0
    for lines in doc.scheduled.values():
        total += _pending_count(lines)
    return total


def _other_pool_hints(
    doc: TasksDocument,
    backlog_body: list[str],
) -> list[str]:
    hints: list[str] = []
    tomorrow_n = _pending_count(doc.sections.get("Tomorrow", []))
    if tomorrow_n:
        hints.append(
            f"- Tomorrow 有 {tomorrow_n} 项（今天计划不展开；问「明天有什么任务」可查看）"
        )
    scheduled_n = _scheduled_pending_count(doc)
    if scheduled_n:
        hints.append(
            f"- Scheduled 有 {scheduled_n} 项（今天计划不展开；问「未来排期任务」可查看）"
        )
    backlog_n = _pending_count(backlog_body)
    if backlog_n:
        hints.append(
            f"- Backlog 有 {backlog_n} 个未排期事项（今天不必全部处理；问「堆积任务」可查看）"
        )
    return hints


def _status_label(low_energy: bool, active_count: int, overdue_count: int) -> str:
    if low_energy:
        return "低能量，宜减量"
    if overdue_count > 0:
        return "有逾期，先清一项"
    if active_count > 3:
        return "任务偏多，只抓重点"
    return "正常"


def generate_today(paths: Paths) -> TodayPlanResult:
    tasks_content = read_text(paths.tasks_file)
    doc = parse_tasks_md(tasks_content)

    doc, taie_synced, taie_removed, taie_sync_err, taie_items = sync_taie_red_flags_to_active(
        paths, doc
    )
    if not taie_sync_err:
        write_text(paths.tasks_file, doc.render())

    energy_content = read_text(paths.energy_log_file)
    backlog_body = parse_backlog_section(read_text(paths.backlog_file))

    low_energy = _detect_low_energy(energy_content)
    energy_mode = "低能量" if low_energy else "正常"

    if taie_sync_err:
        taie_state = f"读取失败 ({taie_sync_err})"
        taie_display = ["（暂无或读取失败）"]
        taie_lines: list[str] = []
    elif taie_items:
        taie_state = (
            f"已读取 {len(taie_items)} 条红旗（全部列出），"
            f"新增 {taie_synced} 条，移除 {taie_removed} 条（Today / Active）"
        )
        taie_display = format_taie_list_lines(taie_items)
        taie_lines = taie_display
    else:
        taie_state = "无红旗任务"
        taie_display = ["（暂无）"]
        taie_lines = []

    today = today_date(paths.timezone)
    now = now_str(paths.timezone)

    active_blocks = iter_task_blocks(doc.sections.get("Today / Active", []))
    overdue_blocks = iter_task_blocks(doc.sections.get("Overdue", []))

    next_step = _pick_next_step(
        doc,
        taie_lines,
        low_energy,
        backlog_body,
    )

    def sec(name: str, max_n: int | None = None) -> str:
        return format_section_display(doc.sections.get(name, []), max_tasks=max_n)

    hints = _other_pool_hints(doc, backlog_body)

    lines: list[str] = [
        f"# 今日计划 — {today}",
        "",
        "## 当前判断",
        f"- 当前时间：{now}",
        f"- 当前状态：{_status_label(low_energy, len(active_blocks), len(overdue_blocks))}",
        f"- 能量模式：{energy_mode}",
        f"- TAIE 状态：{taie_state}",
        "",
        "## 今日任务池",
        "",
        "### Today / Active",
        sec("Today / Active"),
        "",
        "### Overdue",
        sec("Overdue", max_n=3),
        "",
        "## TAIE 红旗任务（全部，已简化标题）",
        *taie_display,
        "",
        "## 容量判断",
        "- 今天先不要把所有任务都排满。",
        "- 优先处理 Today / Active、Overdue、以及 TAIE 红旗里最重要的 1 项。",
        "- Tomorrow / Scheduled / Backlog 今天不展开具体条目。",
    ]

    if low_energy:
        lines.append("- 【低能量模式】今日只突出 1-3 个重点，其余顺延。")

    if hints:
        lines.extend(["", "## 其他池提示", *hints])

    lines.extend(
        [
            "",
            "## 执行顺序建议",
            "1. 先处理 Today / Active 中必须做的生活事项。",
            "2. 再从 TAIE 红旗中选 1 个主线任务。",
        ]
    )
    if low_energy:
        lines.append("3. 【低能量】只保留 1 个主目标，其余全部延后。")
    else:
        lines.extend(
            [
                "3. 状态一般时，只保留 1 个主目标 + 1 个支援任务。",
                "4. 状态较好时，再处理 Next Round 中的一项。",
            ]
        )

    lines.extend(
        [
            "",
            "## 下一步",
            next_step,
            "",
        ]
    )

    content = "\n".join(lines)
    write_text(paths.today_file, content)

    return TodayPlanResult(
        ok=True,
        file_path=str(paths.today_file),
        next_step=next_step,
        energy_mode=energy_mode,
        taie_synced=taie_synced,
        taie_removed=taie_removed,
    )
