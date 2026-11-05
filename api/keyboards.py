from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from .config import ADMIN_ID

def main_toolbar(user_id):
    kb = [
        [KeyboardButton(text="🔍 Search Vehicle"), KeyboardButton(text="💳 My Wallet")],
        [KeyboardButton(text="➕ Add Credits"), KeyboardButton(text="ℹ️ Help & Support")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="👑 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)

def recharge_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Credit Packages", callback_data="cat_credits")],
        [InlineKeyboardButton(text="♾️ Unlimited Search Plans", callback_data="cat_unlimited")]
    ])

def credit_plans():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Starter Pack - 10 Credits (₹40)", callback_data="buy_10_40")],
        [InlineKeyboardButton(text="🔥 Pro Driver - 30 Credits (₹110)", callback_data="buy_30_110")],
        [InlineKeyboardButton(text="⚡ Power User - 75 Credits (₹250)", callback_data="buy_75_250")],
        [InlineKeyboardButton(text="👑 Fleet Owner - 200 Credits (₹600)", callback_data="buy_200_600")],
        [InlineKeyboardButton(text="💎 Enterprise - 500 Credits (₹1400)", callback_data="buy_500_1400")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_recharge")]
    ])

def unlimited_plans():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ 1 DAY UNLIMITED", callback_data="unlim_1")],
        [InlineKeyboardButton(text="🔥 5 DAYS UNLIMITED", callback_data="unlim_5")],
        [InlineKeyboardButton(text="🚀 15 DAYS UNLIMITED", callback_data="unlim_15")],
        [InlineKeyboardButton(text="👑 30 DAYS UNLIMITED", callback_data="unlim_30")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_recharge")]
    ])

def admin_dashboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Users Management", callback_data="admin_users")],
        [InlineKeyboardButton(text="💳 Add/Remove Credits", callback_data="admin_credits")],
        [InlineKeyboardButton(text="💸 Pending Payments", callback_data="admin_payments")],
        [InlineKeyboardButton(text="♾️ Unlimited Subscriptions", callback_data="admin_subs")]
    ])
