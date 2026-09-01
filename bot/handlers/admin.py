from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..catalog import build_catalog
from ..config import Config
from ..fulfillment import deliver_product
from ..storage import log_order

router = Router(name="admin")


@router.message(Command("confirm"))
async def confirm_payment(message: Message, bot: Bot, config: Config) -> None:
    if message.from_user.id not in config.admin_ids:
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Формат: /confirm <user_id> <код продукта: 1 или 2>")
        return

    _, user_id_raw, code = parts
    catalog = build_catalog(config)
    if code not in catalog or not user_id_raw.isdigit():
        await message.answer("Не понял команду. Формат: /confirm <user_id> <1|2>")
        return

    user_id = int(user_id_raw)
    product = catalog[code]

    log_order(
        config.data_dir,
        user_id=user_id,
        username="",
        product_code=code,
        product_title=product.title,
        price=product.price_rub,
        status="confirmed_by_admin",
    )
    await deliver_product(bot, config, user_id, code)
    await message.answer(f"Готово: {product.title} выдан пользователю {user_id}.")
