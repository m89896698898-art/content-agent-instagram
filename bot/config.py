"""Загрузка конфигурации бота из переменных окружения."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _split_ids(raw: str) -> list[int]:
    return [int(x) for x in raw.replace(" ", "").split(",") if x]


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: list[int]

    # Приём платежей через встроенные Telegram Payments (YooKassa и т.п.).
    # Если не задан — бот переходит на ручной режим оплаты (см. ниже).
    provider_token: str

    # Ручной режим: реквизиты/ссылка на оплату и подтверждение админом.
    manual_payment_instructions: str

    # Zoom / Calendly ссылка для мгновенной самозаписи на 20-минутный разбор.
    # Если не задана — бот собирает контакт и удобное время, передаёт админу.
    booking_url: str

    product1_price_rub: int
    product2_price_rub: int

    product1_content_path: str

    channel_url: str
    instagram_url: str

    data_dir: str = field(default="data")


def load_config() -> Config:
    return Config(
        bot_token=os.environ["BOT_TOKEN"],
        admin_ids=_split_ids(os.environ.get("ADMIN_IDS", "")),
        provider_token=os.environ.get("PROVIDER_TOKEN", ""),
        manual_payment_instructions=os.environ.get(
            "MANUAL_PAYMENT_INSTRUCTIONS",
            "Переведите сумму по реквизитам, которые пришлёт Хасбулла, "
            "и отправьте сюда скриншот чека.",
        ),
        booking_url=os.environ.get("BOOKING_URL", ""),
        product1_price_rub=int(os.environ.get("PRODUCT1_PRICE_RUB", "990")),
        product2_price_rub=int(os.environ.get("PRODUCT2_PRICE_RUB", "14900")),
        product1_content_path=os.environ.get("PRODUCT1_CONTENT_PATH", ""),
        channel_url=os.environ.get("CHANNEL_URL", ""),
        instagram_url=os.environ.get("INSTAGRAM_URL", "https://instagram.com/hasbulla_gubdenskiy"),
    )
