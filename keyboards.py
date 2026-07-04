from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def language_choice_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🇷🇺 Русӣ", callback_data="lang_ru")
    kb.button(text="🇬🇧 Англисӣ", callback_data="lang_en")
    kb.adjust(2)
    return kb.as_markup()


def admin_approve_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Тасдиқ", callback_data=f"approve_user_{user_id}")
    kb.button(text="❌ Рад", callback_data=f"reject_user_{user_id}")
    kb.adjust(2)
    return kb.as_markup()


def lesson_done_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Азёд кардам, давом", callback_data="lesson_done")
    kb.adjust(1)
    return kb.as_markup()


def admin_test_approve_kb(result_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Гузарад", callback_data=f"approve_test_{result_id}")
    kb.button(text="❌ Такрор кунад", callback_data=f"reject_test_{result_id}")
    kb.adjust(2)
    return kb.as_markup()


STATUS_EMOJI = {
    "pending": "⏳",
    "approved": "✅",
    "rejected": "❌",
    "blocked": "🚫",
}


def admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 Ҳамаи корбарон", callback_data="admin_users_0")
    kb.button(text="⏳ Дархостҳои интизорӣ", callback_data="admin_pending_0")
    kb.adjust(1)
    return kb.as_markup()


def users_list_kb(users: list, page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in users:
        emoji = STATUS_EMOJI.get(u["status"], "❔")
        label = f"{emoji} {u['full_name']} — дарси {u['current_lesson']}"
        kb.row(InlineKeyboardButton(text=label, callback_data=f"admin_user_{u['user_id']}"))

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}_{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}_{page + 1}"))
    if nav_buttons:
        kb.row(*nav_buttons)

    kb.row(InlineKeyboardButton(text="🔙 Ба меню", callback_data="admin_menu"))
    return kb.as_markup()


def user_detail_kb(user: dict, back_prefix: str = "admin_users_0") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    status = user["status"]
    uid = user["user_id"]

    if status == "pending":
        kb.button(text="✅ Иҷозат додан", callback_data=f"admin_approve_{uid}")
        kb.button(text="❌ Рад кардан", callback_data=f"admin_reject_{uid}")
    elif status == "approved":
        kb.button(text="🚫 Бастан", callback_data=f"admin_block_{uid}")
        kb.button(text="🔄 Иваз кардани забон", callback_data=f"admin_lang_{uid}")
    elif status in ("rejected", "blocked"):
        kb.button(text="✅ Иҷозат додан", callback_data=f"admin_approve_{uid}")

    kb.button(text="🔙 Ба рӯйхат", callback_data=back_prefix)
    kb.adjust(1)
    return kb.as_markup()


def admin_lang_choice_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🇷🇺 Русӣ", callback_data=f"admin_setlang_{user_id}_ru")
    kb.button(text="🇬🇧 Англисӣ", callback_data=f"admin_setlang_{user_id}_en")
    kb.button(text="🔙 Бекор", callback_data=f"admin_user_{user_id}")
    kb.adjust(2, 1)
    return kb.as_markup()