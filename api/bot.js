import { waitUntil } from "@vercel/functions";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(200).json({ ok: true, message: "Bot is running perfectly!" });
  }

  res.status(200).json({ ok: true });
  const update = req.body;
  
  if (!update) return;
  waitUntil(processUpdate(update));
}

async function processUpdate(update) {
  try {
    const message = update.message;
    if (!message || !message.text) return;

    const chatId = message.chat.id;
    const raw = message.text.trim();

    if (raw.startsWith("/start")) {
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
      console.error("API Error:", err);
      await editMessage(chatId, loadingMsgId, "⏱️ Server ne time out kar diya. Thodi der baad try karein.");
      return;
    }

    if (!data || !data.success || !data.vehicle) {
      await editMessage(chatId, loadingMsgId, "❌ Vehicle not found. Number check karke dobara try karein.");
      return;
    }

    // 🚀 यहाँ से JSON का काम शुरू होता है 🚀
    
    // पूरे डेटा को सुंदर JSON स्ट्रिंग में बदलें
    const fullJsonString = JSON.stringify(data, null, 2);

    // Telegram में मैसेज की लिमिट 4096 अक्षरों की होती है
    let replyText = "";
    if (fullJsonString.length > 4000) {
        // अगर डेटा बहुत बड़ा है, तो उसे काट दें (ताकि बॉट क्रैश न हो)
        replyText = `<pre><code class="language-json">${fullJsonString.substring(0, 3900)}...</code></pre>\n<i>(JSON bahut lamba hai, isliye cut kar diya gaya hai)</i>`;
    } else {
        // पूरा JSON कोड ब्लॉक की तरह भेजें
        replyText = `<pre><code class="language-json">${fullJsonString}</code></pre>`;
    }

    await editMessage(chatId, loadingMsgId, replyText);

  } catch (err) {
    console.error("Error in processUpdate:", err);
  }
}

// Telegram API कॉल करने के लिए हेल्पर
async function sendMessage(chatId, text) {
  const url = `https://api.telegram.org/bot${process.env.BOT_TOKEN}/sendMessage`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: "HTML" }),
  });
  const data = await res.json();
  if (!data.ok) console.error("Telegram Error:", data);
  return data.result?.message_id;
}

async function editMessage(chatId, messageId, text) {
  const url = `https://api.telegram.org/bot${process.env.BOT_TOKEN}/editMessageText`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, message_id: messageId, text, parse_mode: "HTML" }),
  });
  const data = await res.json();
  if (!data.ok) console.error("Telegram Edit Error:", data);
}
