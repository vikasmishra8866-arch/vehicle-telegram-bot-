// api/webhook.js
import { Bot, webhookCallback } from "grammy";

const bot = new Bot(process.env.BOT_TOKEN);

bot.command("start", (ctx) => {
  ctx.reply("Namaste! Vehicle number bhejein jaise: GJ05HG7801");
});

bot.on("message:text", async (ctx) => {
  const text = ctx.message.text.trim().toUpperCase().replace(/[^A-Z0-9]/g, "");
  if (!/^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$/.test(text)) {
    return ctx.reply("Valid vehicle number bhejein jaise: GJ05HG7801");
  }
  
  const loadingMsg = await ctx.reply("🔍 Fetching details...");
  
  try {
    const res = await fetch(`https://hideme.eu.org/lookup?api=mvahan&key=${process.env.API_KEY}&number=${text}`);
    const data = await res.json();
    
    if (!data.success || !data.vehicle) {
      return ctx.api.editMessageText(ctx.chat.id, loadingMsg.message_id, "❌ Vehicle not found");
    }
    
    const v = data.vehicle;
    const msg = formatVehicle(v);
    await ctx.api.editMessageText(ctx.chat.id, loadingMsg.message_id, msg, { parse_mode: "HTML" });
  } catch (e) {
    await ctx.api.editMessageText(ctx.chat.id, loadingMsg.message_id, "❌ API error, try again");
  }
});

export default webhookCallback(bot, "https");
