from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timezone

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_or_create_user(telegram_id: int, username: str, first_name: str):
    try:
        res = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        if not res.data:
            new_user = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "wallet_balance": 1, # 1 Free Credit
            }
            supabase.table("users").insert(new_user).execute()
            # Log Transaction
            supabase.table("wallet_transactions").insert({
                "user_id": telegram_id, "type": "credit", "amount": 1,
                "previous_balance": 0, "new_balance": 1, "reason": "Free Demo Credit"
            }).execute()
            return new_user
        return res.data[0]
    except Exception as e:
        print(f"DB Error get_or_create_user: {e}")
        return None

def check_cooldown(telegram_id: int):
    try:
        res = supabase.table("users").select("last_search_at").eq("telegram_id", telegram_id).execute()
        if res.data and res.data[0].get("last_search_at"):
            last_search = datetime.fromisoformat(res.data[0]["last_search_at"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if (now - last_search).total_seconds() < 5:
                return False
        # Update time
        supabase.table("users").update({"last_search_at": datetime.now(timezone.utc).isoformat()}).eq("telegram_id", telegram_id).execute()
        return True
    except Exception as e:
        print(f"DB Error cooldown: {e}")
        return True # Allow if DB fails

def deduct_credit(telegram_id: int):
    try:
        res = supabase.table("users").select("wallet_balance").eq("telegram_id", telegram_id).execute()
        if res.data:
            current_bal = res.data[0]["wallet_balance"]
            if current_bal >= 1:
                new_bal = current_bal - 1
                supabase.table("users").update({"wallet_balance": new_bal}).eq("telegram_id", telegram_id).execute()
                supabase.table("wallet_transactions").insert({
                    "user_id": telegram_id, "type": "debit", "amount": 1,
                    "previous_balance": current_bal, "new_balance": new_bal, "reason": "Vehicle Search"
                }).execute()
                return True
        return False
    except Exception as e:
        print(f"DB Error deduct_credit: {e}")
        return False

def log_search(telegram_id: int, vehicle_number: str, status: str, credits_deducted: int):
    try:
        supabase.table("search_history").insert({
            "user_id": telegram_id, "vehicle_number": vehicle_number, 
            "status": status, "credits_deducted": credits_deducted
        }).execute()
    except Exception as e:
        print(f"DB Error log_search: {e}")
