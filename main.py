from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
import requests
import os

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini API Endpoint (Flash model)
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Set up Flask app
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Function to fetch reply from Gemini AI
def get_gemini_reply(message_text):
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": message_text}
                ]
            }
        ]
    }

    response = requests.post(GEMINI_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        reply_text = result['candidates'][0]['content']['parts'][0]['text']
        return reply_text
    else:
        return "Oops! I couldn’t get a reply from Gemini."

# Handler for incoming Telegram messages
def handle_message(update, context):
    user_message = update.message.text
    reply = get_gemini_reply(user_message)
    update.message.reply_text(reply)

# Set up dispatcher
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Webhook route
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# Health check route
@app.route("/")
def index():
    return "Bot is live!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
