from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from .. import keyboards, texts
from ..config import Config
from ..storage import log_lead

router = Router(name="quiz")


class Quiz(StatesGroup):
    running = State()


# Каждый вопрос: текст + варианты (подпись, зона).
QUESTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "1. Вы точно знаете, сколько бизнес заработал чистыми в прошлом месяце "
        "(не выручка, а то, что осталось после всех расходов)?",
        [("Да, знаю точную цифру", ""), ("Примерно представляю", "finance"), ("Нет, не считал(а)", "finance")],
    ),
    (
        "2. Если вы на две недели выключитесь из продаж — они продолжатся "
        "на том же уровне?",
        [("Да, система работает без меня", ""), ("Просядут, но не остановятся", "sales"), ("Продажи почти остановятся", "sales")],
    ),
    (
        "3. Сотрудники принимают рабочие решения без вашего одобрения?",
        [("Да, регулярно", ""), ("Иногда, по мелочи", "team"), ("Нет, всё решаю я", "team")],
    ),
    (
        "4. Повторяющиеся задачи (найм, закупка, ответ клиенту) делаются "
        "каждый раз одинаково, по правилу, а не заново с нуля?",
        [("Да, есть чёткий порядок", ""), ("Частично", "process"), ("Каждый раз по-разному", "process")],
    ),
    (
        "5. Сколько дней в месяц бизнес может работать вообще без вашего "
        "личного участия?",
        [("10 и больше", ""), ("3–9 дней", "owner"), ("0–2 дня", "owner")],
    ),
]


@router.callback_query(F.data == "quiz:start")
async def start_quiz(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Quiz.running)
    await state.update_data(index=0, scores={})
    await call.message.edit_text(texts.QUIZ_INTRO)
    await ask_question(call, state)
    await call.answer()


async def ask_question(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    index = data["index"]
    question, options = QUESTIONS[index]
    await call.message.answer(question, reply_markup=keyboards.quiz_options(options))


@router.callback_query(Quiz.running, F.data.startswith("quiz:answer:"))
async def answer_quiz(call: CallbackQuery, state: FSMContext, config: Config) -> None:
    zone = call.data.split(":", 2)[2]
    data = await state.get_data()
    index = data["index"]
    scores = data["scores"]

    if zone:
        scores[zone] = scores.get(zone, 0) + 1

    index += 1
    if index >= len(QUESTIONS):
        await state.clear()
        weak_zone = max(scores, key=scores.get) if scores else "process"
        title, explanation = texts.ZONE_RESULT[weak_zone]

        log_lead(
            config.data_dir,
            user_id=call.from_user.id,
            username=call.from_user.username or "",
            source="quiz",
            note=f"weak_zone={weak_zone}",
        )

        result_text = (
            f"{texts.QUIZ_RESULT_HEADER}: <b>{title}</b>\n\n{explanation}"
            f"{texts.QUIZ_RESULT_CTA}"
        )
        await call.message.edit_text(result_text, reply_markup=keyboards.quiz_result_actions())
    else:
        await state.update_data(index=index, scores=scores)
        await call.message.delete()
        await ask_question(call, state)

    await call.answer()
