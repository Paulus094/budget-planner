import os

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8001")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://budget:budget_secret@db:5432/budget_db",
)
STORAGE_SECRET = os.getenv("NICEGUI_SECRET", "nicegui-secret-changeme")

GERMAN_MONTHS = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]
