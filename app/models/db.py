from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import DATABASE_URL
from app.utils import parse_amount

logger = logging.getLogger(__name__)


def _db_connect(retries: int = 5, delay: float = 1.5) -> psycopg2.extensions.connection:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            return psycopg2.connect(DATABASE_URL)
        except Exception as exc:
            last_err = exc
            logger.warning("DB nicht erreichbar (Versuch %d/%d): %s", attempt, retries, exc)
            time.sleep(delay)
    raise RuntimeError(f"Keine DB-Verbindung: {last_err}")


def db_get_or_create_tab(user_id: int, year: int, month: int) -> int:
    conn = _db_connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id FROM budget_tabs WHERE user_id=%s AND year=%s AND month=%s",
                (user_id, year, month),
            )
            row = cur.fetchone()
            if row:
                return row["id"]
            cur.execute(
                "INSERT INTO budget_tabs (user_id, year, month) VALUES (%s, %s, %s) RETURNING id",
                (user_id, year, month),
            )
            tab_id = cur.fetchone()["id"]
        conn.commit()
        return tab_id
    finally:
        conn.close()


def db_get_tab_info(tab_id: int) -> Dict:
    conn = _db_connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM budget_tabs WHERE id=%s", (tab_id,))
            row = cur.fetchone()
            return dict(row) if row else {}
    finally:
        conn.close()


def db_update_tab(tab_id: int, **kwargs: Any) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k}=%s" for k in kwargs)
    values = list(kwargs.values()) + [tab_id]
    conn = _db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE budget_tabs SET {fields} WHERE id=%s", values)
        conn.commit()
    finally:
        conn.close()


def db_get_user_months(user_id: int) -> List[Dict]:
    conn = _db_connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, year, month, locked FROM budget_tabs "
                "WHERE user_id=%s ORDER BY year DESC, month DESC",
                (user_id,),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def db_delete_tab(tab_id: int) -> None:
    conn = _db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM budget_tabs WHERE id=%s", (tab_id,))
        conn.commit()
    finally:
        conn.close()


def db_get_items(tab_id: int, table: str) -> List[Dict]:
    conn = _db_connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {table} WHERE tab_id=%s ORDER BY sort_order",
                (tab_id,),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def db_save_items(tab_id: int, table: str, items: List[Dict]) -> None:
    conn = _db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table} WHERE tab_id=%s", (tab_id,))
            for i, item in enumerate(items):
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                level = int(item.get("level", 0) or 0)
                if table == "surplus_items":
                    cur.execute(
                        f"""INSERT INTO {table}
                            (tab_id, sort_order, name, monthly_amount, strategy,
                             current_value, level, paid_override, paid_out)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (
                            tab_id, i, name,
                            parse_amount(item.get("monthly_amount", 0)),
                            str(item.get("strategy", "")),
                            parse_amount(item.get("current_value")) if item.get("current_value") not in (None, "", 0) else None,
                            level,
                            parse_amount(item.get("paid_override")) if item.get("paid_override") not in (None, "", 0) else None,
                            parse_amount(item.get("paid_out")) if item.get("paid_out") not in (None, "", 0) else None,
                        ),
                    )
                else:
                    cur.execute(
                        f"""INSERT INTO {table}
                            (tab_id, sort_order, name, amount, level)
                            VALUES (%s,%s,%s,%s,%s)""",
                        (tab_id, i, name, parse_amount(item.get("amount", 0)), level),
                    )
        conn.commit()
    finally:
        conn.close()


def calc_level0_total(items: List[Dict], field: str = "amount") -> float:
    return sum(
        parse_amount(i.get(field, 0))
        for i in items
        if i.get("name") and int(i.get("level", 0) or 0) == 0
    )
