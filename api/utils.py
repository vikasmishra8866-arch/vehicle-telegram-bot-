def format_vehicle_dossier(data, reg_no):
    v = data.get("vehicle", {})
    
    def valid(val):
        if val is None: return False
        s = str(val).strip().lower()
        if s in ["", "null", "na", "none", "0", "0.0", "undefined"]: return False
        return True

    text = "⚡ <b>VEHICLE DOSSIER // QUICK INFO</b>\n\n"
    
    # 🔹 Reg. No
    if valid(reg_no):
        text += f"🔹 <b>Reg. No:</b> <b>{reg_no}</b>\n"
        
    # 🔹 Vehicle (Make & Category)
    make = v.get("make")
    v_cat = v.get("vehicle_category") or v.get("vehicle_class")
    if valid(make):
        v_info = f"{make}"
        if valid(v_cat): v_info += f" ({v_cat})"
        text += f"🔹 <b>Vehicle:</b> {v_info}\n"

    # 🔹 Owner
    if valid(v.get("owner")):
        text += f"🔹 <b>Owner:</b> {v.get('owner')}\n"

    # 🔹 Fuel & Color
    fuel = v.get("fuel")
    color = v.get("color")
    fuel_color = ""
    if valid(fuel): fuel_color += f"{fuel} ⛽"
    if valid(color): 
        if fuel_color: fuel_color += " | "
        fuel_color += f"Color: {color} 🔴"
    if fuel_color:
        text += f"🔹 <b>Fuel:</b> {fuel_color}\n"

    # 📋 REGISTRATION & SPECS
    text += "\n📋 <b>REGISTRATION &amp; SPECS</b>\n"
    lines = []
    
    if valid(v.get("registration_date")): lines.append(f"├ 📅 Reg Date: {v.get('registration_date')}")
    if valid(v.get("rto")): lines.append(f"├ 🏛️ RTO: {v.get('rto')}")
    if valid(v.get("engine")): lines.append(f"├ ⚙️ Engine: <code>{v.get('engine')}</code>")
    if valid(v.get("chassis")): lines.append(f"├ 🔧 Chassis: <code>{v.get('chassis')}</code>")
    
    # ट्री (Tree) फॉर्मेटिंग को सही करें (आखिरी वाले को └ बनाएं)
    if lines:
        for i in range(len(lines) - 1):
            lines[i] = lines[i].replace("└", "├")
        lines[-1] = lines[-1].replace("├", "└")
        text += "\n".join(lines) + "\n"

    # 📍 Address
    if valid(v.get("address")):
        text += f"\n📍 <b>Address:</b> {v.get('address')}\n"
        
    # 📞 Mobile
    if valid(data.get("mobile")):
        text += f"📞 <b>Mobile:</b> <code>{data.get('mobile')}</code>\n"

    return text
