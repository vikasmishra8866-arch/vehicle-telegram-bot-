from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timezone

# Vercel के लिए Lazy Initialization
_supabase_client = None

def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("❌ Supabase URL या Key मिसिंग है! Vercel Environment Variables चेक करें।")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client

def get_or_create_user(telegram_id: int, username: str, first_name: str):
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        
        if not res.data:
            # नया यूजर (1 फ्री क्रेडिट)
            new_user = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "wallet_balance": 1,
            }
            supabase.table("users").insert(new_user).execute()
            supabase.table("wallet_transactions").insert({
                "user_id": telegram_id, "type": "credit", "amount": 1,
                "previous_balance": 0, "new_balance": 1, "reason": "Free Demo Credit"
            }).execute()
            return new_user
            
        return res.data[0]
    except Exception as e:
        print(f"❌ DB Error in get_or_create_user: {e}")
        return None

def check_cooldown(telegram_id: int):
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("last_search_at").eq("telegram_id", telegram_id).execute()
        
        if res.data and res.data[0].get("last_search_at"):
            last_search = datetime.fromisoformat(res.data[0]["last_search_at"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if (now - last_search).total_seconds() < 5:
                return False
                
        supabase.table("users").update({"last_search_at": datetime.now(timezone.utc).isoformat()}).eq("telegram_id", telegram_id).execute()
        return True
    except Exception as e:
        print(f"❌ DB Error in check_cooldown: {e}")
        return True 

def deduct_credit(telegram_id: int):
    try:
        supabase = get_supabase()
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
        print(f"❌ DB Error in deduct_credit: {e}")
        return False

def log_search(telegram_id: int, vehicle_number: str, status: str, credits_deducted: int):
    try:
        supabase = get_supabase()
        supabase.table("search_history").insert({
            "user_id": telegram_id, "vehicle_number": vehicle_number, 
            "status": status, "credits_deducted": credits_deducted
        }).execute()
    except Exception as e:
        print(f"❌ DB Error in log_search: {e}")

def add_credits_admin(target_id: int, amount: int, reason="Admin Manual Add"):
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("wallet_balance").eq("telegram_id", target_id).execute()
        if res.data:
            current_bal = res.data[0]["wallet_balance"]
            new_bal = current_bal + amount
            supabase.table("users").update({"wallet_balance": new_bal}).eq("telegram_id", target_id).execute()
            
            supabase.table("wallet_transactions").insert({
                "user_id": target_id, "type": "admin_add", "amount": amount,
                "previous_balance": current_bal, "new_balance": new_bal, "reason": reason
            }).execute()
            return True, new_bal
        return False, 0
    except Exception as e:
        print(f"❌ DB Error in add_credits_admin: {e}")
        return False, 0

def get_user_info(target_id: int):
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("*").eq("telegram_id", target_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        return None
        # (पुराने कोड के नीचे ये नए फंक्शन्स जोड़ें)

def get_active_subscription(user_id: int):
    try:
        supabase = get_supabase()
        # चेक करें कि क्या एक्टिव सब्सक्रिप्शन है और उसकी एक्सपायरी डेट फ्यूचर में है
        res = supabase.table("subscriptions").select("*").eq("user_id", user_id).eq("status", "active").gte("expiry_date", datetime.now(timezone.utc).isoformat()).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"DB Error get_sub: {e}")
        return None

def create_payment_order(user_id: int, plan: str, amount: int, credits: int):
    try:
        supabase = get_supabase()
        res = supabase.table("payment_orders").insert({
            "user_id": user_id, "plan_name": plan, "amount": amount, "credits": credits, "status": "pending"
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        return None
