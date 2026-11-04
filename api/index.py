import os
from fastapi import FastAPI, Request, BackgroundTasks
from aiogram import Bot, Dispatcher, types
from mangum import Mangum

# ⚠️ बहुत ज़रूरी: Vercel पर इम्पोर्ट्स के आगे डॉट (.) का इस्तेमाल करें
from .config import BOT_TOKEN, WEBHOOK_SECRET
from .bot_handlers import router

# FastAPI और Bot को इनिशियलाइज़ करें
app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# बॉट के सारे कमांड्स (handlers) जोड़ें
dp.include_router(router)

async def process_update(update_data: dict):
    """यह फंक्शन बैकग्राउंड में Telegram के अपडेट को प्रोसेस करेगा"""
    try:
        # aiogram v3 के लिए अपडेट को वैलिडेट करें
        update = types.Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"❌ Error processing update: {e}")

@app.post(f"/api/webhook/{WEBHOOK_SECRET}")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """Telegram Webhook को रिसीव करने का endpoint"""
    try:
        # 1. Telegram से आया डेटा पढ़ें
        update_data = await request.json()
        
        # 2. डेटा को बैकग्राउंड टास्क में भेजें (ताकि Telegram को तुरंत 200 OK मिले)
        background_tasks.add_task(process_update, update_data)
        
        # 3. तुरंत रिस्पॉन्स दें
        return {"ok": True}
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/")
def health_check():
    """ब्राउज़र में चेक करने के लिए कि सर्वर चालू है"""
    return {"status": "Bot is running perfectly!", "webhook_path": f"/api/webhook/{WEBHOOK_SECRET}"}

# ⚡ Vercel Serverless के लिए सबसे ज़रूरी लाइन (Mangum ASGI Handler)
handler = Mangum(app)
