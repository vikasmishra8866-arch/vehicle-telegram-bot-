# Vehicle Telegram Bot

VahanLookup API को Telegram बॉट के जरिए इस्तेमाल करने के लिए।

## Environment Variables
- `BOT_TOKEN` — Telegram bot token (BotFather से)
- `API_KEY` — hideme.eu.org की API key
- `WEBHOOK_SECRET` — कोई रैंडम स्ट्रिंग (webhook सुरक्षा के लिए)

## Endpoints
- `POST /api/bot` — Telegram webhook
- `GET /api/set-webhook?secret=...` — webhook सेट करने के लिए
