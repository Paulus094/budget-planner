from __future__ import annotations

from nicegui import app, ui

from app.models.auth import auth_login, get_current_user


@ui.page("/")
def index_page() -> None:
    user = get_current_user()
    if user:
        ui.navigate.to("/app")
    else:
        ui.navigate.to("/login")


@ui.page("/login")
def login_page() -> None:
    if get_current_user():
        ui.navigate.to("/app")
        return

    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1">')

    with ui.column().classes(
        "absolute-center items-center gap-5 w-full max-w-sm px-6"
    ):
        ui.label("💰 Budget-Planer").classes("text-3xl font-bold text-blue-700")
        ui.label("Bitte anmelden").classes("text-gray-500")

        with ui.card().classes("w-full p-6 shadow-lg"):
            username_in = ui.input("Benutzername", placeholder="dein-name").classes("w-full")
            password_in = ui.input(
                "Passwort", password=True, password_toggle_button=True
            ).classes("w-full mt-2")
            error_lbl = ui.label("").classes("text-red-500 text-sm min-h-5")
            login_btn = ui.button("Anmelden").classes("w-full mt-2 bg-blue-700 text-white")

            def do_login() -> None:
                uname = username_in.value.strip()
                pw = password_in.value
                if not uname or not pw:
                    error_lbl.set_text("Bitte Benutzername und Passwort eingeben.")
                    return
                error_lbl.set_text("Anmelden …")
                result = auth_login(uname, pw)
                if result:
                    app.storage.user["token"] = result["access_token"]
                    app.storage.user["user_info"] = {
                        "user_id": result["user_id"],
                        "username": result["username"],
                        "is_admin": result["is_admin"],
                    }
                    ui.navigate.to("/app")
                else:
                    error_lbl.set_text("Ungültige Anmeldedaten.")
                    password_in.set_value("")

            password_in.on("keydown.enter", do_login)
            login_btn.on("click", do_login)
