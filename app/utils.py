from __future__ import annotations

from typing import Any, Tuple

from app.config import GERMAN_MONTHS


def parse_amount(text: Any) -> float:
    if text is None:
        return 0.0
    if isinstance(text, (int, float)):
        return float(text)
    s = str(text).strip().replace("€", "").replace("EUR", "").replace(" ", "")
    if not s:
        return 0.0
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def format_eur(amount: float) -> str:
    try:
        value = float(amount)
    except Exception:
        value = 0.0
    neg = value < 0
    value = abs(value)
    integer = int(value)
    decimals = int(round((value - integer) * 100))
    if decimals == 100:
        integer += 1
        decimals = 0
    int_str = f"{integer:,}".replace(",", "X").replace(".", ",").replace("X", ".")
    out = f"{int_str},{decimals:02d} €"
    return f"-{out}" if neg else out


def month_label(year: int, month: int) -> str:
    return f"{GERMAN_MONTHS[month - 1]} {year}"


def add_months(year: int, month: int, delta: int = 1) -> Tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    ny = total // 12
    nm = total % 12 + 1
    return ny, nm
