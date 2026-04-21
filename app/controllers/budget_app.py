from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from nicegui import ui

from app.models.auth import get_current_user
from app.models.db import (
    calc_level0_total,
    db_delete_tab,
    db_get_items,
    db_get_or_create_tab,
    db_get_tab_info,
    db_get_user_months,
    db_update_tab,
)
from app.utils import add_months, format_eur, month_label
from app.views.components import make_header, stat_card
from app.views.entry_table import entry_table
from app.views.history_chart import render_history_chart
from app.views.surplus_table import surplus_table


@ui.page("/app")
def budget_app_page() -> None:
    user = get_current_user()
    if not user:
        ui.navigate.to("/login")
        return

    user_id: int = user["user_id"]
    is_admin: bool = user.get("is_admin", False)

    make_header("💰 Budget-Planer", show_admin=is_admin)

    now = datetime.now()
    state: Dict[str, Any] = {
        "year": now.year,
        "month": now.month,
        "tab_id": None,
    }

    main_area = ui.column().classes("w-full max-w-screen-xl mx-auto px-4 py-4 gap-4")

    def reload() -> None:
        load_month(state["year"], state["month"])

    def load_month(year: int, month: int) -> None:
        state["year"] = year
        state["month"] = month
        tab_id = db_get_or_create_tab(user_id, year, month)
        state["tab_id"] = tab_id
        tab_info = db_get_tab_info(tab_id)

        income_items = db_get_items(tab_id, "income_items")
        fixed_items = db_get_items(tab_id, "fixed_expense_items")
        pot_items = db_get_items(tab_id, "pot_items")
        surplus_items_data = db_get_items(tab_id, "surplus_items")

        main_area.clear()
        with main_area:
            render_page(tab_id, tab_info, income_items, fixed_items, pot_items, surplus_items_data)

    def render_page(
        tab_id: int,
        tab_info: Dict,
        income_items: List[Dict],
        fixed_items: List[Dict],
        pot_items: List[Dict],
        surplus_items_data: List[Dict],
    ) -> None:
        year: int = state["year"]
        month: int = state["month"]
        locked: bool = bool(tab_info.get("locked", False))

        with ui.row().classes("items-center gap-3 flex-wrap"):
            prev_y, prev_m = add_months(year, month, -1)
            next_y, next_m = add_months(year, month, 1)

            ui.button("‹", on_click=lambda: load_month(prev_y, prev_m)).props(
                "flat round dense"
            ).classes("text-blue-700 text-xl")
            ui.label(month_label(year, month)).classes(
                "text-2xl font-bold text-blue-800 min-w-56 text-center"
            )
            ui.button("›", on_click=lambda: load_month(next_y, next_m)).props(
                "flat round dense"
            ).classes("text-blue-700 text-xl")

            months_list = db_get_user_months(user_id)
            if months_list:
                opts = {
                    f"{m['year']}-{m['month']:02d}": month_label(m["year"], m["month"])
                    for m in months_list
                }

                def on_select(e: Any) -> None:
                    val: str = e.value
                    y, m_ = int(val.split("-")[0]), int(val.split("-")[1])
                    load_month(y, m_)

                ui.select(
                    opts,
                    value=f"{year}-{month:02d}",
                    label="Monat wählen",
                    on_change=on_select,
                ).classes("w-48 ml-4")

            with ui.row().classes("ml-auto gap-2"):
                if locked:
                    ui.button(
                        "🔓 Entsperren",
                        on_click=lambda: toggle_lock(tab_id, False),
                    ).props("color=warning outline")
                else:
                    ui.button(
                        "🔒 Sperren",
                        on_click=lambda: toggle_lock(tab_id, True),
                    ).props("color=grey outline")
                ui.button(
                    "🗑 Monat löschen",
                    on_click=lambda: confirm_delete(tab_id),
                ).props("color=negative outline")

        if locked:
            ui.badge("Gesperrt", color="warning").classes("self-start")

        income_total = calc_level0_total(income_items, "amount")
        fixed_total = calc_level0_total(fixed_items, "amount")
        pots_total = calc_level0_total(pot_items, "amount")
        surplus_base = max(0.0, income_total - fixed_total - pots_total)
        surplus_alloc = calc_level0_total(surplus_items_data, "monthly_amount")
        remainder = surplus_base - surplus_alloc

        with ui.row().classes("w-full gap-3 flex-wrap"):
            stat_card("Einnahmen", format_eur(income_total), "text-green-600")
            stat_card(
                tab_info.get("fixed_title", "Fixkosten"),
                format_eur(fixed_total),
                "text-red-500",
            )
            stat_card(
                tab_info.get("pots_title", "Spartöpfe"),
                format_eur(pots_total),
                "text-orange-500",
            )
            stat_card("Freier Überschuss", format_eur(surplus_base), "text-blue-700")
            stat_card("Verteilt", format_eur(surplus_alloc), "text-indigo-500")
            remainder_color = "text-green-600" if remainder >= 0 else "text-red-500"
            stat_card("Rest", format_eur(remainder), remainder_color)

        with ui.grid(columns=2).classes("w-full gap-4"):
            entry_table(
                "Einnahmen",
                tab_id,
                "income_items",
                income_items,
                locked,
                on_saved=lambda: ui.notify("Gespeichert", color="positive", timeout=1500),
            )
            entry_table(
                tab_info.get("fixed_title", "Fixkosten"),
                tab_id,
                "fixed_expense_items",
                fixed_items,
                locked,
                on_saved=lambda: ui.notify("Gespeichert", color="positive", timeout=1500),
            )

        with ui.grid(columns=2).classes("w-full gap-4"):
            entry_table(
                tab_info.get("pots_title", "Spartöpfe"),
                tab_id,
                "pot_items",
                pot_items,
                locked,
                on_saved=lambda: ui.notify("Gespeichert", color="positive", timeout=1500),
            )
            surplus_table(
                tab_id,
                surplus_items_data,
                locked,
                on_saved=lambda: ui.notify("Gespeichert", color="positive", timeout=1500),
            )

        with ui.expansion("Tabellenbezeichnungen anpassen", icon="settings").classes("w-full"):
            with ui.row().classes("gap-4 items-end"):
                ft_in = ui.input(
                    "Fixkosten-Titel",
                    value=tab_info.get("fixed_title", "Fixkosten"),
                ).classes("flex-1")
                pt_in = ui.input(
                    "Spartopf-Titel",
                    value=tab_info.get("pots_title", "Spartöpfe"),
                ).classes("flex-1")

                def save_titles() -> None:
                    db_update_tab(
                        tab_id,
                        fixed_title=ft_in.value,
                        pots_title=pt_in.value,
                    )
                    ui.notify("Gespeichert", color="positive")
                    reload()

                ui.button("Speichern", on_click=save_titles)

        render_history_chart(user_id)

    def toggle_lock(tab_id: int, locked: bool) -> None:
        db_update_tab(tab_id, locked=locked)
        ui.notify(
            "Monat gesperrt 🔒" if locked else "Monat entsperrt 🔓",
            color="positive",
        )
        reload()

    def confirm_delete(tab_id: int) -> None:
        with ui.dialog() as dlg, ui.card():
            ui.label("Monat wirklich löschen?").classes("text-lg font-bold")
            ui.label(
                "Alle Daten dieses Monats werden unwiderruflich entfernt."
            ).classes("text-sm text-gray-500 mt-1")
            with ui.row().classes("justify-end gap-2 mt-4"):
                ui.button("Abbrechen", on_click=dlg.close).props("flat")

                def do_delete() -> None:
                    dlg.close()
                    db_delete_tab(tab_id)
                    ui.notify("Monat gelöscht", color="positive")
                    load_month(datetime.now().year, datetime.now().month)

                ui.button("Löschen", on_click=do_delete).props("color=negative")
        dlg.open()

    load_month(now.year, now.month)
