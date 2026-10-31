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

    const formattedText = formatVehicle(data);
    await editMessage(chatId, loadingMsgId, formattedText);

  } catch (err) {
    console.error("Error in processUpdate:", err);
  }
}

// ---------- मुख्य फॉर्मेटिंग फंक्शन ----------
function formatVehicle(data) {
  const v = data.vehicle || {};
  const regNo = data.reg_no || v.registration_no || "UNKNOWN";
  
  // नल, NA, और खाली डेटा को पहचानने के लिए
  const isValid = (val) => {
    if (val === null || val === undefined || val === '' || val === 'null' || val === 'NA' || val === '0' || val === 0) return false;
    return true;
  };

  // HTML सेफ्टी के लिए (ताकि API का डेटा मैसेज को ब्रेक न करे)
  const escapeHTML = (str) => {
    if (str === null || str === undefined) return "";
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  };

  // लंबे एड्रेस को 2-3 लाइन में तोड़ने के लिए
  const wrapText = (text, maxLength = 35) => {
    if (!text) return "";
    const words = text.split(' ');
    let lines = [];
    let currentLine = "";
    words.forEach(word => {
      if ((currentLine + word).length > maxLength) {
        lines.push(currentLine.trim());
        currentLine = word + " ";
      } else {
        currentLine += word + " ";
      }
    });
    if (currentLine.trim()) lines.push(currentLine.trim());
    return lines.join('\n');
  };

  // ट्री स्ट्रक्चर (├─ └─) बनाने के लिए
  const formatSection = (title, items) => {
    const validItems = items.filter(i => isValid(i.value));
    if (validItems.length === 0) return "";

    let out = `├─ ${title}\n`;
    validItems.forEach((item, idx) => {
      const isLast = idx === validItems.length - 1;
      const branch = isLast ? "└─" : "├─";
      
      const safeValue = escapeHTML(item.value);

      if (item.label) {
        const paddedLabel = item.label.padEnd(10, ' ');
        out += `│   ${branch} ${paddedLabel}: ${safeValue}\n`;
      } else {
        const lines = safeValue.split('\n');
        out += `│   ${branch} ${lines[0]}\n`;
        for (let i = 1; i < lines.length; i++) {
          out += `│      ${lines[i]}\n`;
        }
      }
    });
    return out;
  };

  const sections = [];

  // 1. व्हीकल आइडेंटिटी
  const identityItems = [
    { label: "Make", value: v.make },
    { label: "Variant", value: v.variant },
    { label: "Fuel", value: v.fuel },
    { label: "Color", value: v.color },
    { label: "Body Type", value: v.body_type },
    { label: "Category", value: [v.vehicle_category, v.vehicle_class].filter(isValid).join(" / ") || null }
  ];
  const identity = formatSection("🚘 VEHICLE IDENTITY", identityItems);
  if (identity) sections.push(identity);

  // 2. ओनर डिटेल्स
  const ownerItems = [
    { label: "Owner", value: v.owner },
    { label: "Mobile", value: data.mobile },
    { label: "Found", value: data.mobile_found === true ? "Yes" : (data.mobile_found === false ? "No" : null) }
  ];
  const owner = formatSection("👤 OWNER DETAILS", ownerItems);
  if (owner) sections.push(owner);

  // 3. मशीन डिटेल्स
  const machineItems = [
    { label: "Chassis", value: v.chassis },
    { label: "Last 5", value: data.chassis_last5 },
    { label: "Engine", value: v.engine }
  ];
  const machine = formatSection("🔑 MACHINE DETAILS", machineItems);
  if (machine) sections.push(machine);

  // 4. रजिस्ट्रेशन
  const regItems = [
    { label: "Date", value: v.registration_date },
    { label: "Reg No", value: v.registration_no },
    { label: "RTO", value: v.rto }
  ];
  const reg = formatSection("📅 REGISTRATION", regItems);
  if (reg) sections.push(reg);

  // 5. एड्रेस (स्पेशल फॉर्मेटिंग)
  if (isValid(v.address)) {
    const wrappedAddress = wrapText(v.address, 35);
    sections.push(formatSection("📍 ADDRESS", [{ label: "", value: wrappedAddress }]));
  }

  // 6. इंश्योरेंस
  const insItems = [
    { label: "Company", value: v.insurance_company },
    { label: "Upto", value: v.insurance_upto }
  ];
  const ins = formatSection("🛡️ INSURANCE", insItems);
  if (ins) sections.push(ins);

  // अब सबको जोड़कर आपका डिज़ाइन तैयार करें
  let text = `🧭 <b>VEHICLE JOURNEY</b> — ${escapeHTML(regNo)}\n`;
  text += `────────────────────────────────────────────\n`;
  text += `│\n`;
  text += sections.join("│\n");
  text += `\n────────────────────────────────────────────\n`;
  text += `⚠️🚨 <b>IMPORTANT NOTE / ज़रूरी सूचना</b> 🚨⚠️\n`;
  text += `🔍 Ye details sirf AUDIT / VERIFICATION purpose ke liye hain.\n`;
  text += `🚫 Kripya iska koi bhi GALAT USE na karein.\n`;
  text += `🔒 Privacy & safety ka khayal rakhein. 🙏\n`;
  text += `✅ Sirf authorized audit purpose ke liye use karein.\n`;
  text += `────────────────────────────────────────────`;

  return text;
}

// ---------- Telegram API Helpers ----------
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
