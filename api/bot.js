import { waitUntil } from "@vercel/functions";

export default async function handler(req, res) {
  // सिर्फ POST रिक्वेस्ट स्वीकार करें
  if (req.method !== "POST") {
    return res.status(200).json({ ok: true, message: "Bot is alive" });
  }

  // टेलीग्राम को तुरंत 200 OK भेजें
  res.status(200).json({ ok: true });

  // बॉडी को पढ़ें
  let body = '';
  req.on('data', chunk => { body += chunk.toString(); });
  
  req.on('end', () => {
    try {
      const update = JSON.parse(body);
      console.log("Received update:", JSON.stringify(update));
      
      // बैकग्राउंड में प्रोसेस करें
      waitUntil(processUpdate(update));
    } catch (e) {
      console.error("Failed to parse body:", e);
    }
  });
}

async function processUpdate(update) {
  try {
    console.log("Processing update...");
    const message = update.message;
    if (!message || !message.text) return;

    const chatId = message.chat.id;
    const raw = message.text.trim();
    console.log(`Message from ${chatId}: ${raw}`);

    // ... (यहाँ से आगे का कोड पहले जैसा ही रहेगा: /start कमांड, व्हीकल नंबर चेक करना, API कॉल करना, आदि।) ...
    // उदाहरण के लिए:
    if (raw === "/start") {
       await sendMessage(chatId, "🚗 <b>Vehicle Lookup Bot</b>\n\nKisi bhi vehicle ka registration number bhejein.\nExample: <code>GJ05HG7801</code>");
       return;
    }

    const regNo = raw.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
    if (regNo.length < 6 || regNo.length > 12) {
      await sendMessage(chatId, "❌ Invalid format. Bhejein jaise: <code>GJ05HG7801</code>");
      return;
    }

    const loadingMsgId = await sendMessage(chatId, "🔍 Fetching vehicle details...\n<i>(ye 8-17 second le sakta hai)</i>");

    const url = `https://hideme.eu.org/lookup?api=mvahan&key=${process.env.API_KEY}&number=${encodeURIComponent(regNo)}`;
    let data;
    try {
      const apiRes = await fetch(url, { signal: AbortSignal.timeout(25000) });
      data = await apiRes.json();
    } catch (err) {
      await editMessage(chatId, loadingMsgId, "⏱️ Server ne time out kar diya. Thodi der baad try karein.");
      return;
    }

    if (!data || !data.success || !data.vehicle) {
      await editMessage(chatId, loadingMsgId, "❌ Vehicle not found. Number check karke dobara try karein.");
      return;
    }

    const text = formatVehicle(data.vehicle);
    await editMessage(chatId, loadingMsgId, text);

  } catch (err) {
    console.error("Error in processUpdate:", err);
  }
}

// sendMessage, editMessage, formatVehicle फंक्शन्स पहले जैसे ही रहेंगे
