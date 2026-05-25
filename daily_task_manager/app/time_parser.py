"""Parse explicit clock times from natural-language Chinese reminder text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from app.storage import get_timezone

RECURRING_RE = re.compile(r"每[天日周月]|每日|每天|每逢")
ISO_DATETIME_RE = re.compile(
    r"(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2}))?"
)
CN_DATE_RE = re.compile(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日")
CLOCK_COLON_RE = re.compile(r"(\d{1,2}):(\d{2})")
CLOCK_CN_RE = re.compile(
    r"(?:(今天|今晚|明天|明早|后天|大后天)\s*)?"
    r"(?:(上午|早上|早晨|中午|下午|晚上|晚间|夜里|凌晨)\s*)?"
    r"(\d{1,2})\s*(?:点|时)\s*(半)?"
)
# date prefix before clock: 6月11日下午3点
CN_DATE_CLOCK_RE = re.compile(
    r"(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*"
    r"(?:(上午|早上|早晨|中午|下午|晚上|晚间|夜里|凌晨)\s*)?"
    r"(\d{1,2})\s*(?:点|时)\s*(半)?"
)

DAY_PART_ONLY = ("下午", "等会", "等会儿", "一会", "一会儿", "稍后", "下次", "下一轮", "上午", "晚上", "今晚")


@dataclass
class TimeParseResult:
    ok: bool
    trigger_at: Optional[datetime] = None
    recurring_required: bool = False
    message: str = ""
    assumed_date: Optional[str] = None
    reminder_text: str = ""


def has_explicit_clock(text: str) -> bool:
    if ISO_DATETIME_RE.search(text) and ISO_DATETIME_RE.search(text).group(4):
        return True
    if re.search(r"\d{1,2}:\d{2}", text):
        return True
    if CN_DATE_CLOCK_RE.search(text):
        return True
    if CLOCK_CN_RE.search(text):
        return True
    return False


def is_recurring_request(text: str) -> bool:
    return bool(RECURRING_RE.search(text)) and has_explicit_clock(text)


def _apply_daypart(hour: int, minute: int, daypart: Optional[str]) -> tuple[int, int]:
    if not daypart:
        if hour <= 12 and "下午" not in (daypart or "") and hour < 12:
            pass
        return hour, minute
    if daypart in ("上午", "早上", "早晨", "凌晨"):
        if hour == 12:
            hour = 0
        return hour, minute
    if daypart == "中午":
        return 12, minute
    if daypart in ("下午", "晚上", "晚间", "夜里"):
        if hour < 12:
            hour += 12
        return hour, minute
    return hour, minute


def _clean_reminder_text(text: str) -> str:
    s = text.strip()
    s = CN_DATE_CLOCK_RE.sub("", s)
    s = ISO_DATETIME_RE.sub("", s)
    s = CLOCK_CN_RE.sub("", s)
    s = CLOCK_COLON_RE.sub("", s)
    for pat in (
        r"今天|今晚|明天|明早|后天|大后天",
        r"请?提醒(?:我)?",
        r"记得(?:提醒)?我?",
        r"别忘(?:了)?提醒?",
        r"设置定时提醒",
        r"创建\s*cron",
    ):
        s = re.sub(pat, "", s)
    s = re.sub(r"\s+", " ", s).strip(" ，,。.")
    return s or text.strip()


def parse_reminder_time(text: str, timezone: str, now: Optional[datetime] = None) -> TimeParseResult:
    raw = text.strip()
    if not raw:
        return TimeParseResult(ok=False, message="empty text")

    if is_recurring_request(raw):
        return TimeParseResult(
            ok=False,
            recurring_required=True,
            message="检测到重复提醒，需用户确认后再创建",
            reminder_text=_clean_reminder_text(raw),
        )

    if not has_explicit_clock(raw):
        return TimeParseResult(ok=False, message="no explicit clock time")

    tz = get_timezone(timezone)
    if now is None:
        now = datetime.now(tz)
    else:
        now = now.astimezone(tz)

    strict_today = "今天" in raw or "今晚" in raw
    day_offset: Optional[int] = None
    if "大后天" in raw:
        day_offset = 3
    elif "后天" in raw:
        day_offset = 2
    elif "明天" in raw or "明早" in raw:
        day_offset = 1
    elif "今天" in raw or "今晚" in raw:
        day_offset = 0

    target_date: Optional[date] = None
    hour: Optional[int] = None
    minute = 0

    m_iso = ISO_DATETIME_RE.search(raw)
    if m_iso and m_iso.group(4):
        y, mo, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        hour, minute = int(m_iso.group(4)), int(m_iso.group(5))
        target_date = date(y, mo, d)
    elif re.search(r"\d{1,2}:\d{2}", raw):
        m = CLOCK_COLON_RE.search(raw)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))
            if "大后天" in raw:
                day_offset = 3
            elif "后天" in raw:
                day_offset = 2
            elif "明天" in raw or "明早" in raw:
                day_offset = 1
            elif "今天" in raw or "今晚" in raw:
                day_offset = 0
                strict_today = True
            if day_offset is None:
                day_offset = 0
            target_date = now.date() + timedelta(days=day_offset)
    elif CN_DATE_CLOCK_RE.search(raw):
        m = CN_DATE_CLOCK_RE.search(raw)
        assert m
        mo, d = int(m.group(1)), int(m.group(2))
        daypart = m.group(3)
        hour = int(m.group(4))
        minute = 30 if m.group(5) else 0
        hour, minute = _apply_daypart(hour, minute, daypart)
        year = now.year
        target_date = date(year, mo, d)
        if target_date < now.date():
            target_date = date(year + 1, mo, d)
    elif CLOCK_CN_RE.search(raw):
        m = CLOCK_CN_RE.search(raw)
        assert m
        rel = m.group(1)
        daypart = m.group(2)
        hour = int(m.group(3))
        minute = 30 if m.group(4) else 0
        hour, minute = _apply_daypart(hour, minute, daypart)
        if rel in ("今天", "今晚"):
            day_offset = 0
            strict_today = True
        elif rel == "明天" or rel == "明早":
            day_offset = 1
        elif rel == "后天":
            day_offset = 2
        elif rel == "大后天":
            day_offset = 3
        if day_offset is None:
            day_offset = 0
        target_date = now.date() + timedelta(days=day_offset)

    if target_date is None or hour is None:
        return TimeParseResult(ok=False, message="无法解析时间")

    trigger = datetime(
        target_date.year, target_date.month, target_date.day, hour, minute, 0, tzinfo=tz
    )
    assumed: Optional[str] = None

    if strict_today and trigger <= now:
        return TimeParseResult(
            ok=False,
            message="指定今天的时间已过，请确认新的提醒时间",
            reminder_text=_clean_reminder_text(raw),
        )

    if not strict_today and day_offset in (None, 0) and trigger <= now:
        trigger = trigger + timedelta(days=1)
        assumed = trigger.date().isoformat()

    return TimeParseResult(
        ok=True,
        trigger_at=trigger,
        assumed_date=assumed,
        reminder_text=_clean_reminder_text(raw),
        message="",
    )
