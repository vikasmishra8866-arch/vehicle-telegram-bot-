import { Bot, webhookCallback } from "grammy";

// Bot initialize करें (TOKEN environment variable से आएगा)
const bot = new Bot(process.env.BOT_TOKEN);

// ---------- /start कमांड ----------
bot.command("start", async (ctx) => {
  await ctx.reply(
    "🚗 <b>Vehicle Lookup Bot</b>\n\n" +
      "Kisi bhi vehicle ka registration number bhejein.\n" +
      "Example: <code>GJ05HG7801</code>\n\n" +
      "Main aapko poori details dikhaunga.",
    { parse_mode: "HTML" }
  );
});

// ---------- हर टेक्स्ट मैसेज पर ----------
bot.on("message:text", async (ctx) => {
  const raw = ctx.message.text.trim();

  // अगर कोई command है तो छोड़ दें
  if (raw.startsWith("/")) return;

  // Vehicle number clean + uppercase करें
  const regNo = raw.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();

  // Validation (कम से कम 6 अक्षर, ज़्यादा से ज़्यादा 12)
  if (regNo.length < 6 || regNo.length > 12) {
    return ctx.reply(
      "❌ Invalid format. Bhejein jaise: <code>GJ05HG7801</code>",
      { parse_mode: "HTML" }
    );
  }

  // "Fetching..." message
  const loading = await ctx.reply("🔍 Fetching vehicle details...");

  try {
    // API call
    const url = `https://hideme.eu.org/lookup?api=mvahan&key=${process.env.API_KEY}&number=${encodeURIComponent(regNo)}`;
    const res = await fetch(url);
    const data = await res.json();

    // अगर data नहीं मिला
    if (!data.success || !data.vehicle) {
      return ctx.api.editMessageText(
        ctx.chat.id,
        loading.message_id,
        "❌ Vehicle not found. Number check karke dobara try karein."
      );
    }

    // Format और reply
    const text = formatVehicle(data.vehicle);
    await ctx.api.editMessageText(ctx.chat.id, loading.message_id, text, {
      parse_mode: "HTML",
      disable_web_page_preview: true,
    });
  } catch (err) {
    console.error("API Error:", err);
    await ctx.api.editMessageText(
      ctx.chat.id,
      loading.message_id,
      "❌ Server error. Thodi der baad try karein."
    );
  }
});

// ---------- Helper: response को सुंदर बनाना ----------
function formatVehicle(v) {
  const rows = [];
  const add = (label, value) => {
    if (value && value !== "null" && value !== "" && value !== "NA") {
      rows.push(`<b>${label}:</b> ${value}`);
    }
  };

  // 🚗 Basic Info
  rows.push("🚗 <b>VEHICLE DETAILS</b>");
  rows.push("━━━━━━━━━━━━━━━━━━");
  add("Registration", v.registration_no);
  add("Make", v.make);
  add("Model", v.model);
  add("Variant", v.variant);
  add("Fuel", v.fuel);
  add("Color", v.color);
  add("Body Type", v.body_type);
  add("Class", v.vehicle_class);
  add("Category", v.vehicle_category);

  rows.push("");
  rows.push("👤 <b>OWNER INFO</b>");
  rows.push("━━━━━━━━━━━━━━━━━━");
  add("Owner", v.owner);
  add("Father's Name", v.father_name);
  add("Address", v.address);
  add("City", v.city);
  add("Financier", v.financier);

  rows.push("");
  rows.push("⚙️ <b>TECHNICAL</b>");
  rows.push("━━━━━━━━━━━━━━━━━━");
  add("Engine No", v.engine);
  add("Chassis No", v.chassis);
  add("Chassis (Last 5)", v.chassis_last5);
  add("Cubic Capacity", v.cubic_capacity ? `${v.cubic_capacity} CC` : null);
  add("Seating", v.seating_capacity);

  rows.push("");
  rows.push("📋 <b>REGISTRATION</b>");
  rows.push("━━━━━━━━━━━━━━━━━━");
  add("Reg. Date", v.registration_date);
  add("RTO", v.rto);
  add("Fitness Upto", v.fit_upto);
  add("Tax Upto", v.tax_upto);

  rows.push("");
  rows.push("🛡️ <b>INSURANCE & PUC</b>");
  rows.push("━━━━━━━━━━━━━━━━━━");
  add("Insurance Co.", v.insurance_company);
  add("Policy No.", v.insurance_policy_no);
  add("Insurance Upto", v.insurance_upto);
  add("PUC No.", v.puc_no);
  add("PUC Upto", v.puc_upto);

  return rows.join("\n");
}

// ---------- Vercel के लिए handler ----------
export default webhookCallback(bot, "vercel");
