# -*- coding: utf-8 -*-
"""生成 iCalendar (.ics)，供 iPhone「日历 → 添加日历 - 订阅」使用。

- 法定假、调休：data/holidays.json（须每年按国务院办公厅通知更新）
- 二十四节气：sxtwl（寿星天文历）
- 农历传统节日：zhdate
- 国际节日：脚本内固定规则

用法: python generate_ics.py --start 2024 --end 2026 --out out
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import List, Tuple

import sxtwl
from zhdate import ZhDate

JQ_INDEX_TO_NAME = (
    "冬至",
    "小寒",
    "大寒",
    "立春",
    "雨水",
    "惊蛰",
    "春分",
    "清明",
    "谷雨",
    "立夏",
    "小满",
    "芒种",
    "夏至",
    "小暑",
    "大暑",
    "立秋",
    "处暑",
    "白露",
    "秋分",
    "寒露",
    "霜降",
    "立冬",
    "小雪",
    "大雪",
)

TRADITIONAL_LUNAR_EVENTS: List[Tuple[int, int, str, bool]] = [
    (1, 15, "元宵节（正月十五）", False),
    (2, 2, "龙抬头（二月初二）", False),
    (5, 5, "端午节（五月初五）", False),
    (7, 7, "七夕（七月初七）", False),
    (7, 15, "中元节（七月十五）", False),
    (8, 15, "中秋节（八月十五）", False),
    (9, 9, "重阳节（九月初九）", False),
    (12, 8, "腊八节（腊月初八）", False),
    (12, 23, "小年（北方·腊月廿三）", False),
    (12, 24, "小年（南方·腊月廿四）", False),
]


def _parse_date(s: str) -> date:
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


def _gregorian_jieqi_for_year(y: int):
    out = []
    seen = set()
    for src in (sxtwl.getJieQiByYear(y - 1), sxtwl.getJieQiByYear(y)):
        for info in src:
            dd = sxtwl.JD2DD(info.jd)
            d = date(int(dd.Y), int(dd.M), int(dd.D))
            if d.year != y:
                continue
            key = (info.jqIndex, d.toordinal())
            if key in seen:
                continue
            seen.add(key)
            name = JQ_INDEX_TO_NAME[info.jqIndex % 24]
            sec = int(round(float(dd.s)))
            if sec >= 60:
                sec = 59
            elif sec < 0:
                sec = 0
            mi = int(dd.m)
            if mi >= 60:
                mi = 59
            elif mi < 0:
                mi = 0
            hh = int(dd.h)
            if hh >= 24:
                hh = 23
            elif hh < 0:
                hh = 0
            tout = (hh, mi, sec, int(dd.Y), int(dd.M), int(dd.D))
            out.append((d, name, tout))
    out.sort(key=lambda x: x[0])
    return out


def _lunar_solar_dates_in_gregorian_year(
    gregorian_year: int, lunar_month: int, lunar_day: int, leap: bool = False
) -> List[date]:
    found: List[date] = []
    for ly in (gregorian_year - 1, gregorian_year, gregorian_year + 1):
        try:
            dt = ZhDate(ly, lunar_month, lunar_day, leap_month=leap).to_datetime()
        except TypeError:
            dt = ZhDate(ly, lunar_month, lunar_day).to_datetime()
        except Exception:
            continue
        d = dt.date()
        if d.year == gregorian_year:
            found.append(d)
    return sorted(set(found))


def _nth_weekday_in_month(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _thanksgiving_us(year: int) -> date:
    return _nth_weekday_in_month(year, 11, 3, 4)


def _ics_escape(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def _fold_line(line: str, limit: int = 75) -> List[str]:
    if len(line) <= limit:
        return [line]
    parts = [line[:limit]]
    rest = line[limit:]
    while rest:
        parts.append(" " + rest[: limit - 1])
        rest = rest[limit - 1 :]
    return parts


def _uid(*parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]
    return "%s@chinese-ics" % h


def _dtstamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _format_date_value(d: date) -> str:
    return d.strftime("%Y%m%d")


def add_all_day_vevent(
    lines: List[str],
    start: date,
    end_exclusive: date,
    summary: str,
    uid: str,
    categories: str,
    description: str = "",
) -> None:
    lines.append("BEGIN:VEVENT")
    lines.append("UID:%s" % uid)
    lines.append("DTSTAMP:%s" % _dtstamp_utc())
    lines.append("DTSTART;VALUE=DATE:%s" % _format_date_value(start))
    lines.append("DTEND;VALUE=DATE:%s" % _format_date_value(end_exclusive))
    for L in _fold_line("SUMMARY:%s" % _ics_escape(summary)):
        lines.append(L)
    if description:
        for L in _fold_line("DESCRIPTION:%s" % _ics_escape(description)):
            lines.append(L)
    for L in _fold_line("CATEGORIES:%s" % _ics_escape(categories)):
        lines.append(L)
    lines.append("END:VEVENT")


def add_timed_vevent(
    lines: List[str],
    start_dt: datetime,
    end_dt: datetime,
    summary: str,
    uid: str,
    categories: str,
    description: str = "",
) -> None:
    def fmt_z(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
        dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y%m%dT%H%M%SZ")

    lines.append("BEGIN:VEVENT")
    lines.append("UID:%s" % uid)
    lines.append("DTSTAMP:%s" % _dtstamp_utc())
    lines.append("DTSTART:%s" % fmt_z(start_dt))
    lines.append("DTEND:%s" % fmt_z(end_dt))
    for L in _fold_line("SUMMARY:%s" % _ics_escape(summary)):
        lines.append(L)
    if description:
        for L in _fold_line("DESCRIPTION:%s" % _ics_escape(description)):
            lines.append(L)
    for L in _fold_line("CATEGORIES:%s" % _ics_escape(categories)):
        lines.append(L)
    lines.append("END:VEVENT")


def load_official(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_calendar_official(holiday_data: dict, years: range, lines: List[str]) -> None:
    for y in years:
        key = str(y)
        block = holiday_data.get(key)
        if not block:
            continue
        for v in block.get("vacations", []):
            start = _parse_date(v["start"])
            end_incl = _parse_date(v["end"])
            end_ex = end_incl + timedelta(days=1)
            name = v["name"]
            note = v.get("note", "")
            desc = "中国法定节假日（国务院公布）" + ("。%s" % note if note else "")
            add_all_day_vevent(
                lines,
                start,
                end_ex,
                "%s（放假）" % name,
                _uid("vac", key, v["start"], v["end"], name),
                "法定假日",
                desc,
            )
        for m in block.get("makeup_workdays", []):
            d = _parse_date(m["date"])
            for_label = m.get("for", "调休")
            add_all_day_vevent(
                lines,
                d,
                d + timedelta(days=1),
                "调休上班（%s）" % for_label,
                _uid("work", m["date"], for_label),
                "调休补班",
                "原为周末，调整为工作日。",
            )


def build_calendar_jieqi(years: range, lines: List[str]) -> None:
    for y in years:
        for d, name, tinfo in _gregorian_jieqi_for_year(y):
            h, mi, s, Y, M, D = tinfo
            desc = (
                "二十四节气。推算时刻（东八区）%04d-%02d-%02d %02d:%02d:%02d（sxtwl 寿星天文历）。民俗以当日日历为准。"
                % (Y, M, D, h, mi, s)
            )
            start = datetime(Y, M, D, h, mi, s, tzinfo=timezone(timedelta(hours=8)))
            end = start + timedelta(minutes=30)
            add_timed_vevent(
                lines,
                start,
                end,
                name,
                _uid("jq", str(d), name),
                "二十四节气",
                desc,
            )


def build_calendar_traditional_lunar(years: range, lines: List[str]) -> None:
    for y in years:
        try:
            sf = ZhDate(y, 1, 1).to_datetime().date()
            if sf.year == y:
                add_all_day_vevent(
                    lines,
                    sf,
                    sf + timedelta(days=1),
                    "春节（农历正月初一）",
                    _uid("lunar", str(y), "spring"),
                    "传统节日",
                    "农历新年。法定春节假期以国务院安排为准。",
                )
                eve = sf - timedelta(days=1)
                if eve.year == y:
                    add_all_day_vevent(
                        lines,
                        eve,
                        eve + timedelta(days=1),
                        "除夕（农历）",
                        _uid("lunar", str(y), "eve"),
                        "传统节日",
                    )
        except Exception:
            pass
        for lm, ld, label, leap in TRADITIONAL_LUNAR_EVENTS:
            for d in _lunar_solar_dates_in_gregorian_year(y, lm, ld, leap=leap):
                add_all_day_vevent(
                    lines,
                    d,
                    d + timedelta(days=1),
                    label,
                    _uid("trad", str(d), label),
                    "传统节日",
                )


def build_calendar_intl(years: range, lines: List[str]) -> None:
    def one(d: date, summary: str, description: str = "") -> None:
        add_all_day_vevent(
            lines,
            d,
            d + timedelta(days=1),
            summary,
            _uid("intl", str(d), summary),
            "国际节日",
            description,
        )

    for y in years:
        one(date(y, 1, 1), "新年（公历）")
        one(date(y, 2, 14), "情人节")
        one(date(y, 3, 8), "国际妇女节")
        one(date(y, 3, 12), "植树节（中国）")
        one(date(y, 3, 15), "国际消费者权益日")
        one(date(y, 4, 1), "愚人节")
        one(date(y, 6, 1), "国际儿童节")
        one(date(y, 12, 25), "圣诞节")
        one(date(y, 10, 31), "万圣节前夜")
        mothers = _nth_weekday_in_month(y, 5, 6, 2)
        fathers = _nth_weekday_in_month(y, 6, 6, 3)
        one(mothers, "母亲节", "5 月第二个星期日（常见惯例）")
        one(fathers, "父亲节", "6 月第三个星期日（常见惯例）")
        one(_thanksgiving_us(y), "感恩节（美国）", "11 月第四个星期四")


def write_ical(path: str, lines: List[str]) -> None:
    dn = os.path.dirname(path)
    if dn:
        os.makedirs(dn, exist_ok=True)
    body = "\r\n".join(lines) + "\r\n"
    with open(path, "wb") as f:
        f.write(body.encode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--out", type=str, default="out")
    ap.add_argument("--data", type=str, default="")
    args = ap.parse_args()
    if args.end < args.start:
        print("end < start", file=sys.stderr)
        sys.exit(1)
    years = range(args.start, args.end + 1)
    data_path = args.data or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "holidays.json"
    )
    holiday_data = load_official(data_path)

    bundles = [
        ("china-official.ics", lambda ls: build_calendar_official(holiday_data, years, ls)),
        ("solar-terms.ics", lambda ls: build_calendar_jieqi(years, ls)),
        ("traditional-lunar.ics", lambda ls: build_calendar_traditional_lunar(years, ls)),
        ("international.ics", lambda ls: build_calendar_intl(years, ls)),
    ]

    for name, builder in bundles:
        lines: List[str] = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Chinese Calendar ICS//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:中国历（模块化）",
            "X-WR-TIMEZONE:Asia/Shanghai",
        ]
        builder(lines)
        lines.append("END:VCALENDAR")
        write_ical(os.path.join(args.out, name), lines)

    combined: List[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Chinese Calendar ICS//combined//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:节假日·节气·传统·国际",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]
    build_calendar_official(holiday_data, years, combined)
    build_calendar_jieqi(years, combined)
    build_calendar_traditional_lunar(years, combined)
    build_calendar_intl(years, combined)
    combined.append("END:VCALENDAR")
    write_ical(os.path.join(args.out, "combined.ics"), combined)
    print("OK ->", os.path.abspath(args.out))


if __name__ == "__main__":
    main()
