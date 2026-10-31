// api/bot.js
import { Bot, webhookCallback } from "grammy";

const bot = new Bot(process.env.BOT_TOKEN);

bot.catch((err) => {
  console.error("Bot error:", err);
});

bot.command("start", async (ctx) => {
  await ctx.reply(
    "🚗 <b>Vehicle Lookup Bot</b>\n\n" +
    "Kisi bhi vehicle ka registration number bhejein (jaise <code>GJ05HG7801</code>) " +
    "aur main aapko poori details dikhaunga.",
    { parse_mode: "HTML" }
  );
});

bot.on("message:text", async (ctx) => {
  const raw = ctx.message.text.trim();
  
  // Skip commands
  if (raw.startsWith("/")) return;
  
  // Clean and format
  const regNo = raw.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
  
  // Basic validation
  if (!/^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$/.test(regNo) && regNo.length < 6) {
    return ctx.reply("❌ Invalid format. Bhejein jaise: <code>GJ05HG7801</code>", { parse_mode: "HTML" });
  }
  
  const loading = await ctx.reply("🔍 Fetching details...");
  
  try {
    const url = `https://hideme.eu.org/lookup?api=mvahan&key=${process.env.API_KEY}&number=${encodeURIComponent(regNo)}`;
    const res = await fetch(url);
    const data = await res.json();
    
    if (!data.success || !data.vehicle) {
      await ctx.api.editMessageText(ctx.chat.id, loading.message_id, "❌ Vehicle not found. Number check karein.");
      return;
    }
    
    const v = data.vehicle;
    const text = formatVehicle(v);
    
    await ctx.api.editMessageText(ctx.chat.id, loading.message_id, text, { 
      parse_mode: "HTML",
      disable_web_page_preview: true 
    });
  } catch (e) {
    console.error("Fetch error:", e);
    await ctx.api.editMessageText(ctx.chat.id, loading.message_id, "❌ Server error. Please try again.");
  }
});

function formatVehicle(v) {
  const rows = [];
  const add = (label, value) => {
    if (value && value !== "null" && value !== "" && value !== "NA") {
      rows.push(`<b>${label}:</b> ${value}`);
    }
  };
  
  add("Registration No", v.registration_no);
  add("Owner", v.owner);
  add("Father's Name", v.father_name);
  add("Make", v.make);
  add("Model", v.model);
  add("Variant", v.variant);
  add("Vehicle Class", v.vehicle_class);
  add("Vehicle Category", v.vehicle_category);
  add("Fuel", v.fuel);
  add("Color", v.color);
  add("Body Type", v.body_type);
  add("Engine", v.engine);
  add("Chassis", v.chassis);
  add("Cubic Capacity", v.cubic_capacity);
  add("Seating Capacity", v.seating_capacity);
  add("Registration Date", v.registration_date);
  add("RTO", v.rto);
  add("City", v.city);
  add("Insurance Company", v.insurance_company);
  add("Insurance Policy No", v.insurance_policy_no);
  add("Insurance Upto", v.insurance_upto);
  add("PUC No", v.puc_no);
  add("PUC Upto", v.puc_upto);
  add("Fitness Upto", v.fit_upto);
  add("Tax Upto", v.tax_upto);
  add("Financier", v.financier);
  add("Address", v.address);
  
  return `🚗 <b>Vehicle Details</b>\n\n${rows.join("\n")}`;
}

export default webhookCallback(bot, "vercel");
