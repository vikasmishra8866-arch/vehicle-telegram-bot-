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
    text = "<code>GJ05CT6560</code> IS FORMAT ME GADI NUMBER ENTER KRE"
    await message.answer(text, parse_mode="HTML", reply_markup=main_toolbar())

@router.message(lambda msg: msg.text == "ℹ️ Help")
async def btn_help(message: types.Message):
    text = "<code>GJ05CT6560</code> IS FORMAT ME GADI NUMBER ENTER KRE"
    await message.answer(text, parse_mode="HTML")

@router.message(lambda msg: re.match(r"^[A-Za-z0-9\s-]{6,15}$", msg.text or ""))
async def search_vehicle(message: types.Message):
    reg_no = re.sub(r'[^a-zA-Z0-9]', '', message.text).upper()
    
    msg = await message.reply("🔍 Fetching vehicle details...", parse_mode="HTML")
    url = f"https://hideme.eu.org/lookup?api=mvahan&key={VEHICLE_API_KEY}&number={reg_no}"
    
    data = None
    
    # 🚀 Retry Logic: अगर API फेल होती है, तो 2 बार कोशिश करेगा
    for attempt in range(2):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=25) as response:
                    if response.status == 200:
                        fetched_data = await response.json()
                        if fetched_data and fetched_data.get("success"):
                            data = fetched_data
                            break # सक्सेस हो गया तो लूप से बाहर आ जाएं
        except Exception as e:
            print(f"API Attempt {attempt+1} failed: {e}")
        
        if attempt == 0:
            # पहली बार फेल होने पर यूजर को बताएं और 2 सेकंड रुकें
            await msg.edit_text("⏳ API is taking time. Retrying once more...", parse_mode="HTML")
            await asyncio.sleep(2)

    # अगर दोनों बार फेल हो जाए
    if not data or not data.get("vehicle"):
        await msg.edit_text("❌ Vehicle not found or API is currently down. Please try again after some time.")
        return

    # सक्सेस होने पर रिजल्ट दिखाएं
    formatted_text = format_vehicle_dossier(data, reg_no)
    await msg.edit_text(formatted_text, parse_mode="HTML")
