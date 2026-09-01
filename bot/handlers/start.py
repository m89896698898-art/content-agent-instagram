from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from .. import keyboards, texts
from ..config import Config
from ..storage import log_lead

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, config: Config) -> None:
    log_lead(
        config.data_dir,
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        source="start",
    )
    await message.answer(texts.WELCOME, reply_markup=keyboards.main_menu())


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery) -> None:
    await call.message.edit_text(texts.WELCOME, reply_markup=keyboards.main_menu())
    await call.answer()
