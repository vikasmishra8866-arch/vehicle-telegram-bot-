def format_vehicle_dossier(data, reg_no):
    v = data.get("vehicle", {})
    
    def valid(val):
        if val is None: return False
        s = str(val).strip().lower()
        if s in ["", "null", "na", "none", "0", "0.0", "undefined"]: return False
        return True
        
    def get_val(key, default="None"):
        val = v.get(key)
        return val if valid(val) else default

    # हेडर
    text = "👑 <b>VIP VEHICLE VERIFICATION</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # मुख्य जानकारी
    text += f"🚗 <b>Maker:</b> {get_val('make')}\n"
    variant = v.get('variant') or v.get('model')
    text += f"🚚 <b>Variant:</b> {variant if valid(variant) else 'None'}\n"
    text += f"🔢 <b>Number:</b> <b>{reg_no}</b>\n\n"

    # ओनर जानकारी
    text += "👤 <b>Registered Owner</b>\n"
    owner = get_val('owner')
    city = v.get('city') or v.get('rto')
    city_text = f" ({city})" if valid(city) else ""
    text += f"└ <b>{owner}</b>{city_text}\n\n"

    # व्हीकल प्रोफाइल
    text += "📊 <b>Vehicle Profile</b>\n"
    
    v_class = v.get('vehicle_class') or v.get('body_type')
    if valid(v_class): text += f"├ <b>Class:</b> {v_class}\n"
    if valid(v.get('fuel')): text += f"├ <b>Fuel:</b> {v.get('fuel')}\n"
    if valid(v.get('registration_date')): text += f"├ <b>Reg Date:</b> {v.get('registration_date')}\n"
    
    financier = get_val('financier', "None")
    text += f"└ <b>Financier:</b> {financier}\n\n"

    # आइडेंटिफिकेशन नंबर
    text += "🛠️ <b>Identification Numbers</b>\n"
    if valid(v.get('engine')): text += f"├ <b>Engine:</b> <code>{v.get('engine')}</code>\n"
    if valid(v.get('chassis')): text += f"└ <b>Chassis:</b> <code>{v.get('chassis')}</code>\n\n"

    # कांटेक्ट और एड्रेस
    mobile = data.get("mobile")
    if valid(mobile):
        text += f"📞 <b>Owner Contact:</b> <code>{mobile}</code> ✅\n"
    else:
        text += f"📞 <b>Owner Contact:</b> ❌ <i>Not Found</i>\n"
        text += f"🔄 <i>Kripya ishi gaadi number (<code>{reg_no}</code>) ko dobara search karein.</i>\n"

    if valid(v.get('address')):
        text += f"🏠 <b>Permit/Address:</b> {v.get('address')}\n"

    return text
