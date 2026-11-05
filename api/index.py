from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from mangum import Mangum
from .config import BOT_TOKEN, WEBHOOK_SECRET
from .user_handlers import router as user_router
from .payment_handlers import router as pay_router
from .admin_handlers import router as admin_router

app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(pay_router)
dp.include_router(admin_router)

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
    return {"status": "Bot is running!"}

handler = Mangum(app)
