from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timezone

# ✅ Vercel के लिए Lazy Initialization (सर्वर स्टार्ट होते ही क्रैश न हो)
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
        # 1. चेक करें कि यूजर पहले से है या नहीं
        res = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        
        if not res.data:
            # 2. अगर नया यूजर है, तो उसे 1 फ्री क्रेडिट के साथ बनाएं
            new_user = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "wallet_balance": 1, # 1 Free Credit
            }
            supabase.table("users").insert(new_user).execute()
            
            # 3. ट्रांजैक्शन हिस्ट्री में लॉग करें
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
    except Exception as e:
        print(f"❌ DB Error in get_or_create_user: {e}")
        return None

def check_cooldown(telegram_id: int):
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("last_search_at").eq("telegram_id", telegram_id).execute()
        
        if res.data and res.data[0].get("last_search_at"):
            last_search_str = res.data[0]["last_search_at"]
            # समय को UTC में बदलें
            last_search = datetime.fromisoformat(last_search_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            
            # अगर 5 सेकंड से कम समय हुआ है, तो रोकें
            if (now - last_search).total_seconds() < 5:
                return False
                
        # अगर टाइम पूरा हो गया है, तो टाइम अपडेट करें और आगे बढ़ने दें
        supabase.table("users").update({
            "last_search_at": datetime.now(timezone.utc).isoformat()
        }).eq("telegram_id", telegram_id).execute()
        
        return True
    except Exception as e:
        print(f"❌ DB Error in check_cooldown: {e}")
        return True # अगर DB में दिक्कत हो, तो यूजर को ब्लॉक न करें

def deduct_credit(telegram_id: int):
    try:
        supabase = get_supabase()
        # 1. करंट बैलेंस चेक करें
        res = supabase.table("users").select("wallet_balance").eq("telegram_id", telegram_id).execute()
        
        if res.data:
            current_bal = res.data[0]["wallet_balance"]
            
            # 2. अगर बैलेंस 1 या ज्यादा है, तो काटें
            if current_bal >= 1:
                new_bal = current_bal - 1
                supabase.table("users").update({"wallet_balance": new_bal}).eq("telegram_id", telegram_id).execute()
                
                # 3. ट्रांजैक्शन हिस्ट्री में लॉग करें
                supabase.table("wallet_transactions").insert({
                    "user_id": telegram_id, 
                    "type": "debit", 
                    "amount": 1,
                    "previous_balance": current_bal, 
                    "new_balance": new_bal, 
                    "reason": "Vehicle Search"
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
            "user_id": telegram_id, 
            "vehicle_number": vehicle_number, 
            "status": status, 
            "credits_deducted": credits_deducted
        }).execute()
    except Exception as e:
        print(f"❌ DB Error in log_search: {e}")
