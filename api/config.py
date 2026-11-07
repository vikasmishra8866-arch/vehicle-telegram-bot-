import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
VEHICLE_API_KEY = os.getenv("VEHICLE_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret123")
