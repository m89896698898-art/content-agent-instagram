from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from .. import keyboards, texts
from ..config import Config
from ..storage import log_lead

router = Router(name="booking")


class Booking(StatesGroup):
    name = State()
    contact = State()
    time = State()


@router.callback_query(F.data.startswith("booking:start:"))
async def start_booking(call: CallbackQuery, state: FSMContext, config: Config) -> None:
    source = call.data.split(":")[2]

    if config.booking_url:
        log_lead(
            config.data_dir,
            user_id=call.from_user.id,
            username=call.from_user.username or "",
            source=f"booking_link:{source}",
        )
        await call.message.answer(texts.BOOKING_INTRO_LINK, reply_markup=keyboards.booking_link(config.booking_url))
        await call.answer()
        return

    await state.set_state(Booking.name)
    await state.update_data(source=source)
    await call.message.answer(texts.BOOKING_ASK_NAME)
    await call.answer()


@router.message(Booking.name)
async def booking_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Booking.contact)
    await message.answer(texts.BOOKING_ASK_CONTACT)


@router.message(Booking.contact)
async def booking_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(contact=message.text)
    await state.set_state(Booking.time)
    await message.answer(texts.BOOKING_ASK_TIME)


@router.message(Booking.time)
async def booking_time(message: Message, state: FSMContext, bot: Bot, config: Config) -> None:
    data = await state.get_data()
    await state.clear()

    log_lead(
        config.data_dir,
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        source=f"booking:{data.get('source', '')}",
        name=data.get("name", ""),
        contact=data.get("contact", ""),
        note=f"preferred_time={message.text}",
    )

    if config.hasbulla_personal_url:
        await message.answer(texts.BOOKING_DONE, reply_markup=keyboards.personal_chat(config.hasbulla_personal_url))
    else:
        await message.answer(texts.BOOKING_DONE)

    for admin_id in config.admin_ids:
        await bot.send_message(
            admin_id,
            "🎥 Новая запись на разбор\n"
            f"Имя: {data.get('name', '')}\n"
            f"Контакт: {data.get('contact', '')}\n"
            f"Время: {message.text}\n"
            f"Telegram: @{message.from_user.username or message.from_user.id}",
        )
