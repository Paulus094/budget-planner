from __future__ import annotations

from typing import List

from nicegui import ui

from app.config import GERMAN_MONTHS
from app.models.db import calc_level0_total, db_get_items, db_get_user_months


def render_history_chart(user_id: int) -> None:
    months_data = db_get_user_months(user_id)
    months_data = sorted(months_data, key=lambda x: (x["year"], x["month"]))[-12:]
    if len(months_data) < 2:
        return

    categories: List[str] = []
    income_series: List[float] = []
    expense_series: List[float] = []
    balance_series: List[float] = []

    for m in months_data:
        tid = m["id"]
        inc = db_get_items(tid, "income_items")
        fix = db_get_items(tid, "fixed_expense_items")
        pot = db_get_items(tid, "pot_items")
        i_total = calc_level0_total(inc, "amount")
        e_total = calc_level0_total(fix, "amount") + calc_level0_total(pot, "amount")
        categories.append(f"{GERMAN_MONTHS[m['month'] - 1][:3]} {str(m['year'])[-2:]}")
        income_series.append(round(i_total, 2))
        expense_series.append(round(e_total, 2))
        balance_series.append(round(i_total - e_total, 2))

    with ui.card().classes("w-full"):
        ui.label("Verlauf (letzte 12 Monate)").classes("text-base font-bold text-gray-700 mb-2")
        ui.highchart(
            {
                "chart": {"type": "line"},
                "title": {"text": ""},
                "xAxis": {"categories": categories},
                "yAxis": {
                    "title": {"text": "Betrag (€)"},
                    "labels": {
                        "formatter": "function() { return this.value.toLocaleString('de-DE') + ' €'; }"
                    },
                },
                "tooltip": {
                    "valueDecimals": 2,
                    "valueSuffix": " €",
                },
                "series": [
                    {"name": "Einnahmen", "data": income_series, "color": "#22c55e"},
                    {"name": "Ausgaben", "data": expense_series, "color": "#ef4444"},
                    {"name": "Bilanz", "data": balance_series, "color": "#3b82f6"},
                ],
                "credits": {"enabled": False},
            }
        ).classes("w-full h-72")
