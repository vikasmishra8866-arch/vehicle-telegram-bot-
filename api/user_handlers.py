from aiogram import Router, types
from aiogram.filters import Command
import aiohttp
import re
from .database import get_or_create_user, check_cooldown, deduct_credit, log_search, get_active_subscription
from .config import VEHICLE_API_KEY, ADMIN_ID
from .keyboards import main_toolbar, recharge_menu
from .utils import format_vehicle_tree

router = Router()

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    bal = user.get("wallet_balance", 0) if user else 0
    text = f"🚗 <b>Vehicle Lookup Bot</b>\n\n👋 Welcome {message.from_user.first_name}!\n💳 Wallet Balance: <b>{bal} Credits</b>\n\nVehicle number bhejein.\nExample: <code>GJ05HG7801</code>"
    await message.answer(text, parse_mode="HTML", reply_markup=main_toolbar(message.from_user.id))

@router.message(lambda msg: msg.text == "💳 My Wallet")
async def btn_wallet(message: types.Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    sub = get_active_subscription(message.from_user.id)
    sub_text = f"\n♾️ Unlimited Plan Active till: {sub['expiry_date'][:10]}" if sub else ""
    await message.answer(f"👛 <b>YOUR WALLET</b>\n\n💳 Credits: <b>{user.get('wallet_balance', 0)}</b>{sub_text}", parse_mode="HTML")

@router.message(lambda msg: msg.text == "➕ Add Credits")
async def btn_add_credits(message: types.Message):
    await message.answer("🛒 <b>RECHARGE MENU</b>\n\nKripya category chunein:", reply_markup=recharge_menu(), parse_mode="HTML")

@router.message(lambda msg: msg.text == "ℹ️ Help & Support")
async def btn_help(message: types.Message):
    await message.answer("📖 <b>HELP</b>\n\nSirf registration number bhejein. Support ke liye admin se contact karein: @Rizx_x", parse_mode="HTML")

@router.message(lambda msg: re.match(r"^[A-Za-z0-9\s-]{6,15}$", msg.text or ""))
async def search_vehicle(message: types.Message):
    user_id = message.from_user.id
    reg_no = re.sub(r'[^a-zA-Z0-9]', '', message.text).upper()
    
    user = get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)
    if not check_cooldown(user_id):
        await message.reply("⏳ Please wait 5 seconds.")
        return

    is_admin = (user_id == ADMIN_ID)
    active_sub = get_active_subscription(user_id)
    
    if not is_admin and not active_sub and user.get("wallet_balance", 0) <= 0:
        await message.reply("❌ Aapke paas credits nahi hain. Kripya Recharge karein.")
        return

    msg = await message.reply("🔍 Fetching...\n<i>(8-17 seconds)</i>", parse_mode="HTML")
    url = f"https://hideme.eu.org/lookup?api=mvahan&key={VEHICLE_API_KEY}&number={reg_no}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=25) as response:
                data = await response.json()
    except:
        await msg.edit_text("⏱️ API Timeout. Try again.")
        return

    if not data or not data.get("success") or "vehicle" not in data:
        await msg.edit_text("❌ Vehicle not found.")
        log_search(user_id, reg_no, "not_found", 0)
        return

    v = data["vehicle"]
    credit_msg = ""
    
    if not is_admin and not active_sub:
        if data.get("mobile_found", False):
            if deduct_credit(user_id):
                credit_msg = "\n\n<i>(1 Credit deducted)</i>"
                log_search(user_id, reg_no, "success", 1)
        else:
            credit_msg = "\n\n⚠️ <i>Mobile not found. No credits deducted.</i>"
            log_search(user_id, reg_no, "mobile_not_found", 0)
    else:
        log_search(user_id, reg_no, "success_admin", 0)

    await msg.edit_text(format_vehicle_tree(reg_no, v, data) + credit_msg, parse_mode="HTML")
