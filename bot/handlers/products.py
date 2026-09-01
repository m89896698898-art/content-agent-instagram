from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice

from .. import keyboards, texts
from ..catalog import build_catalog
from ..config import Config

router = Router(name="products")


@router.callback_query(F.data == "product:1")
async def show_product1(call: CallbackQuery, config: Config) -> None:
    await call.message.edit_text(
        texts.PRODUCT1_DESCRIPTION,
        reply_markup=keyboards.product1_card(config.product1_price_rub),
    )
    await call.answer()


@router.callback_query(F.data == "product:2")
async def show_product2(call: CallbackQuery, config: Config) -> None:
    await call.message.edit_text(
        texts.PRODUCT2_DESCRIPTION,
        reply_markup=keyboards.product2_card(config.product2_price_rub),
    )
    await call.answer()


@router.callback_query(F.data.startswith("pay:"))
async def start_payment(call: CallbackQuery, config: Config) -> None:
    code = call.data.split(":")[1]
    product = build_catalog(config)[code]

    if config.provider_token:
        await call.message.answer_invoice(
            title=product.title,
            description=f"{product.title} — оплата в боте Хасбуллы",
            payload=f"{code}:{call.from_user.id}",
            provider_token=config.provider_token,
            currency="RUB",
            prices=[LabeledPrice(label=product.title, amount=product.price_rub * 100)],
        )
    else:
        text = texts.MANUAL_PAYMENT_HEADER.format(title=product.title, price=product.price_rub)
        text += config.manual_payment_instructions
        await call.message.answer(text, reply_markup=keyboards.manual_payment_confirm(code))

    await call.answer()
