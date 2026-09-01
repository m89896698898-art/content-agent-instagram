"""Выдача продукта после оплаты — общая логика для авто- и ручного подтверждения."""
from __future__ import annotations

import os

from aiogram import Bot
from aiogram.types import FSInputFile

from . import keyboards, texts
from .config import Config


async def deliver_product(bot: Bot, config: Config, user_id: int, code: str) -> None:
    if code == "1":
        await bot.send_message(user_id, texts.PRODUCT1_DELIVERY_INTRO)
        path = config.product1_content_path
        if path and os.path.exists(path):
            await bot.send_document(user_id, FSInputFile(path))
        else:
            await bot.send_message(user_id, texts.PRODUCT1_DELIVERY_FALLBACK)
        return

    if code == "2":
        if config.booking_url:
            await bot.send_message(
                user_id,
                texts.PRODUCT2_AFTER_PAYMENT,
                reply_markup=keyboards.booking_link(config.booking_url),
            )
        else:
            from .keyboards import InlineKeyboardBuilder  # local import, avoid cycle

            b = InlineKeyboardBuilder()
            b.button(text="🎥 Записаться на созвон", callback_data="booking:start:paid")
            await bot.send_message(user_id, texts.PRODUCT2_AFTER_PAYMENT, reply_markup=b.as_markup())
