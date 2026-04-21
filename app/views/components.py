from __future__ import annotations

from nicegui import app, ui

from app.models.auth import get_current_user


def make_header(title: str = "Budget-Planer", show_admin: bool = False) -> None:
    user = get_current_user()

    def do_logout():
        app.storage.user.clear()
        ui.navigate.to("/login")

    with ui.header(elevated=True).classes(
        "items-center justify-between px-6 py-3 bg-blue-700 text-white"
    ):
        ui.label(title).classes("text-xl font-bold tracking-wide")
        with ui.row().classes("items-center gap-4"):
            if user:
                ui.label(f"👤 {user.get('username', '')}").classes("text-sm opacity-80")
            if show_admin:
                ui.button("Admin", on_click=lambda: ui.navigate.to("/admin")).props(
                    "flat dense color=white"
                )
            ui.button("Zur App", on_click=lambda: ui.navigate.to("/app")).props(
                "flat dense color=white"
            )
            ui.button("Abmelden", on_click=do_logout).props("flat dense color=white")


def stat_card(title: str, value: str, color_class: str = "text-gray-800") -> None:
    with ui.card().classes("flex-1 text-center py-4 px-2 min-w-32"):
        ui.label(title).classes("text-xs text-gray-500 uppercase tracking-wide")
        ui.label(value).classes(f"text-lg font-bold mt-1 {color_class}")
