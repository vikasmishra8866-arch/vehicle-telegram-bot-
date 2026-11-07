from aiogram import Router, types
from aiogram.filters import Command
import aiohttp
import re
from .config import VEHICLE_API_KEY
from .keyboards import main_toolbar
from .utils import format_vehicle_dossier

router = Router()

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    # आपका दिया हुआ सटीक मैसेज
    text = "<code>GJ05CT6560</code> IS FORMAT ME GADI NUMBER ENTER KRE"
    await message.answer(text, parse_mode="HTML", reply_markup=main_toolbar())

@router.message(lambda msg: msg.text == "ℹ️ Help")
async def btn_help(message: types.Message):
    # Help दबाने पर भी वही मैसेज
    text = "<code>GJ05CT6560</code> IS FORMAT ME GADI NUMBER ENTER KRE"
    await message.answer(text, parse_mode="HTML")

@router.message(lambda msg: re.match(r"^[A-Za-z0-9\s-]{6,15}$", msg.text or ""))
async def search_vehicle(message: types.Message):
    # 🚀 Auto-Capitalization (छोटे अक्षरों को अपने आप बड़ा करेगा)
    reg_no = re.sub(r'[^a-zA-Z0-9]', '', message.text).upper()
    
    msg = await message.reply("🔍 Fetching vehicle details...", parse_mode="HTML")
    url = f"https://hideme.eu.org/lookup?api=mvahan&key={VEHICLE_API_KEY}&number={reg_no}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=25) as response:
                data = await response.json()
    except Exception as e:
        print(f"API Error: {e}")
        await msg.edit_text("⏱️ API Timeout or Server Error. Please try again.")
        return

    if not data or not data.get("success") or "vehicle" not in data:
        await msg.edit_text("❌ Vehicle not found.")
        return

    # नया फॉर्मेट कॉल करें
    formatted_text = format_vehicle_dossier(data, reg_no)
    await msg.edit_text(formatted_text, parse_mode="HTML")
