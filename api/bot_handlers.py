from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import re

from .database import (
    get_or_create_user, check_cooldown, deduct_credit, 
    log_search, add_credits_admin, get_user_info
)
from .config import VEHICLE_API_KEY, ADMIN_ID

router = Router()

# ---------------- BASIC COMMANDS ----------------

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    bal = user.get("wallet_balance", 0) if user else 0
    
    text = (
        f"🚗 <b>Vehicle Lookup Bot</b>\n\n"
        f"👋 Welcome {message.from_user.first_name}!\n"
        f"💳 Wallet Balance: <b>{bal} Credits</b>\n\n"
        f"Kisi bhi vehicle ka registration number bhejein.\n"
        f"Example: <code>GJ05HG7801</code>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("balance"))
async def check_balance(message: types.Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if user:
        await message.answer(f"💳 Aapka Wallet Balance: <b>{user.get('wallet_balance', 0)} Credits</b>", parse_mode="HTML")

@router.message(Command("addcredits"))
async def show_plans(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Starter Pack - 10 Credits (₹40)", callback_data="buy_10")],
        [InlineKeyboardButton(text="🔥 Pro Driver - 30 Credits (₹110)", callback_data="buy_30")],
        [InlineKeyboardButton(text="⚡ Power User - 75 Credits (₹250)", callback_data="buy_75")],
        [InlineKeyboardButton(text="👑 Fleet Owner - 200 Credits (₹600)", callback_data="buy_200")],
        [InlineKeyboardButton(text="💎 Enterprise Mega - 500 Credits (₹1400)", callback_data="buy_500")]
    ])
    await message.answer("💰 <b>Kripya apna plan chunein:</b>", reply_markup=kb, parse_mode="HTML")

# ---------------- ADMIN COMMANDS ----------------

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Aap admin nahi hain.")
        return
    
    text = (
        "👑 <b>ADMIN CONTROL PANEL</b>\n\n"
        "Available Commands:\n"
        "👉 /addcredit [User_ID] [Amount] - Credits add karne ke liye\n"
        "👉 /userinfo [User_ID] - User ki details dekhne ke liye"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("addcredit"))
async def add_credit_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.reply("❌ Format: /addcredit [User_ID] [Amount]")
            return
            
        target_id = int(args[1])
        amount = int(args[2])
        
        success, new_bal = add_credits_admin(target_id, amount)
        
        if success:
            await message.reply(f"✅ Successfully {amount} credits added to {target_id}.\nNew Balance: {new_bal}")
            try:
                await message.bot.send_message(target_id, f"🎉 Aapke wallet me {amount} credits add kiye gaye hain!\n💳 New Balance: {new_bal} Credits")
            except:
                pass
        else:
            await message.reply("❌ User not found in database.")
            
    except ValueError:
        await message.reply("❌ Invalid ID or Amount. Numbers daalein.")

@router.message(Command("userinfo"))
async def user_info_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.reply("❌ Format: /userinfo [User_ID]")
            return
            
        target_id = int(args[1])
        user = get_user_info(target_id)
        
        if user:
            text = (
                f"👤 <b>USER INFO</b>\n"
                f"🆔 ID: <code>{user['telegram_id']}</code>\n"
                f"📛 Name: {user.get('first_name', 'N/A')}\n"
                f"🔗 Username: @{user.get('username', 'N/A')}\n"
                f"💳 Balance: {user.get('wallet_balance', 0)} Credits"
            )
            await message.reply(text, parse_mode="HTML")
        else:
            await message.reply("❌ User not found.")
    except ValueError:
        await message.reply("❌ Invalid ID.")

# ---------------- VEHICLE SEARCH (MAIN LOGIC) ----------------

@router.message(lambda msg: re.match(r"^[A-Za-z0-9\s-]{6,15}$", msg.text or ""))
async def search_vehicle(message: types.Message):
    user_id = message.from_user.id
    raw_text = message.text.strip()
    reg_no = re.sub(r'[^a-zA-Z0-9]', '', raw_text).upper()
    
    user = get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)
    if not user:
        await message.reply("❌ Database error. Please try again later.")
        return

    # 1. Cooldown Check
    if not check_cooldown(user_id):
        await message.reply("⏳ Please wait 5 seconds before searching another vehicle.")
        return

    # 2. Wallet Check & Admin Bypass
    is_admin = (user_id == ADMIN_ID)
    if not is_admin and user.get("wallet_balance", 0) <= 0:
        await message.reply("❌ Aapke paas credits nahi hain. Kripya /addcredits se recharge karein.")
        return

    msg = await message.reply("🔍 Fetching vehicle details...\n<i>(ye 8-17 second le sakta hai)</i>", parse_mode="HTML")

    # 3. API Call
    url = f"https://hideme.eu.org/lookup?api=mvahan&key={VEHICLE_API_KEY}&number={reg_no}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=25) as response:
                data = await response.json()
    except Exception as e:
        await msg.edit_text("⏱️ API Timeout. Thodi der baad try karein.")
        return

    if not data or not data.get("success") or "vehicle" not in data:
        await msg.edit_text("❌ Vehicle not found. Number check karke dobara try karein.")
        log_search(user_id, reg_no, "not_found", 0)
        return

    v = data["vehicle"]
    mobile_found = data.get("mobile_found", False)
    credit_msg = ""
    
    # 4. Credit Deduction Logic (Only if not admin)
    if not is_admin:
        if mobile_found:
            if deduct_credit(user_id):
                credit_msg = "\n\n<i>(1 Credit deducted)</i>"
                log_search(user_id, reg_no, "success", 1)
        else:
            credit_msg = "\n\n⚠️ <i>Owner contact not found. No credits deducted.</i>"
            log_search(user_id, reg_no, "mobile_not_found", 0)
    else:
        log_search(user_id, reg_no, "success_admin", 0)

    # 5. Format Output
    formatted_text = format_vehicle_tree(reg_no, v, data) + credit_msg
    await msg.edit_text(formatted_text, parse_mode="HTML")

