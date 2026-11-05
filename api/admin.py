from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import ADMIN_ID
from .keyboards import admin_dashboard
from .database import approve_payment, grant_unlimited_access, get_supabase
from datetime import datetime

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("👑 <b>ADMIN CONTROL PANEL</b>\n\nYahan se bot manage karein:", parse_mode="HTML", reply_markup=admin_dashboard())

@router.message(lambda msg: msg.text == "👑 Admin Panel")
async def admin_panel_btn(message: types.Message):
    await admin_panel(message)

# --- एडमिन पैनल के इनलाइन बटन हैंडलर्स ---

@router.callback_query(lambda c: c.data == "admin_users")
async def cb_admin_users(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    await callback.answer("Users Management feature abhi develop ho raha hai!", show_alert=True)

@router.callback_query(lambda c: c.data == "admin_credits")
async def cb_admin_credits(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("💳 <b>ADD/REMOVE CREDITS</b>\n\nKripya ye command use karein:\n<code>/addcredit [User_ID] [Amount]</code>", parse_mode="HTML")
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_payments")
async def cb_admin_payments(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("💸 <b>PENDING PAYMENTS</b>\n\nJab koi user 'I Have Paid' dabata hai, toh aapke paas ek notification aayega jisse aap approve kar sakte hain.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_subs")
async def cb_admin_subs(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("♾️ <b>UNLIMITED SUBS</b>\n\nKripya ye command use karein:\n<code>/grant [User_ID] [Days]</code>", parse_mode="HTML")
    await callback.answer()

# --- अप्रूवल और रिजेक्शन लॉजिक ---

@router.callback_query(lambda c: c.data.startswith("appr_"))
async def approve_cb(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    order_id = callback.data.replace("appr_", "")
    
    success, msg = approve_payment(order_id, ADMIN_ID)
    if success:
        await callback.message.edit_text("✅ Payment Approved successfully. Credits added.")
        await callback.bot.send_message(callback.message.chat.id, "✅ User ke credits add ho gaye hain.") # (Optionally notify user)
    else:
        await callback.answer(f"❌ Error: {msg}", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("rej_"))
async def reject_cb(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    order_id = callback.data.replace("rej_", "")
    
    get_supabase().table("payment_orders").update({"status": "rejected"}).eq("id", order_id).execute()
    await callback.message.edit_text("❌ Payment Rejected.")

@router.message(Command("addcredit"))
async def add_credit_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        if len(args) != 3: return await message.reply("Format: /addcredit [User_ID] [Amount]")
        user_id, amount = int(args[1]), int(args[2])
        
        supabase = get_supabase()
        res = supabase.table("users").select("wallet_balance").eq("telegram_id", user_id).execute()
        if res.data:
            current_bal = res.data[0]["wallet_balance"]
            new_bal = current_bal + amount
            supabase.table("users").update({"wallet_balance": new_bal}).eq("telegram_id", user_id).execute()
            await message.reply(f"✅ {amount} Credits added to {user_id}.")
        else:
            await message.reply("❌ User not found.")
    except ValueError:
        await message.reply("❌ Invalid ID or Amount.")

@router.message(Command("grant"))
async def grant_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        if len(args) != 3: return await message.reply("Format: /grant [User_ID] [Days]")
        user_id, days = int(args[1]), int(args[2])
        
        if grant_unlimited_access(user_id, days, ADMIN_ID):
            await message.reply(f"✅ {days} Days Unlimited Access granted to {user_id}.")
        else:
            await message.reply("❌ Failed to grant access.")
    except ValueError:
        await message.reply("❌ Invalid format.")
