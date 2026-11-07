from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_toolbar():
    # सिर्फ एक Help बटन
    kb = [
        [KeyboardButton(text="ℹ️ Help")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)
