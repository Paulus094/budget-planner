"""
Budget-Planer Auth Service
FastAPI-Dienst für Nutzerverwaltung und JWT-Authentifizierung.
"""

import logging
import os
import time

import bcrypt
import jwt
import psycopg2
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://budget:budget_secret@db:5432/budget_db",
)
JWT_SECRET = os.getenv("JWT_SECRET", "changeme-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # 7 Tage

# Initialer Admin-Nutzer (aus Umgebungsvariablen)
INITIAL_ADMIN_USER = os.getenv("INITIAL_ADMIN_USER", "")
INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "")

security = HTTPBearer()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Budget-Planer Auth Service", version="1.0.0")


# ---------------------------------------------------------------------------
# DB-Hilfsfunktionen
# ---------------------------------------------------------------------------
def _connect(retries: int = 10, delay: float = 2.0) -> psycopg2.extensions.connection:
    """Verbindungsaufbau mit Retry-Logik für den Container-Start."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            return psycopg2.connect(DATABASE_URL)
        except Exception as exc:
            last_err = exc
            logger.warning("DB nicht erreichbar (Versuch %d/%d): %s", attempt, retries, exc)
            time.sleep(delay)
    raise RuntimeError(f"Konnte keine DB-Verbindung herstellen: {last_err}")


# ---------------------------------------------------------------------------
# JWT-Hilfsfunktionen
# ---------------------------------------------------------------------------
def _create_token(user_id: int, username: str, is_admin: bool) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "is_admin": is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token abgelaufen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ungültiger Token")


def _require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = _decode_token(credentials.credentials)
    if not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin-Rechte erforderlich")
    return payload


# ---------------------------------------------------------------------------
# Pydantic-Modelle
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6)
    is_admin: bool = False


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    is_admin: bool


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


# ---------------------------------------------------------------------------
# Startup: initialen Admin anlegen
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup() -> None:
    if not INITIAL_ADMIN_USER or not INITIAL_ADMIN_PASSWORD:
        logger.info("Kein initialer Admin konfiguriert (INITIAL_ADMIN_USER / INITIAL_ADMIN_PASSWORD).")
        return

    conn = _connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (INITIAL_ADMIN_USER,))
            if cur.fetchone():
                logger.info("Admin-Nutzer '%s' existiert bereits.", INITIAL_ADMIN_USER)
                return
            hashed = bcrypt.hashpw(INITIAL_ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
            cur.execute(
                "INSERT INTO users (username, hashed_password, is_admin) VALUES (%s, %s, %s)",
                (INITIAL_ADMIN_USER, hashed, True),
            )
        conn.commit()
        logger.info("Initialer Admin-Nutzer '%s' angelegt.", INITIAL_ADMIN_USER)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Endpunkte
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin) -> TokenResponse:
    conn = _connect(retries=3)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (credentials.username,))
            user = cur.fetchone()

        if not user or not bcrypt.checkpw(
            credentials.password.encode(), user["hashed_password"].encode()
        ):
            raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")

        token = _create_token(user["id"], user["username"], user["is_admin"])
        return TokenResponse(
            access_token=token,
            user_id=user["id"],
            username=user["username"],
            is_admin=user["is_admin"],
        )
    finally:
        conn.close()


@app.get("/verify")
def verify(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = _decode_token(credentials.credentials)
    return {
        "user_id": int(payload["sub"]),
        "username": payload["username"],
        "is_admin": payload["is_admin"],
    }


@app.post("/register")
def register(user: UserCreate, _admin: dict = Depends(_require_admin)) -> dict:
    """Neuen Nutzer anlegen – nur für Admins."""
    conn = _connect(retries=3)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (user.username,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")

            hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
            cur.execute(
                "INSERT INTO users (username, hashed_password, is_admin) VALUES (%s, %s, %s) RETURNING id",
                (user.username, hashed, user.is_admin),
            )
            new_id = cur.fetchone()["id"]
        conn.commit()
        return {"id": new_id, "username": user.username, "message": "Nutzer angelegt"}
    finally:
        conn.close()


@app.delete("/users/{user_id}")
def delete_user(user_id: int, _admin: dict = Depends(_require_admin)) -> dict:
    """Nutzer löschen – nur für Admins."""
    conn = _connect(retries=3)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")
        conn.commit()
        return {"message": "Nutzer gelöscht"}
    finally:
        conn.close()


@app.post("/change-password")
def change_password(
    data: PasswordChange,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Eigenes Passwort ändern."""
    payload = _decode_token(credentials.credentials)
    user_id = int(payload["sub"])

    conn = _connect(retries=3)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT hashed_password FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user or not bcrypt.checkpw(
                data.old_password.encode(), user["hashed_password"].encode()
            ):
                raise HTTPException(status_code=401, detail="Altes Passwort falsch")

            new_hash = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
            cur.execute("UPDATE users SET hashed_password = %s WHERE id = %s", (new_hash, user_id))
        conn.commit()
        return {"message": "Passwort geändert"}
    finally:
        conn.close()


@app.get("/users")
def list_users(_admin: dict = Depends(_require_admin)) -> list:
    """Alle Nutzer auflisten – nur für Admins."""
    conn = _connect(retries=3)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, is_admin, created_at FROM users ORDER BY username"
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
