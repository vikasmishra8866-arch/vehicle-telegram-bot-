from fastapi import FastAPI, Request, BackgroundTasks
from aiogram import Bot, Dispatcher, types
from api.config import BOT_TOKEN, WEBHOOK_SECRET
from api.bot_handlers import router
import asyncio

app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# बॉट के राउटर जोड़ें
dp.include_router(router)

async def feed_update(update_data):
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)

@app.post(f"/api/webhook/{WEBHOOK_SECRET}")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    # Telegram को तुरंत 200 OK भेजें, और प्रोसेसिंग बैकग्राउंड में करें
    update_data = await request.json()
    background_tasks.add_task(feed_update, update_data)
    return {"ok": True}

@app.get("/")
def health_check():
    return {"status": "Bot is running!"}
