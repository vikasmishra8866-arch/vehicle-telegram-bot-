import { waitUntil } from "@vercel/functions";

export default async function handler(req, res) {
  // 1. सुनिश्चित करें कि यह POST रिक्वेस्ट है
  if (req.method !== "POST") {
    return res.status(200).json({ ok: true, message: "Bot is running perfectly!" });
  }

  // 2. Telegram को तुरंत 200 OK भेजें
  res.status(200).json({ ok: true });

  // 3. Vercel द्वारा पार्स किए गए बॉडी को पकड़ें
  const update = req.body;
  
  if (!update) {
    console.log("❌ No body received from Telegram.");
    return;
  }

  // 4. बैकग्राउंड में प्रोसेसिंग शुरू करें
  waitUntil(processUpdate(update));
}

async function processUpdate(update) {
  try {
    console.log("✅ नया अपडेट मिला:", JSON.stringify(update)); // यह लॉग्स में दिखेगा

    const message = update.message;
    if (!message || !message.text) {
      console.log("⚠️ मैसेज या टेक्स्ट नहीं है।");
      return;
    }

    const chatId = message.chat.id;
    const raw = message.text.trim();
    console.log(`💬 मैसेज: "${raw}" | Chat ID: ${chatId}`);

    // /start या किसी भी कमांड को हैंडल करें
    if (raw.startsWith("/start")) {
       console.log("🚀 /start कमांड मिला, रिप्लाई भेज रहे हैं...");
       await sendMessage(chatId, "🚗 <b>Vehicle Lookup Bot</b>\n\nKisi bhi vehicle ka registration number bhejein.\nExample: <code>GJ05HG7801</code>");
       return;
    }

    // व्हीकल नंबर चेक
    const regNo = raw.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
    if (regNo.length < 6 || regNo.length > 12) {
      console.log("❌ गलत फॉर्मेट");
      await sendMessage(chatId, "❌ Invalid format. Bhejein jaise: <code>GJ05HG7801</code>");
      return;
    }

    // लोडिंग मैसेज
    console.log("⏳ लोडिंग मैसेज भेज रहे हैं...");
    const loadingMsgId = await sendMessage(chatId, "🔍 Fetching vehicle details...\n<i>(ye 8-17 second le sakta hai)</i>");

    // API कॉल
    const url = `https://hideme.eu.org/lookup?api=mvahan&key=${process.env.API_KEY}&number=${encodeURIComponent(regNo)}`;
    let data;
    try {
      console.log("📡 API कॉल कर रहे हैं...");
      const apiRes = await fetch(url, { signal: AbortSignal.timeout(25000) });
      data = await apiRes.json();
      console.log("✅ API से डेटा आ गया");
    } catch (err) {
      console.error("❌ API Error:", err);
      await editMessage(chatId, loadingMsgId, "⏱️ Server ne time out kar diya. Thodi der baad try karein.");
      return;
    }

    if (!data || !data.success || !data.vehicle) {
      console.log("❌ डेटा नहीं मिला या success: false है");
      await editMessage(chatId, loadingMsgId, "❌ Vehicle not found. Number check karke dobara try karein.");
      return;
    }

    const text = formatVehicle(data.vehicle);
    console.log("📝 रिप्लाई भेज रहे हैं...");
    await editMessage(chatId, loadingMsgId, text);
    console.log("🎉 रिप्लाई सफलतापूर्वक भेज दी गई!");

  } catch (err) {
    console.error("🔥 processUpdate में एरर:", err);
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
  if (!data.ok) console.error("❌ Telegram SendMessage Error:", data);
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
  if (!data.ok) console.error("❌ Telegram EditMessage Error:", data);
}

function formatVehicle(v) {
  return `🚗 <b>VEHICLE DETAILS</b>\nReg No: ${v.registration_no || 'N/A'}\nOwner: ${v.owner || 'N/A'}\nMake: ${v.make || 'N/A'}\nModel: ${v.model || 'N/A'}`;
}
