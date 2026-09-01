from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from .. import texts
from ..catalog import build_catalog
from ..config import Config
from ..fulfillment import deliver_product
from ..storage import log_order

router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot, config: Config) -> None:
    payload = message.successful_payment.invoice_payload
    code, _, _ = payload.partition(":")
    product = build_catalog(config)[code]

    log_order(
        config.data_dir,
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        product_code=code,
        product_title=product.title,
        price=product.price_rub,
        status="paid",
    )
    await deliver_product(bot, config, message.from_user.id, code)

    for admin_id in config.admin_ids:
        await bot.send_message(
            admin_id,
            f"💰 Оплата прошла: {product.title} — {product.price_rub} ₽\n"
            f"От: @{message.from_user.username or message.from_user.id}",
        )


@router.callback_query(F.data.startswith("paid:"))
async def manual_paid_click(call: CallbackQuery, bot: Bot, config: Config) -> None:
    code = call.data.split(":")[1]
    product = build_catalog(config)[code]
    user = call.from_user

    log_order(
        config.data_dir,
        user_id=user.id,
        username=user.username or "",
        product_code=code,
        product_title=product.title,
        price=product.price_rub,
        status="pending_confirmation",
    )

    await call.message.edit_text(texts.MANUAL_PAYMENT_PENDING)
    await call.answer()

    for admin_id in config.admin_ids:
        await bot.send_message(
            admin_id,
            texts.MANUAL_PAYMENT_ADMIN_ALERT.format(
                title=product.title,
                price=product.price_rub,
                user=f"@{user.username}" if user.username else user.full_name,
                user_id=user.id,
                code=code,
            ),
        )
