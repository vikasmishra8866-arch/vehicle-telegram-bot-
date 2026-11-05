import qrcode
from io import BytesIO
from aiogram.types import BufferedInputFile
from .config import UPI_ID

def generate_upi_qr(amount: int, credits: int):
    upi_uri = f"upi://pay?pa={UPI_ID}&am={amount}&pn=VehicleDesk&tn=Topup_{credits}_Credits"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return BufferedInputFile(bio.read(), filename="qr.png")

def format_vehicle_tree(reg_no, v, data):
    def valid(val): return val and str(val).strip().lower() not in ["", "null", "na", "none", "0"]
    text = f"🧭 <b>VEHICLE JOURNEY</b> — {reg_no}\n────────────────────────────────────────────\n│\n"
    text += "├─ 🚘 <b>VEHICLE IDENTITY</b>\n"
    if valid(v.get("make")): text += f"│   ├─ Make      : {v.get('make')}\n"
    if valid(v.get("variant")): text += f"│   ├─ Variant   : {v.get('variant')}\n"
    if valid(v.get("fuel")): text += f"│   ├─ Fuel      : {v.get('fuel')}\n"
    if valid(v.get("color")): text += f"│   ├─ Color     : {v.get('color')}\n"
    if valid(v.get("body_type")): text += f"│   ├─ Body Type : {v.get('body_type')}\n"
    if valid(v.get("vehicle_class")): text += f"│   └─ Class     : {v.get('vehicle_class')}\n│\n"
    text += "├─ 👤 <b>OWNER DETAILS</b>\n"
    if valid(v.get("owner")): text += f"│   ├─ Owner     : {v.get('owner')}\n"
    if valid(data.get("mobile")): text += f"│   ├─ Mobile    : {data.get('mobile')}\n"
    text += f"│   └─ Found     : {'Yes' if data.get('mobile_found') else 'No'}\n│\n"
    text += "├─ 🔑 <b>MACHINE DETAILS</b>\n"
    if valid(v.get("chassis")): text += f"│   ├─ Chassis   : {v.get('chassis')}\n"
    if valid(v.get("engine")): text += f"│   └─ Engine    : {v.get('engine')}\n│\n"
    text += "├─ 📅 <b>REGISTRATION</b>\n"
    if valid(v.get("registration_date")): text += f"│   ├─ Date      : {v.get('registration_date')}\n"
    text += f"│   ├─ Reg No    : {reg_no}\n"
    if valid(v.get("rto")): text += f"│   └─ RTO       : {v.get('rto')}\n│\n"
    if valid(v.get("insurance_company")): text += f"├─ 🛡️ <b>INSURANCE</b>\n│   └─ Company   : {v.get('insurance_company')}\n│\n"
    text += "────────────────────────────────────────────\n⚠️🚨 <b>IMPORTANT NOTE</b> 🚨⚠️\n🔍 Ye details sirf AUDIT purpose ke liye hain.\n"
    return text
