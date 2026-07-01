import json
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import database as db
import groq_service as gs
import keyboards as kb
from config import ADMIN_ID, MINI_QUIZ_EVERY, BIG_TEST_EVERY, TOTAL_LESSONS

router = Router()

user_quiz_state = {}


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user = db.get_user(message.from_user.id)
    if user is None:
        db.add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
        user = db.get_user(message.from_user.id)
        await notify_admin_new_user(bot, message.from_user.id, message.from_user.full_name, message.from_user.username)
        await message.answer("Дархости ту фиристода шуд. Мунтазири тасдиқи админ бош ⏳")
        return

    if user["status"] == "approved":
        await message.answer("Салом дубора! Барои давом додан /lesson-ро пахш кун ё бинавис 'дарс'.")
        return

    if user["status"] == "pending":
        await message.answer("Дархости ту фиристода шуд. Мунтазири тасдиқи админ бош ⏳")
        return

    if user["status"] == "rejected":
        await message.answer("Дархости ту рад шуда буд. Бо админ тамос гир.")
        return


@router.message(F.text.lower() == "дарс")
async def text_lesson(message: Message, bot: Bot):
    await send_next_lesson_or_test(message.from_user.id, bot)


async def notify_admin_new_user(bot: Bot, user_id: int, full_name: str, username: str):
    text = f"👤 Корбари нав:\n{full_name} (@{username})\nID: {user_id}\n\nБа хондани дарсҳо иҷозат медиҳӣ?"
    await bot.send_message(ADMIN_ID, text, reply_markup=kb.admin_approve_kb(user_id))


@router.callback_query(F.data == "lang_ru")
@router.callback_query(F.data == "lang_en")
async def choose_language(call: CallbackQuery, bot: Bot):
    lang = "ru" if call.data == "lang_ru" else "en"
    db.set_language(call.from_user.id, lang)
    await call.message.edit_text(f"Забон интихоб шуд: {'Русӣ' if lang=='ru' else 'Англисӣ'} ✅")
    await send_next_lesson_or_test(call.from_user.id, bot)


async def send_next_lesson_or_test(user_id: int, bot: Bot):
    user = db.get_user(user_id)
    if not user or user["status"] != "approved":
        await bot.send_message(user_id, "Ту ҳанӯз тасдиқ нашудаӣ.")
        return

    current = user["current_lesson"]
    next_lesson = current + 1

    if current >= TOTAL_LESSONS:
        await bot.send_message(user_id, "🎉 Ту ҳамаи 600 дарсро ба итмом расондӣ!")
        return

    if user["awaiting"] in ("mini_quiz", "big_test"):
        await bot.send_message(user_id, "Натиҷаи тести охирини ту ҳанӯз аз ҷониби админ тасдиқ нашудааст ⏳")
        return

    await send_lesson(user_id, next_lesson, user["language"], bot)


async def send_lesson(user_id: int, lesson_number: int, language: str, bot: Bot):
    cached = db.get_cached_lesson(lesson_number, language)
    if cached:
        content = json.loads(cached)
    else:
        content = gs.generate_lesson(lesson_number, language)
        db.save_lesson(lesson_number, language, json.dumps(content))

    text = f"📘 Дарси {lesson_number}\n\n"
    for i, w in enumerate(content["words"], 1):
        text += f"{i}. {w['word']} — {w['translation']}\n   _{w['example']}_\n   ({w['example_translation']})\n\n"

    db.set_current_lesson(user_id, lesson_number)
    await bot.send_message(user_id, text, reply_markup=kb.lesson_done_kb(), parse_mode="Markdown")


@router.callback_query(F.data == "lesson_done")
async def lesson_done(call: CallbackQuery, bot: Bot):
    user = db.get_user(call.from_user.id)
    lesson_number = user["current_lesson"]
    await call.message.edit_reply_markup(reply_markup=None)

    if lesson_number % BIG_TEST_EVERY == 0:
        await start_test(call.from_user.id, "big", 1, lesson_number, bot)
    elif lesson_number % MINI_QUIZ_EVERY == 0:
        start_range = lesson_number - MINI_QUIZ_EVERY + 1
        await start_test(call.from_user.id, "mini", start_range, lesson_number, bot)
    else:
        await send_lesson(call.from_user.id, lesson_number + 1, user["language"], bot)


async def start_test(user_id: int, test_type: str, start: int, end: int, bot: Bot):
    user = db.get_user(user_id)
    language = user["language"]
    quiz_key = f"{test_type}_{start}-{end}_{language}"

    cached = db.get_cached_quiz(quiz_key)
    if cached:
        quiz = json.loads(cached)
    else:
        all_words = []
        for ln in range(start, end + 1):
            lc = db.get_cached_lesson(ln, language)
            if lc:
                all_words.extend(json.loads(lc)["words"])
        quiz = gs.generate_quiz(all_words, test_type)
        db.save_quiz(quiz_key, json.dumps(quiz))

    db.set_awaiting(user_id, "big_test" if test_type == "big" else "mini_quiz")
    user_quiz_state[user_id] = {
        "questions": quiz["questions"],
        "current": 0,
        "score": 0,
        "test_type": test_type,
        "range": f"{start}-{end}",
    }
    label = "тести КАЛОН 🔥" if test_type == "big" else "тести хурд"
    await bot.send_message(user_id, f"Вақти {label} расид! Дарсҳои {start}-{end}.")
    await send_question(user_id, bot)


async def send_question(user_id: int, bot: Bot):
    state = user_quiz_state[user_id]
    idx = state["current"]
    q = state["questions"][idx]

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(q["options"]):
        builder.button(text=opt, callback_data=f"ans_{i}")
    builder.adjust(1)

    await bot.send_message(
        user_id,
        f"Савол {idx + 1}/{len(state['questions'])}:\n{q['question']}",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("ans_"))
async def answer_question(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    state = user_quiz_state.get(user_id)
    if not state:
        return

    chosen = int(call.data.split("_")[1])
    idx = state["current"]
    correct = state["questions"][idx]["correct_index"]
    if chosen == correct:
        state["score"] += 1

    await call.message.edit_reply_markup(reply_markup=None)
    state["current"] += 1

    if state["current"] < len(state["questions"]):
        await send_question(user_id, bot)
    else:
        await finish_test(user_id, bot)


async def finish_test(user_id: int, bot: Bot):
    state = user_quiz_state.pop(user_id)
    score = state["score"]
    total = len(state["questions"])
    result_id = db.add_test_result(user_id, state["test_type"], state["range"], score, total)

    user = db.get_user(user_id)
    await bot.send_message(user_id, f"✅ Тест анҷом ёфт: {score}/{total}\nНатиҷа ба админ фиристода шуд, мунтазир бош ⏳")

    label = "🔥 ТЕСТИ КАЛОН" if state["test_type"] == "big" else "Тести хурд"
    text = (
        f"{label}\nКорбар: {user['full_name']} (ID: {user_id})\n"
        f"Дарсҳо: {state['range']}\nНатиҷа: {score}/{total}"
    )
    await bot.send_message(ADMIN_ID, text, reply_markup=kb.admin_test_approve_kb(result_id))