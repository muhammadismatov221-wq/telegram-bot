from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


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