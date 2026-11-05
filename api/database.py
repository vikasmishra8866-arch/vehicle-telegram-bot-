from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timezone, timedelta

_supabase_client = None

def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client

def get_or_create_user(telegram_id: int, username: str, first_name: str):
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        if not res.data:
            new_user = {"telegram_id": telegram_id, "username": username, "first_name": first_name, "wallet_balance": 1}
            supabase.table("users").insert(new_user).execute()
            supabase.table("wallet_transactions").insert({
                "user_id": telegram_id, "type": "credit", "amount": 1,
                "previous_balance": 0, "new_balance": 1, "reason": "Free Demo Credit"
            }).execute()
            return new_user
        return res.data[0]
    except Exception as e:
        print(f"❌ DB Error get_or_create_user: {e}")
        return None

def check_cooldown(telegram_id: int):
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("last_search_at").eq("telegram_id", telegram_id).execute()
        if res.data and res.data[0].get("last_search_at"):
            last_search = datetime.fromisoformat(res.data[0]["last_search_at"].replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - last_search).total_seconds() < 5:
                return False
        supabase.table("users").update({"last_search_at": datetime.now(timezone.utc).isoformat()}).eq("telegram_id", telegram_id).execute()
        return True
    except Exception as e:
        print(f"❌ DB Error check_cooldown: {e}")
        return True 

def get_active_subscription(user_id: int):
    try:
        supabase = get_supabase()
        res = supabase.table("subscriptions").select("*").eq("user_id", user_id).eq("status", "active").gte("expiry_date", datetime.now(timezone.utc).isoformat()).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"❌ DB Error get_sub: {e}")
        return None

def deduct_credit(telegram_id: int):
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("wallet_balance").eq("telegram_id", telegram_id).execute()
        if res.data and res.data[0]["wallet_balance"] >= 1:
            current_bal = res.data[0]["wallet_balance"]
            new_bal = current_bal - 1
            supabase.table("users").update({"wallet_balance": new_bal}).eq("telegram_id", telegram_id).execute()
            supabase.table("wallet_transactions").insert({
                "user_id": telegram_id, "type": "debit", "amount": 1,
                "previous_balance": current_bal, "new_balance": new_bal, "reason": "Vehicle Search"
            }).execute()
            return True
        return False
    except Exception as e:
        print(f"❌ DB Error deduct_credit: {e}")
        return False

def log_search(telegram_id: int, vehicle_number: str, status: str, credits_deducted: int):
    try:
        get_supabase().table("search_history").insert({
            "user_id": telegram_id, "vehicle_number": vehicle_number, 
            "status": status, "credits_deducted": credits_deducted
        }).execute()
    except Exception as e:
        print(f"❌ DB Error log_search: {e}")

def create_payment_order(user_id: int, plan: str, amount: int, credits: int):
    try:
        supabase = get_supabase()
        res = supabase.table("payment_orders").insert({
            "user_id": user_id, "plan_name": plan, "amount": amount, "credits": credits, "status": "pending"
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        print(f"❌ DB Error creating order: {e}") 
        return None

def update_order_status(order_id: str, status: str):
    try:
        supabase = get_supabase()
        supabase.table("payment_orders").update({"status": status}).eq("id", order_id).execute()
        return True
    except Exception as e:
        print(f"❌ DB Error updating order: {e}")
        return False

def approve_payment(order_id: str, admin_id: int):
    try:
        supabase = get_supabase()
        res = supabase.table("payment_orders").select("*").eq("id", order_id).eq("status", "verification").execute()
        if not res.data: return False, "Order pending verification nahi hai."
        
        order = res.data[0]
        user_id = order["user_id"]
        credits = order["credits"]

        user_res = supabase.table("users").select("wallet_balance").eq("telegram_id", user_id).execute()
        if not user_res.data: return False, "User not found."
        
        current_bal = user_res.data[0]["wallet_balance"]
        new_bal = current_bal + credits
        
        supabase.table("users").update({"wallet_balance": new_bal}).eq("telegram_id", user_id).execute()
        supabase.table("wallet_transactions").insert({
            "user_id": user_id, "type": "credit", "amount": credits,
            "previous_balance": current_bal, "new_balance": new_bal, "reason": f"Payment Approved by Admin {admin_id}"
        }).execute()
        supabase.table("payment_orders").update({"status": "approved"}).eq("id", order_id).execute()
        return True, new_bal
    except Exception as e:
        print(f"❌ DB Error approving payment: {e}")
        return False, str(e)

def create_unlimited_request(user_id: int, days: int):
    try:
        supabase = get_supabase()
        res = supabase.table("unlimited_requests").insert({
            "user_id": user_id, "duration_days": days, "status": "pending"
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        print(f"❌ DB Error creating req: {e}")
        return None

def grant_unlimited_access(user_id: int, days: int, admin_id: int):
    try:
        supabase = get_supabase()
        expiry = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
        supabase.table("subscriptions").insert({
            "user_id": user_id, "plan_name": f"{days} Days Unlimited", "duration_days": days,
            "status": "active", "expiry_date": expiry, "granted_by": admin_id
        }).execute()
        return True
    except Exception as e:
        print(f"❌ Error granting sub: {e}")
        return False
