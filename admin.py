from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

import database as db
import keyboards as kb
from config import ADMIN_ID, MINI_QUIZ_EVERY

router = Router()


def admin_only(call: CallbackQuery) -> bool:
    return call.from_user.id == ADMIN_ID


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