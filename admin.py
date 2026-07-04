from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from config import ADMIN_ID, MINI_QUIZ_EVERY, USERS_PAGE_SIZE

router = Router()

STATUS_LABEL = {
    "pending": "⏳ Интизорӣ",
    "approved": "✅ Иҷозатдор",
    "rejected": "❌ Рад шуда",
    "blocked": "🚫 Баста шуда",
}
LANG_LABEL = {"ru": "Русӣ", "en": "Англисӣ"}


def admin_only(call: CallbackQuery) -> bool:
    return call.from_user.id == ADMIN_ID


def format_user_card(user: dict) -> str:
    status = STATUS_LABEL.get(user["status"], user["status"])
    lang = LANG_LABEL.get(user["language"], user["language"])
    username = f"@{user['username']}" if user["username"] else "—"
    return (
        f"👤 {user['full_name']} ({username})\n"
        f"ID: {user['user_id']}\n"
        f"Ҳолат: {status}\n"
        f"Забон: {lang}\n"
        f"Дарси ҷорӣ: {user['current_lesson']}"
    )


@router.callback_query(F.data.startswith("approve_user_"))
async def approve_user(call: CallbackQuery, bot: Bot):
    if not admin_only(call):
        return
    user_id = int(call.data.split("_")[-1])
    db.set_status(user_id, "approved")
    await call.message.edit_text(call.message.text + "\n\n✅ Тасдиқ шуд")
    await bot.send_message(
        user_id,
        "🎉 Ту тасдиқ шудӣ! Аввал забони омӯхтаниро интихоб кун:",
        reply_markup=kb.language_choice_kb(),
    )


@router.callback_query(F.data.startswith("reject_user_"))
async def reject_user(call: CallbackQuery, bot: Bot):
    if not admin_only(call):
        return
    user_id = int(call.data.split("_")[-1])
    db.set_status(user_id, "rejected")
    await call.message.edit_text(call.message.text + "\n\n❌ Рад шуд")
    await bot.send_message(user_id, "Дархости ту рад шуд.")


@router.callback_query(F.data.startswith("approve_test_"))
async def approve_test(call: CallbackQuery, bot: Bot):
    if not admin_only(call):
        return
    result_id = int(call.data.split("_")[-1])
    result = db.get_test_result(result_id)
    db.set_test_status(result_id, "approved")
    db.set_awaiting(result["user_id"], None)

    await call.message.edit_text(call.message.text + "\n\n✅ ТАСДИҶ - дарси нав кушода шуд")
    await bot.send_message(result["user_id"], "✅ Админ тасдиқ кард! Барои дарси нав бинавис 'дарс'.")


@router.callback_query(F.data.startswith("reject_test_"))
async def reject_test(call: CallbackQuery, bot: Bot):
    if not admin_only(call):
        return
    result_id = int(call.data.split("_")[-1])
    result = db.get_test_result(result_id)
    db.set_test_status(result_id, "rejected")

    user = db.get_user(result["user_id"])
    if result["test_type"] == "mini":
        start = int(result["lesson_range"].split("-")[0])
        db.set_current_lesson(result["user_id"], start - 1)

    db.set_awaiting(result["user_id"], None)
    await call.message.edit_text(call.message.text + "\n\n❌ РАД - дарс такрор мешавад")
    await bot.send_message(result["user_id"], "❌ Админ гуфт такрор кун. Бинавис 'дарс' барои давом.")


# ---------------------- Панели админ ----------------------

@router.message(Command("admin"))
async def admin_panel_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 Панели админ", reply_markup=kb.admin_menu_kb())


@router.callback_query(F.data == "admin_menu")
async def admin_menu_cb(call: CallbackQuery):
    if not admin_only(call):
        return
    await call.message.edit_text("🛠 Панели админ", reply_markup=kb.admin_menu_kb())


