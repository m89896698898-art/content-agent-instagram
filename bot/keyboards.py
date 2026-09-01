from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import texts


def main_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🕐 «Дорогой час» — 990 ₽", callback_data="product:1")
    b.button(text="🧭 Бесплатная диагностика (3 мин)", callback_data="quiz:start")
    b.button(text="🎥 20-минутный разбор — бесплатно", callback_data="booking:start:free")
    b.button(text="📞 Личная диагностика — 14 900 ₽", callback_data="product:2")
    b.adjust(1)
    return b.as_markup()


def back_to_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ В меню", callback_data="menu")
    return b.as_markup()


def product1_card(price: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=f"Купить за {price} ₽", callback_data="pay:1")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def product2_card(price: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=f"Оплатить и записаться — {price} ₽", callback_data="pay:2")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def manual_payment_confirm(code: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=texts.MANUAL_PAYMENT_CONFIRM_BUTTON, callback_data=f"paid:{code}")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def quiz_options(options: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for label, value in options:
        b.button(text=label, callback_data=f"quiz:answer:{value}")
    b.adjust(1)
    return b.as_markup()


def quiz_result_actions() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🎥 Записаться на 20-минутный разбор", callback_data="booking:start:free")
    b.button(text="📞 Личная диагностика — 14 900 ₽", callback_data="product:2")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def booking_link(url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="Выбрать время", url=url))
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()
