from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .keyboards import credit_plans, unlimited_plans, recharge_menu
from .database import create_payment_order, create_unlimited_request, update_order_status
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

@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_credits(callback: types.CallbackQuery):
    try:
        parts = callback.data.split("_")
        credits = int(parts[1])
        amount = int(parts[2])
        user_id = callback.from_user.id
        
        order_id = create_payment_order(user_id, f"{credits} Credits", amount, credits)
        if not order_id:
            return await callback.answer("❌ Database error. Order could not be saved.", show_alert=True)
            
        qr_img = generate_upi_qr(amount, credits)
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=qr_img,
            caption=f"💳 <b>PAYMENT DETAILS</b>\n\nPlan: {credits} Credits\nAmount: ₹{amount}\nOrder ID: <code>{str(order_id)[:8]}</code>\n\n⚠️ QR expires in 5 minutes. Pay now and click 'I Have Paid'.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ I Have Paid", callback_data=f"paid_{order_id}")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Callback Error (buy): {e}")
        await callback.answer("❌ Error processing request.", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("paid_"))
async def user_paid(callback: types.CallbackQuery):
    try:
        # order_id निकालें (क्योंकि UUID में हाइफ़न होते हैं, इसलिए replace का इस्तेमाल करना सुरक्षित है)
        order_id = callback.data.replace("paid_", "")
        user = callback.from_user
        
        # डेटाबेस में स्टेटस 'verification' करें
        update_order_status(order_id, "verification")
        
        await callback.message.edit_caption(
            caption="⏳ <b>Verification Pending</b>\n\nAapka payment verify kiya ja raha hai. Admin jald hi approve karega.", 
            parse_mode="HTML"
        )
        
        # एडमिन को नोटिफिकेशन भेजें (✅ APPROVE और ❌ REJECT बटन के साथ)
        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ APPROVE", callback_data=f"appr_{order_id}"),
             InlineKeyboardButton(text="❌ REJECT", callback_data=f"rej_{order_id}")]
        ])
        
        await callback.bot.send_message(
            ADMIN_ID, 
            f"💸 <b>NEW PAYMENT VERIFICATION</b>\n\n"
            f"User: @{user.username} (<code>{user.id}</code>)\n"
            f"Order ID: <code>{order_id[:8]}</code>\n\n"
            f"Kripya bank me check karke approve karein.",
            parse_mode="HTML", 
            reply_markup=admin_kb
        )
    except Exception as e:
        print(f"Callback Error (paid): {e}")

@router.callback_query(lambda c: c.data.startswith("unlim_"))
async def select_unlimited(callback: types.CallbackQuery):
    try:
        days = int(callback.data.split("_")[1])
        req_id = create_unlimited_request(callback.from_user.id, days)
        
        if not req_id:
            return await callback.answer("❌ Error creating request.", show_alert=True)
            
        await callback.message.edit_text(
            f"♾️ <b>{days} DAYS UNLIMITED ACCESS</b>\n\n"
            f"Pricing: Contact Admin\n\n"
            f"Aapki request bhej di gayi hai. Admin aapse price discuss karega.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📞 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")]
            ])
        )
        
        await callback.bot.send_message(
            ADMIN_ID, 
            f"🔔 <b>NEW UNLIMITED REQUEST</b>\n\n"
            f"User: @{callback.from_user.username} (<code>{callback.from_user.id}</code>)\n"
            f"Days: {days}\n"
            f"Request ID: <code>{str(req_id)[:8]}</code>\n\n"
            f"Activate karne ke liye /grant {callback.from_user.id} {days} command use karein."
        )
    except Exception as e:
        print(f"Callback Error (unlim): {e}")
