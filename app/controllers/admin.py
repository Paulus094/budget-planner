from __future__ import annotations

from nicegui import ui

from app.models.auth import (
    auth_change_password,
    auth_delete_user,
    auth_list_users,
    auth_register,
    get_current_user,
    get_token,
)
from app.views.components import make_header


@ui.page("/admin")
def admin_page() -> None:
    user = get_current_user()
    if not user:
        ui.navigate.to("/login")
        return
    if not user.get("is_admin"):
        ui.navigate.to("/app")
        return

    make_header("⚙️ Admin-Bereich", show_admin=True)
    token = get_token()

    with ui.column().classes("w-full max-w-3xl mx-auto px-4 py-6 gap-6"):
        ui.label("Nutzerverwaltung").classes("text-2xl font-bold text-blue-800")

        with ui.card().classes("w-full"):
            ui.label("Neuen Nutzer anlegen").classes("text-lg font-semibold mb-3")
            with ui.row().classes("gap-4 items-end flex-wrap"):
                new_user_in = ui.input("Benutzername").classes("flex-1 min-w-40")
                new_pw_in = ui.input("Passwort", password=True).classes("flex-1 min-w-40")
                admin_cb = ui.checkbox("Admin-Rechte")
            err_lbl = ui.label("").classes("text-red-500 text-sm min-h-4")

            def create_user() -> None:
                uname = new_user_in.value.strip()
                pw = new_pw_in.value
                if not uname or not pw:
                    err_lbl.set_text("Bitte alle Felder ausfüllen.")
                    return
                ok, msg = auth_register(token, uname, pw, admin_cb.value)
                if ok:
                    ui.notify(f"Nutzer '{uname}' angelegt ✓", color="positive")
                    new_user_in.set_value("")
                    new_pw_in.set_value("")
                    admin_cb.set_value(False)
                    err_lbl.set_text("")
                    refresh_table()
                else:
                    err_lbl.set_text(msg)

            ui.button("Anlegen", on_click=create_user).props("color=primary").classes("mt-2")

        user_container = ui.column().classes("w-full")

        def refresh_table() -> None:
            users = auth_list_users(token)
            user_container.clear()
            with user_container:
                with ui.card().classes("w-full"):
                    ui.label("Vorhandene Nutzer").classes("text-lg font-semibold mb-3")
                    if not users:
                        ui.label("Keine Nutzer gefunden.").classes("text-gray-400")
                        return
                    ui.table(
                        columns=[
                            {"name": "username", "label": "Benutzername", "field": "username", "align": "left"},
                            {"name": "admin", "label": "Admin", "field": "admin", "align": "center"},
                            {"name": "created", "label": "Erstellt am", "field": "created", "align": "left"},
                            {"name": "actions", "label": "Aktionen", "field": "actions", "align": "center"},
                        ],
                        rows=[
                            {
                                "id": u["id"],
                                "username": u["username"],
                                "admin": "✓" if u["is_admin"] else "–",
                                "created": str(u.get("created_at", ""))[:10],
                            }
                            for u in users
                        ],
                    ).classes("w-full")

                    ui.label("Nutzer löschen:").classes("text-sm text-gray-500 mt-3")
                    for u in users:
                        if u["id"] == user["user_id"]:
                            continue
                        with ui.row().classes("items-center gap-2"):
                            ui.label(u["username"]).classes("text-sm w-32")
                            ui.button(
                                "Löschen",
                                on_click=lambda uid=u["id"], uname=u["username"]: delete_user(uid, uname),
                            ).props("color=negative outline dense")

        def delete_user(uid: int, uname: str) -> None:
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Nutzer '{uname}' wirklich löschen?").classes("font-bold")
                ui.label("Alle Budget-Daten dieses Nutzers werden ebenfalls entfernt.").classes(
                    "text-sm text-gray-500 mt-1"
                )
                with ui.row().classes("justify-end gap-2 mt-4"):
                    ui.button("Abbrechen", on_click=dlg.close).props("flat")

                    def do_delete() -> None:
                        dlg.close()
                        ok, msg = auth_delete_user(token, uid)
                        if ok:
                            ui.notify(f"Nutzer '{uname}' gelöscht", color="positive")
                            refresh_table()
                        else:
                            ui.notify(f"Fehler: {msg}", color="negative")

                    ui.button("Löschen", on_click=do_delete).props("color=negative")
            dlg.open()

        refresh_table()

        with ui.card().classes("w-full"):
            ui.label("Eigenes Passwort ändern").classes("text-lg font-semibold mb-3")
            with ui.row().classes("gap-4 items-end flex-wrap"):
                old_pw_in = ui.input("Aktuelles Passwort", password=True).classes("flex-1 min-w-40")
                new_pw1_in = ui.input("Neues Passwort", password=True).classes("flex-1 min-w-40")
                new_pw2_in = ui.input("Neues Passwort (wdh.)", password=True).classes("flex-1 min-w-40")
            pw_err = ui.label("").classes("text-red-500 text-sm min-h-4")

            def change_pw() -> None:
                if new_pw1_in.value != new_pw2_in.value:
                    pw_err.set_text("Neue Passwörter stimmen nicht überein.")
                    return
                ok, msg = auth_change_password(token, old_pw_in.value, new_pw1_in.value)
                if ok:
                    ui.notify("Passwort geändert ✓", color="positive")
                    old_pw_in.set_value("")
                    new_pw1_in.set_value("")
                    new_pw2_in.set_value("")
                    pw_err.set_text("")
                else:
                    pw_err.set_text(msg)

            ui.button("Passwort ändern", on_click=change_pw).props("color=primary").classes("mt-2")
