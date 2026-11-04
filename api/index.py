import os
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from mangum import Mangum

from .config import BOT_TOKEN, WEBHOOK_SECRET
from .bot_handlers import router

app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

@app.post(f"/api/webhook/{WEBHOOK_SECRET}")
async def webhook(request: Request):
    try:
        update_data = await request.json()
        print("📥 Received update from Telegram")
        
        # Vercel पर फ्रीज होने से रोकने के लिए सीधे await का इस्तेमाल
        update = types.Update.model_validate(update_data, context={"bot": bot, "dispatcher": dp})
        await dp.feed_update(bot, update)
        
        return {"ok": True}
    except Exception as e:
        print(f"❌ Webhook Error: {type(e).__name__}: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/")
def health_check():
    return {"status": "Bot is running!"}

# Vercel के लिए सबसे जरुरी हैंडलर
handler = Mangum(app)
