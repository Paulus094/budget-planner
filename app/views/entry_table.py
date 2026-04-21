from __future__ import annotations

from typing import Any, Dict, List, Optional

from nicegui import ui

from app.models.db import db_save_items
from app.utils import parse_amount


def entry_table(
    title: str,
    tab_id: int,
    table_name: str,
    items: List[Dict],
    locked: bool,
    on_saved: Optional[callable] = None,
) -> None:
    rows: List[Dict] = [
        {
            "name": item.get("name", ""),
            "amount": float(item.get("amount", 0) or 0),
            "level": int(item.get("level", 0) or 0),
        }
        for item in items
    ]
    while len(rows) < 8 or (rows and rows[-1]["name"]):
        rows.append({"name": "", "amount": 0.0, "level": 0})

    with ui.card().classes("w-full"):
        ui.label(title).classes("text-base font-bold text-gray-700 mb-1")

        grid = ui.aggrid(
            {
                "columnDefs": [
                    {
                        "field": "name",
                        "headerName": "Bezeichnung",
                        "editable": not locked,
                        "flex": 3,
                        "cellStyle": {
                            "fontWeight": "var(--level-weight, normal)",
                        },
                    },
                    {
                        "field": "amount",
                        "headerName": "Betrag (€)",
                        "editable": not locked,
                        "flex": 2,
                        "type": "numericColumn",
                        "valueFormatter": (
                            "parseFloat(params.value || 0)"
                            ".toLocaleString('de-DE', "
                            "{minimumFractionDigits:2, maximumFractionDigits:2}) + ' €'"
                        ),
                    },
                    {
                        "field": "level",
                        "headerName": "Ebene",
                        "editable": not locked,
                        "width": 90,
                        "type": "numericColumn",
                        "headerTooltip": "0 = Hauptposten, 1 = Unterposten",
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
                rows.append({"name": "", "amount": 0.0, "level": 0})

            rows[row_idx]["name"] = str(data.get("name", "")).strip()
            rows[row_idx]["amount"] = parse_amount(data.get("amount", 0))
            rows[row_idx]["level"] = max(0, int(data.get("level", 0) or 0))

            while rows and not rows[-1]["name"]:
                rows.pop()
            for _ in range(3):
                rows.append({"name": "", "amount": 0.0, "level": 0})

            db_save_items(tab_id, table_name, rows)
            grid.options["rowData"] = list(rows)
            grid.update()

            if on_saved:
                on_saved()

        if not locked:
            grid.on("cellValueChanged", on_change)
