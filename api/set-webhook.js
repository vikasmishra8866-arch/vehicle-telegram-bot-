export default async function handler(req, res) {
  // सिक्योरिटी: ?secret=... query parameter मिलाना जरूरी है
  if (req.query.secret !== process.env.WEBHOOK_SECRET) {
    return res.status(403).json({ error: "Forbidden" });
  }

  const webhookUrl = `https://${req.headers.host}/api/bot`;

  const response = await fetch(
    `https://api.telegram.org/bot${process.env.BOT_TOKEN}/setWebhook?url=${encodeURIComponent(webhookUrl)}`
  );
  const data = await response.json();

  res.status(200).json({
    webhook_url: webhookUrl,
    telegram_response: data,
  });
}