async def render_users_page(call: CallbackQuery, users: list, page: int, prefix: str, title: str):
    total_pages = max(1, (len(users) + USERS_PAGE_SIZE - 1) // USERS_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    chunk = users[page * USERS_PAGE_SIZE: (page + 1) * USERS_PAGE_SIZE]

    if users:
        text = f"{title} ({len(users)})\nСаҳифа {page + 1}/{total_pages}"
    else:
        text = f"{title}\n\nКорбар нест."

    await call.message.edit_text(text, reply_markup=kb.users_list_kb(chunk, page, total_pages, prefix))


@router.callback_query(F.data.startswith("admin_users_"))
async def admin_users_list(call: CallbackQuery):
    if not admin_only(call):
        return
    page = int(call.data.split("_")[-1])
    users = db.get_all_users()
    await render_users_page(call, users, page, "admin_users", "👥 Ҳамаи корбарон")


@router.callback_query(F.data.startswith("admin_pending_"))
async def admin_pending_list(call: CallbackQuery):
    if not admin_only(call):
        return
    page = int(call.data.split("_")[-1])
    users = [u for u in db.get_all_users() if u["status"] == "pending"]
    await render_users_page(call, users, page, "admin_pending", "⏳ Дархостҳои интизорӣ")


@router.callback_query(F.data.startswith("admin_user_"))
async def admin_user_detail(call: CallbackQuery):
    if not admin_only(call):
        return
    user_id = int(call.data.split("_")[-1])
    user = db.get_user(user_id)
    if not user:
        await call.answer("Корбар ёфт нашуд", show_alert=True)
        return
    await call.message.edit_text(format_user_card(user), reply_markup=kb.user_detail_kb(user))


@router.callback_query(F.data.startswith("admin_approve_"))
async def admin_panel_approve(call: CallbackQuery, bot: Bot):
    if not admin_only(call):
        return
    user_id = int(call.data.split("_")[-1])
    user = db.get_user(user_id)
    if not user:
        await call.answer("Корбар ёфт нашуд", show_alert=True)
        return

    db.set_status(user_id, "approved")

    if not user["lang_selected"]:
        await bot.send_message(
            user_id,
            "🎉 Ту тасдиқ шудӣ! Аввал забони омӯхтаниро интихоб кун:",
            reply_markup=kb.language_choice_kb(),
        )
    else:
        await bot.send_message(user_id, "✅ Ба ту дубора иҷозат дода шуд! Барои давом бинавис 'дарс'.")

    await call.answer("Тасдиқ шуд ✅")
    user = db.get_user(user_id)
    await call.message.edit_text(format_user_card(user), reply_markup=kb.user_detail_kb(user))


@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_panel_reject(call: CallbackQuery, bot: Bot):
    if not admin_only(call):
        return
    user_id = int(call.data.split("_")[-1])
    user = db.get_user(user_id)
    if not user:
        await call.answer("Корбар ёфт нашуд", show_alert=True)
        return

    db.set_status(user_id, "rejected")
    await bot.send_message(user_id, "❌ Дархости ту рад шуд.")
    await call.answer("Рад шуд")
    user = db.get_user(user_id)
    await call.message.edit_text(format_user_card(user), reply_markup=kb.user_detail_kb(user))


@router.callback_query(F.data.startswith("admin_block_"))
async def admin_panel_block(call: CallbackQuery, bot: Bot):
    if not admin_only(call):
        return
    user_id = int(call.data.split("_")[-1])
    user = db.get_user(user_id)
    if not user:
        await call.answer("Корбар ёфт нашуд", show_alert=True)
        return

    db.set_status(user_id, "blocked")
    await bot.send_message(user_id, "🚫 Дастрасии ту муваққатан баста шуд. Бо админ тамос гир.")
    await call.answer("Баста шуд 🚫")
    user = db.get_user(user_id)
    await call.message.edit_text(format_user_card(user), reply_markup=kb.user_detail_kb(user))


@router.callback_query(F.data.startswith("admin_lang_"))
async def admin_lang_menu(call: CallbackQuery):
    if not admin_only(call):
        return
    user_id = int(call.data.split("_")[-1])
    user = db.get_user(user_id)
    if not user:
        await call.answer("Корбар ёфт нашуд", show_alert=True)
        return
    await call.message.edit_text(
        f"{format_user_card(user)}\n\nЗабони навро интихоб кун:",
        reply_markup=kb.admin_lang_choice_kb(user_id),
    )


@router.callback_query(F.data.startswith("admin_setlang_"))
async def admin_set_lang(call: CallbackQuery, bot: Bot):
    if not admin_only(call):
        return
    parts = call.data.split("_")  # admin_setlang_{user_id}_{lang}
    user_id = int(parts[2])
    lang = parts[3]

    user = db.get_user(user_id)
    if not user:
        await call.answer("Корбар ёфт нашуд", show_alert=True)
        return

    db.set_language(user_id, lang)
    await bot.send_message(user_id, f"ℹ️ Админ забони туро иваз кард: {LANG_LABEL[lang]}")
    await call.answer("Забон иваз шуд ✅")

    user = db.get_user(user_id)
    await call.message.edit_text(format_user_card(user), reply_markup=kb.user_detail_kb(user))