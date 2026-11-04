from aiogram import Router, types
from aiogram.filters import Command
from api.database import get_or_create_user, check_cooldown, deduct_credit, log_search
from api.config import API_KEY, ADMIN_ID
import aiohttp
from datetime import datetime
import re

router = Router()

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    bal = user.get("wallet_balance", 0)
    
    text = (
        f"🚗 <b>Vehicle Lookup Bot</b>\n\n"
        f"👋 Welcome {message.from_user.first_name}!\n"
        f"💳 Wallet Balance: <b>{bal} Credits</b>\n\n"
        f"Kisi bhi vehicle ka registration number bhejein.\n"
        f"Example: <code>GJ05HG7801</code>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(lambda msg: re.match(r"^[A-Za-z0-9\s-]{6,15}$", msg.text or ""))
async def search_vehicle(message: types.Message):
    user_id = message.from_user.id
    raw_text = message.text.strip()
    reg_no = re.sub(r'[^a-zA-Z0-9]', '', raw_text).upper()
    
    user = get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)

    # 1. 5-Second Cooldown चेक
    if not check_cooldown(user_id):
        await message.reply("⏳ Please wait 5 seconds before searching another vehicle.")
        return

    # 2. एडमिन और अनलिमिटेड चेक
    is_admin = (user_id == ADMIN_ID)
    is_unlimited = False # इसे बाद में सब्सक्रिप्शन टेबल से चेक करेंगे
    
    # 3. वॉलेट चेक
    if not is_admin and not is_unlimited and user.get("wallet_balance", 0) <= 0:
        await message.reply("❌ Aapke paas credits nahi hain. Kripya /addcredits se recharge karein.")
        return

    msg = await message.reply("🔍 Fetching vehicle details...\n<i>(ye 8-17 second le sakta hai)</i>", parse_mode="HTML")

    # 4. API कॉल
    url = f"https://hideme.eu.org/lookup?api=mvahan&key={API_KEY}&number={reg_no}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=25) as response:
                data = await response.json()
    except Exception as e:
        await msg.edit_text("⏱️ Server ne time out kar diya. Thodi der baad try karein.")
        return

    if not data or not data.get("success") or "vehicle" not in data:
        await msg.edit_text("❌ Vehicle not found. Number check karke dobara try karein.")
        log_search(user_id, reg_no, "not_found", 0)
        return

    v = data["vehicle"]
    
    # 5. मोबाइल नंबर की जांच (क्रेडिट कटने का नियम)
    mobile_found = data.get("mobile_found", False)
    credit_msg = ""
    
    if not is_admin and not is_unlimited:
        if mobile_found:
            # मोबाइल मिला है, क्रेडिट काटो
            if deduct_credit(user_id):
                credit_msg = "\n\n<i>(1 Credit deducted)</i>"
                log_search(user_id, reg_no, "success", 1)
        else:
            # मोबाइल नहीं मिला, क्रेडिट मत काटो
            credit_msg = "\n\n⚠️ <i>Owner contact not found. No credits deducted.</i>"
            log_search(user_id, reg_no, "mobile_not_found", 0)
    else:
        log_search(user_id, reg_no, "success_admin", 0)

    # 6. डेटा फॉर्मेटिंग (आपका ASCII डिज़ाइन)
    formatted_text = format_vehicle_tree(reg_no, v, data) + credit_msg
    await msg.edit_text(formatted_text, parse_mode="HTML")


def format_vehicle_tree(reg_no, v, data):
    def valid(val):
        if val is None or str(val).strip().lower() in ["", "null", "na", "none", "0"]: return False
        return True

    def get_val(key, default="N/A"):
        return v.get(key) if valid(v.get(key)) else default

    # ट्री बनाना
    text = f"🧭 <b>VEHICLE JOURNEY</b> — {reg_no}\n"
    text += "────────────────────────────────────────────\n│\n"

    # 1. Identity
    text += "├─ 🚘 <b>VEHICLE IDENTITY</b>\n"
    if valid(v.get("make")): text += f"│   ├─ Make      : {v.get('make')}\n"
    if valid(v.get("variant")): text += f"│   ├─ Variant   : {v.get('variant')}\n"
    if valid(v.get("fuel")): text += f"│   ├─ Fuel      : {v.get('fuel')}\n"
    if valid(v.get("color")): text += f"│   ├─ Color     : {v.get('color')}\n"
    if valid(v.get("body_type")): text += f"│   ├─ Body Type : {v.get('body_type')}\n"
    if valid(v.get("vehicle_class")): text += f"│   └─ Class     : {v.get('vehicle_class')}\n│\n"

    # 2. Owner
    text += "├─ 👤 <b>OWNER DETAILS</b>\n"
    if valid(v.get("owner")): text += f"│   ├─ Owner     : {v.get('owner')}\n"
    if valid(data.get("mobile")): text += f"│   ├─ Mobile    : {data.get('mobile')}\n"
    text += f"│   └─ Found     : {'Yes' if data.get('mobile_found') else 'No'}\n│\n"

    # 3. Machine
    text += "├─ 🔑 <b>MACHINE DETAILS</b>\n"
    if valid(v.get("chassis")): text += f"│   ├─ Chassis   : {v.get('chassis')}\n"
    if valid(data.get("chassis_last5")): text += f"│   ├─ Last 5    : {data.get('chassis_last5')}\n"
    if valid(v.get("engine")): text += f"│   └─ Engine    : {v.get('engine')}\n│\n"

    # 4. Registration
    text += "├─ 📅 <b>REGISTRATION</b>\n"
    if valid(v.get("registration_date")): text += f"│   ├─ Date      : {v.get('registration_date')}\n"
    text += f"│   ├─ Reg No    : {reg_no}\n"
    if valid(v.get("rto")): text += f"│   └─ RTO       : {v.get('rto')}\n│\n"

    # 5. Insurance
    if valid(v.get("insurance_company")) or valid(v.get("insurance_upto")):
        text += "├─ 🛡️ <b>INSURANCE</b>\n"
        if valid(v.get("insurance_company")): text += f"│   ├─ Company   : {v.get('insurance_company')}\n"
        if valid(v.get("insurance_upto")): text += f"│   └─ Upto      : {v.get('insurance_upto')}\n│\n"

    text += "────────────────────────────────────────────\n"
    text += "⚠️🚨 <b>IMPORTANT NOTE</b> 🚨⚠️\n"
    text += "🔍 Ye details sirf AUDIT / VERIFICATION purpose ke liye hain.\n"
    text += "🚫 Kripya iska koi bhi GALAT USE na karein.\n"
    text += "🔒 Privacy & safety ka khayal rakhein. 🙏\n"
    text += "────────────────────────────────────────────"
    
    return text
