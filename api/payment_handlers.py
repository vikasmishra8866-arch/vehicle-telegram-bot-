from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .keyboards import credit_plans, unlimited_plans, recharge_menu
from .database import create_payment_order, create_unlimited_request
from .utils import generate_upi_qr
from .config import ADMIN_ID, ADMIN_USERNAME

router = Router()

@router.callback_query(lambda c: c.data == "cat_credits")
async def show_credits(callback: types.CallbackQuery):
    await callback.message.edit_text("💰 <b>CREDIT PACKAGES</b>\n\nKripya plan chunein:", reply_markup=credit_plans(), parse_mode="HTML")

@router.callback_query(lambda c: c.data == "cat_unlimited")
async def show_unlimited(callback: types.CallbackQuery):
    await callback.message.edit_text("♾️ <b>UNLIMITED PLANS</b>\n\nPricing ke liye admin se contact karein.", reply_markup=unlimited_plans(), parse_mode="HTML")

@router.callback_query(lambda c: c.data == "back_to_recharge")
async def back_recharge(callback: types.CallbackQuery):
    await callback.message.edit_text("🛒 <b>RECHARGE MENU</b>\n\nKripya category chunein:", reply_markup=recharge_menu(), parse_mode="HTML")

# क्रेडिट खरीदना (UPI QR)
@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_credits(callback: types.CallbackQuery):
    _, credits, amount = callback.data.split("_")
    credits, amount = int(credits), int(amount)
    user_id = callback.from_user.id
    
    order_id = create_payment_order(user_id, f"{credits} Credits", amount, credits)
    if not order_id:
        return await callback.answer("❌ Error creating order.", show_alert=True)
        
    qr_img = generate_upi_qr(amount, credits)
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=qr_img,
        caption=f"💳 <b>PAYMENT DETAILS</b>\n\nPlan: {credits} Credits\nAmount: ₹{amount}\nOrder ID: <code>{order_id[:8]}</code>\n\n⚠️ QR expires in 5 minutes. Pay now and click 'I Have Paid'.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ I Have Paid", callback_data=f"paid_{order_id}")]
        ])
    )
    await callback.answer()

# यूजर ने "I Have Paid" दबाया
@router.callback_query(lambda c: c.data.startswith("paid_"))
async def user_paid(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]
    user = callback.from_user
    
    # (यहाँ हम डेटाबेस में स्टेटस 'verification' करते हैं)
    from .database import get_supabase
    get_supabase().table("payment_orders").update({"status": "verification"}).eq("id", order_id).execute()
    
    await callback.message.edit_caption(caption="⏳ <b>Verification Pending</b>\n\nAapka payment verify kiya ja raha hai. Admin jald hi approve karega.", parse_mode="HTML")
    
    # एडमिन को नोटिफिकेशन भेजें
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ APPROVE", callback_data=f"appr_{order_id}"),
         InlineKeyboardButton(text="❌ REJECT", callback_data=f"rej_{order_id}")]
    ])
    await callback.bot.send_message(
        ADMIN_ID, 
        f"💸 <b>PAYMENT VERIFICATION</b>\n\nUser: @{user.username} (<code>{user.id}</code>)\nOrder ID: <code>{order_id[:8]}</code>\n\nKripya bank me check karke approve karein.",
        parse_mode="HTML", reply_markup=admin_kb
    )

# अनलिमिटेड प्लान चुनना
@router.callback_query(lambda c: c.data.startswith("unlim_"))
async def select_unlimited(callback: types.CallbackQuery):
    days = int(callback.data.split("_")[1])
    req_id = create_unlimited_request(callback.from_user.id, days)
    
    await callback.message.edit_text(
        f"♾️ <b>{days} DAYS UNLIMITED ACCESS</b>\n\nPricing: Contact Admin\n\nAapki request bhej di gayi hai. Admin aapse price discuss karega.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")]
        ])
    )
    await callback.bot.send_message(ADMIN_ID, f"🔔 <b>NEW UNLIMITED REQUEST</b>\n\nUser: @{callback.from_user.username}\nDays: {days}\nRequest ID: <code>{req_id[:8]}</code>\n\nActivate karne ke liye /admin par jayein.")
