"""
Budget-Planer – NiceGUI-Frontend
"""

import logging

from nicegui import ui

from app.config import STORAGE_SECRET

from app.controllers.login import index_page, login_page
from app.controllers.budget_app import budget_app_page
from app.controllers.admin import admin_page

__all__ = ["index_page", "login_page", "budget_app_page", "admin_page"]

logging.basicConfig(level=logging.INFO)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=8080,
        title="Budget-Planer",
        storage_secret=STORAGE_SECRET,
        reload=False,
        show=False,
        favicon="💰",
    )