# ---------------- FORMATTER ----------------

def format_vehicle_tree(reg_no, v, data):
    def valid(val):
        if val is None or str(val).strip().lower() in ["", "null", "na", "none", "0"]: return False
        return True

    text = f"🧭 <b>VEHICLE JOURNEY</b> — {reg_no}\n"
    text += "────────────────────────────────────────────\n│\n"

    text += "├─ 🚘 <b>VEHICLE IDENTITY</b>\n"
    if valid(v.get("make")): text += f"│   ├─ Make      : {v.get('make')}\n"
    if valid(v.get("variant")): text += f"│   ├─ Variant   : {v.get('variant')}\n"
    if valid(v.get("fuel")): text += f"│   ├─ Fuel      : {v.get('fuel')}\n"
    if valid(v.get("color")): text += f"│   ├─ Color     : {v.get('color')}\n"
    if valid(v.get("body_type")): text += f"│   ├─ Body Type : {v.get('body_type')}\n"
    if valid(v.get("vehicle_class")): text += f"│   └─ Class     : {v.get('vehicle_class')}\n│\n"

    text += "├─ 👤 <b>OWNER DETAILS</b>\n"
    if valid(v.get("owner")): text += f"│   ├─ Owner     : {v.get('owner')}\n"
    if valid(data.get("mobile")): text += f"│   ├─ Mobile    : {data.get('mobile')}\n"
    text += f"│   └─ Found     : {'Yes' if data.get('mobile_found') else 'No'}\n│\n"

    text += "├─ 🔑 <b>MACHINE DETAILS</b>\n"
    if valid(v.get("chassis")): text += f"│   ├─ Chassis   : {v.get('chassis')}\n"
    if valid(data.get("chassis_last5")): text += f"│   ├─ Last 5    : {data.get('chassis_last5')}\n"
    if valid(v.get("engine")): text += f"│   └─ Engine    : {v.get('engine')}\n│\n"

    text += "├─ 📅 <b>REGISTRATION</b>\n"
    if valid(v.get("registration_date")): text += f"│   ├─ Date      : {v.get('registration_date')}\n"
    text += f"│   ├─ Reg No    : {reg_no}\n"
    if valid(v.get("rto")): text += f"│   └─ RTO       : {v.get('rto')}\n│\n"

    if valid(v.get("insurance_company")) or valid(v.get("insurance_upto")):
        text += "├─ 🛡️ <b>INSURANCE</b>\n"
        if valid(v.get("insurance_company")): text += f"│   ├─ Company   : {v.get('insurance_company')}\n"
        if valid(v.get("insurance_upto")): text += f"│   └─ Upto      : {v.get('insurance_upto')}\n│\n"

    text += "────────────────────────────────────────────\n"
    text += "⚠️🚨 <b>IMPORTANT NOTE</b> 🚨⚠️\n"
    text += "🔍 Ye details sirf AUDIT / VERIFICATION purpose ke liye hain.\n"
    text += "🚫 Kripya iska koi bhi GALAT USE na karein.\n"
    text += "────────────────────────────────────────────"
    
    return text
