from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import ADMIN_ID
from .keyboards import admin_dashboard
from .database import approve_payment, grant_unlimited_access

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("👑 <b>ADMIN CONTROL PANEL</b>", parse_mode="HTML", reply_markup=admin_dashboard())

@router.message(lambda msg: msg.text == "👑 Admin Panel")
async def admin_panel_btn(message: types.Message):
    await admin_panel(message)

# पेमेंट अप्रूवल लॉजिक (जब एडमिन ✅ दबाए)
@router.callback_query(lambda c: c.data.startswith("appr_"))
async def approve_cb(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    order_id = callback.data.split("_")[1]
    
    success, msg = approve_payment(order_id, ADMIN_ID)
    if success:
        await callback.message.edit_text("✅ Payment Approved successfully. Credits added.")
        # (यहाँ आप चाहें तो यूजर को मैसेज भेज सकते हैं कि उसके क्रेडिट आ गए हैं)
    else:
        await callback.answer(f"❌ Error: {msg}", show_alert=True)

# पेमेंट रिजेक्ट लॉजिक (जब एडमिन ❌ दबाए)
@router.callback_query(lambda c: c.data.startswith("rej_"))
async def reject_cb(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    order_id = callback.data.split("_")[1]
    
    from .database import get_supabase
    get_supabase().table("payment_orders").update({"status": "rejected"}).eq("id", order_id).execute()
    await callback.message.edit_text("❌ Payment Rejected.")

@router.message(Command("grant"))
async def grant_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        if len(args) != 3: return await message.reply("Format: /grant [User_ID] [Days]")
        user_id, days = int(args[1]), int(args[2])
        
        if grant_unlimited_access(user_id, days, ADMIN_ID):
            await message.reply(f"✅ {days} Days Unlimited Access granted to {user_id}.")
            await message.bot.send_message(user_id, f"🎉 Aapko {days} days ka Unlimited Search Access mil gaya hai!")
        else:
            await message.reply("❌ Failed to grant access.")
    except ValueError:
        await message.reply("❌ Invalid format.")
