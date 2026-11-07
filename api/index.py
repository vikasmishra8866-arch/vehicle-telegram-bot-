from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from mangum import Mangum
from .config import BOT_TOKEN, WEBHOOK_SECRET
from .user_handlers import router as user_router

app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# सिर्फ यूजर हैंडलर जोड़ें
dp.include_router(user_router)

@app.post(f"/api/webhook/{WEBHOOK_SECRET}")
async def webhook(request: Request):
    try:
        update_data = await request.json()
        update = types.Update.model_validate(update_data, context={"bot": bot, "dispatcher": dp})
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return {"ok": False}

@app.get("/")
def health_check():
    return {"status": "Bot is running! Lightweight version."}

handler = Mangum(app)
