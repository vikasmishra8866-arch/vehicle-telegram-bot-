import os
from fastapi import FastAPI, Request, BackgroundTasks
from aiogram import Bot, Dispatcher, types
from mangum import Mangum

# रिलेटिव इम्पोर्ट्स (Vercel पर Import Error रोकने के लिए)
from .config import BOT_TOKEN, WEBHOOK_SECRET
from .bot_handlers import router

# FastAPI ऐप और aiogram बॉट इनिशियलाइज़ करें
app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# बॉट के सारे कमांड्स (handlers) जोड़ें
dp.include_router(router)

async def process_update(update_data: dict):
    """Telegram से आए डेटा को प्रोसेस करने का फंक्शन"""
    try:
        # aiogram v3 के लिए अपडेट वैलिडेट करें
        update = types.Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"Error processing update: {e}")

@app.post(f"/api/webhook/{WEBHOOK_SECRET}")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """Telegram Webhook endpoint"""
    try:
        update_data = await request.json()
        # Telegram को तुरंत रिस्पॉन्स देने के लिए बैकग्राउंड टास्क में भेजें
        background_tasks.add_task(process_update, update_data)
        return {"ok": True}
    except Exception as e:
        print(f"Webhook Error: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/")
def health_check():
    """Vercel और ब्राउज़र चेक के लिए"""
    return {"status": "Bot is running perfectly!"}

# ⚡ Vercel के लिए सबसे ज़रूरी लाइन (Mangum ASGI Handler)
handler = Mangum(app)
