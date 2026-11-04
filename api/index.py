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
        print("📥 Received update from Telegram") # लॉग्स में दिखेगा
        
        # सीधे प्रोसेस करें ताकि Vercel सर्वर को बंद न करे
        update = types.Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        
        return {"ok": True}
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/")
def health_check():
    return {"status": "Bot is running!"}

handler = Mangum(app)
