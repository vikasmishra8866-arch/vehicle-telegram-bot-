import os
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from mangum import Mangum

# कॉन्फ़िगरेशन से वेरिएबल्स इम्पोर्ट करें
from .config import BOT_TOKEN, WEBHOOK_SECRET

# सारे हैंडलर्स (राउटर्स) इम्पोर्ट करें
from .user_handlers import router as user_router
from .payment_handlers import router as payment_router
from .admin_handlers import router as admin_router

# FastAPI और aiogram को इनिशियलाइज़ करें
app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# सारे राउटर्स को Dispatcher में जोड़ें
dp.include_router(user_router)
dp.include_router(payment_router)
dp.include_router(admin_router)

@app.post(f"/api/webhook/{WEBHOOK_SECRET}")
async def webhook(request: Request):
    """
    Telegram से आने वाले हर मैसेज और बटन क्लिक को यहाँ रिसीव किया जाता है।
    """
    try:
        # 1. Telegram से आया डेटा पढ़ें
        update_data = await request.json()
        
        # 2. डेटा को aiogram के फॉर्मेट में बदलें
        update = types.Update.model_validate(
            update_data, 
            context={"bot": bot, "dispatcher": dp}
        )
        
        # 3. मैसेज को प्रोसेस करें
        await dp.feed_update(bot, update)
        
        # 4. Telegram को बताएं कि मैसेज मिल गया (200 OK)
        return {"ok": True}
        
    except Exception as e:
        # अगर कोई एरर आती है, तो Vercel Logs में दिखेगी
        print(f"❌ Webhook Error: {type(e).__name__}: {e}")
        return {"ok": False}

@app.get("/")
def health_check():
    """
    यह रास्ता ब्राउज़र में चेक करने के लिए है कि सर्वर लाइव है या नहीं।
    """
    return {"status": "Bot is running perfectly!"}

# ⚡ Vercel Serverless के लिए सबसे ज़रूरी लाइन (Mangum ASGI Handler)
handler = Mangum(app)
