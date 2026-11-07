from aiogram import Router, types
from aiogram.filters import Command
import aiohttp
import re
import asyncio
from .config import VEHICLE_API_KEY
from .keyboards import main_toolbar
from .utils import format_vehicle_dossier

router = Router()

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    # स्टार्ट मैसेज बहुत सुंदर और इंगेजिंग
    text = (
        "🚀 <b>Welcome to VIP Vehicle Verification!</b> 🚀\n\n"
        "🔍 <i>Enter a vehicle number to get detailed information.</i>\n"
        "📝 <b>Example:</b> <code>GJ05CT6560</code>\n\n"
        "👇 <i>Need help? Click the Help button below.</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_toolbar())

@router.message(lambda msg: msg.text == "ℹ️ Help")
async def btn_help(message: types.Message):
    # हेल्प बटन पर सिर्फ @Rizx_x दिखेगा
    text = (
        "🤝 <b>Help & Support</b>\n\n"
        "For any queries or assistance, please contact:\n"
        "👤 <b>Admin:</b> @Rizx_x\n\n"
        "🔍 <i>Type a vehicle number directly to search.</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(lambda msg: re.match(r"^[A-Za-z0-9\s-]{6,15}$", msg.text or ""))
async def search_vehicle(message: types.Message):
    # Auto-Capitalization
    reg_no = re.sub(r'[^a-zA-Z0-9]', '', message.text).upper()
    
    # सर्चिंग मैसेज
    msg = await message.reply("🔍 <b>Searching for vehicle...</b> <i>Please wait.</i> ⏳", parse_mode="HTML")
    
    url = f"https://hideme.eu.org/lookup?api=mvahan&key={VEHICLE_API_KEY}&number={reg_no}"
    
    data = None
    
    # Retry Logic
    for attempt in range(2):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=25) as response:
                    if response.status == 200:
                        fetched_data = await response.json()
                        if fetched_data and fetched_data.get("success"):
                            data = fetched_data
                            break 
        except Exception as e:
            print(f"API Attempt {attempt+1} failed: {e}")
        
        if attempt == 0:
            await msg.edit_text("🔄 <b>API is taking time.</b> <i>Retrying once more...</i> ⏳", parse_mode="HTML")
            await asyncio.sleep(2)

    # अगर डेटा नहीं मिला
    if not data or not data.get("vehicle"):
        await msg.edit_text("❌ <b>Vehicle Not Found!</b>\n\n<i>Please check the vehicle number and try again.</i>", parse_mode="HTML")
        return

    # सक्सेस होने पर VIP फॉर्मेट में रिजल्ट
    formatted_text = format_vehicle_dossier(data, reg_no)
    await msg.edit_text(formatted_text, parse_mode="HTML")
