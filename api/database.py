from supabase import create_client, Client
from api.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timezone
import pytz

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_or_create_user(telegram_id: int, username: str, first_name: str):
    res = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if not res.data:
        # नया यूजर बनाएं (1 फ्री क्रेडिट के साथ)
        new_user = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "wallet_balance": 1,
            "has_received_demo": True
        }
        supabase.table("users").insert(new_user).execute()
        # ट्रांजैक्शन लॉग
        supabase.table("wallet_transactions").insert({
            "user_id": telegram_id,
            "type": "credit",
            "amount": 1,
            "previous_balance": 0,
            "new_balance": 1,
            "reason": "Free Demo Credit"
        }).execute()
        return new_user
    return res.data[0]

def check_cooldown(telegram_id: int):
    res = supabase.table("users").select("last_search_at").eq("telegram_id", telegram_id).execute()
    if res.data and res.data[0].get("last_search_at"):
        last_search = datetime.fromisoformat(res.data[0]["last_search_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if (now - last_search).total_seconds() < 5:
            return False # कूलडाउन एक्टिव है
    # समय अपडेट करें
    supabase.table("users").update({"last_search_at": datetime.now(timezone.utc).isoformat()}).eq("telegram_id", telegram_id).execute()
    return True

def deduct_credit(telegram_id: int, amount=1):
    # यहाँ हमें Atomic ट्रांजैक्शन के लिए RPC (Stored Procedure) इस्तेमाल करना चाहिए, 
    # लेकिन सिंप्लिसिटी के लिए हम पहले चेक कर रहे हैं।
    res = supabase.table("users").select("wallet_balance").eq("telegram_id", telegram_id).execute()
    if res.data:
        current_bal = res.data[0]["wallet_balance"]
        if current_bal >= amount:
            new_bal = current_bal - amount
            supabase.table("users").update({"wallet_balance": new_bal}).eq("telegram_id", telegram_id).execute()
            supabase.table("wallet_transactions").insert({
                "user_id": telegram_id, "type": "debit", "amount": amount,
                "previous_balance": current_bal, "new_balance": new_bal, "reason": "Vehicle Search"
            }).execute()
            return True
    return False

def log_search(telegram_id: int, vehicle_number: str, status: str, credits_deducted: int):
    supabase.table("search_history").insert({
        "user_id": telegram_id, "vehicle_number": vehicle_number, 
        "status": status, "credits_deducted": credits_deducted
    }).execute()
