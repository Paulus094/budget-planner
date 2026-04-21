from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import httpx
from nicegui import app

from app.config import AUTH_URL

logger = logging.getLogger(__name__)


def auth_login(username: str, password: str) -> Optional[Dict]:
    try:
        resp = httpx.post(
            f"{AUTH_URL}/login",
            json={"username": username, "password": password},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as exc:
        logger.error("Auth-Login fehlgeschlagen: %s", exc)
        return None


def auth_verify(token: str) -> Optional[Dict]:
    try:
        resp = httpx.get(
            f"{AUTH_URL}/verify",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as exc:
        logger.error("Token-Verifizierung fehlgeschlagen: %s", exc)
        return None


def auth_register(token: str, username: str, password: str, is_admin: bool) -> Tuple[bool, str]:
    try:
        resp = httpx.post(
            f"{AUTH_URL}/register",
            json={"username": username, "password": password, "is_admin": is_admin},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return True, "Nutzer angelegt"
        return False, resp.json().get("detail", "Fehler")
    except Exception as exc:
        return False, str(exc)


def auth_delete_user(token: str, user_id: int) -> Tuple[bool, str]:
    try:
        resp = httpx.delete(
            f"{AUTH_URL}/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return True, "Nutzer gelöscht"
        return False, resp.json().get("detail", "Fehler")
    except Exception as exc:
        return False, str(exc)


def auth_change_password(token: str, old_pw: str, new_pw: str) -> Tuple[bool, str]:
    try:
        resp = httpx.post(
            f"{AUTH_URL}/change-password",
            json={"old_password": old_pw, "new_password": new_pw},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return True, "Passwort geändert"
        return False, resp.json().get("detail", "Fehler")
    except Exception as exc:
        return False, str(exc)


def auth_list_users(token: str) -> List[Dict]:
    try:
        resp = httpx.get(
            f"{AUTH_URL}/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception:
        return []


def get_current_user() -> Optional[Dict]:
    return app.storage.user.get("user_info")


def get_token() -> str:
    return app.storage.user.get("token", "")
