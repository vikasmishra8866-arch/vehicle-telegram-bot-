import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
VEHICLE_API_KEY = os.getenv("VEHICLE_API_KEY")

ADMIN_ID = int(os.getenv("ADMIN_ID", "8204069256"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret123")
