from __future__ import annotations

from typing import Any, Dict, List, Optional

from nicegui import ui

from app.models.db import db_save_items
from app.utils import parse_amount


def surplus_table(
    tab_id: int,
    items: List[Dict],
    locked: bool,
    on_saved: Optional[callable] = None,
) -> None:
    rows: List[Dict] = [
        {
            "name": item.get("name", ""),
            "monthly_amount": float(item.get("monthly_amount", 0) or 0),
            "strategy": str(item.get("strategy", "") or ""),
            "current_value": float(item.get("current_value", 0) or 0),
            "level": int(item.get("level", 0) or 0),
        }
        for item in items
    ]
    while len(rows) < 6 or (rows and rows[-1]["name"]):
        rows.append({"name": "", "monthly_amount": 0.0, "strategy": "", "current_value": 0.0, "level": 0})

    with ui.card().classes("w-full"):
        ui.label("Überschussverteilung").classes("text-base font-bold text-gray-700 mb-1")

        grid = ui.aggrid(
            {
                "columnDefs": [
                    {"field": "name", "headerName": "Bezeichnung", "editable": not locked, "flex": 2},
                    {
                        "field": "monthly_amount",
                        "headerName": "Monatl. Betrag",
                        "editable": not locked,
                        "flex": 2,
                        "type": "numericColumn",
                        "valueFormatter": (
                            "parseFloat(params.value || 0)"
                            ".toLocaleString('de-DE', "
                            "{minimumFractionDigits:2, maximumFractionDigits:2}) + ' €'"
                        ),
                    },
                    {"field": "strategy", "headerName": "Strategie", "editable": not locked, "flex": 2},
                    {
                        "field": "current_value",
                        "headerName": "Aktueller Stand",
                        "editable": not locked,
                        "flex": 2,
                        "type": "numericColumn",
                        "valueFormatter": (
                            "params.value ? parseFloat(params.value)"
                            ".toLocaleString('de-DE', "
                            "{minimumFractionDigits:2, maximumFractionDigits:2}) + ' €' : ''"
                        ),
                    },
                    {
                        "field": "level",
                        "headerName": "Ebene",
                        "editable": not locked,
                        "width": 90,
                        "type": "numericColumn",
                    },
                ],
                "rowData": rows,
                "domLayout": "autoHeight",
                "suppressMovableColumns": True,
                "stopEditingWhenCellsLoseFocus": True,
                "defaultColDef": {"resizable": True, "sortable": False},
            }
        ).classes("w-full")

        def on_change(e: Any) -> None:
            data = e.args.get("data", {})
            row_idx = e.args.get("rowIndex")
            if row_idx is None:
                return

            while len(rows) <= row_idx:
                rows.append({"name": "", "monthly_amount": 0.0, "strategy": "", "current_value": 0.0, "level": 0})

            rows[row_idx]["name"] = str(data.get("name", "")).strip()
            rows[row_idx]["monthly_amount"] = parse_amount(data.get("monthly_amount", 0))
            rows[row_idx]["strategy"] = str(data.get("strategy", "") or "")
            rows[row_idx]["current_value"] = parse_amount(data.get("current_value", 0))
            rows[row_idx]["level"] = max(0, int(data.get("level", 0) or 0))

            while rows and not rows[-1]["name"]:
                rows.pop()
            for _ in range(3):
                rows.append({"name": "", "monthly_amount": 0.0, "strategy": "", "current_value": 0.0, "level": 0})

            db_save_items(tab_id, "surplus_items", rows)
            grid.options["rowData"] = list(rows)
            grid.update()

            if on_saved:
                on_saved()

        if not locked:
            grid.on("cellValueChanged", on_change)
