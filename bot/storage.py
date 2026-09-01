"""Простое хранение лидов и заказов в CSV — без внешней БД."""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone

_LEADS_FIELDS = ["timestamp", "user_id", "username", "source", "name", "contact", "note"]
_ORDERS_FIELDS = ["timestamp", "user_id", "username", "product_code", "product_title", "price", "status"]


def _path(data_dir: str, filename: str) -> str:
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, filename)


def _append(path: str, fields: list[str], row: dict) -> None:
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def log_lead(data_dir: str, *, user_id: int, username: str, source: str,
             name: str = "", contact: str = "", note: str = "") -> None:
    _append(_path(data_dir, "bot_leads.csv"), _LEADS_FIELDS, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "username": username,
        "source": source,
        "name": name,
        "contact": contact,
        "note": note,
    })


def log_order(data_dir: str, *, user_id: int, username: str, product_code: str,
              product_title: str, price: int, status: str) -> None:
    _append(_path(data_dir, "bot_orders.csv"), _ORDERS_FIELDS, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "username": username,
        "product_code": product_code,
        "product_title": product_title,
        "price": price,
        "status": status,
    })
