from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
import requests, os

app = Flask(__name__)

# Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Set up Telegram Bot
bot = Bot(token=TELEGRAM_TOKEN)

def handle_message(update, context):
    user_message = update.message.text
    response = ask_gemini(user_message)
    update.message.reply_text(response)

def ask_gemini(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    r = requests.post(url, headers=headers, json=data)
    result = r.json()
    try:
        reply = result['candidates'][0]['content']['parts'][0]['text']
    except:
        reply = "Oops! I couldn’t get a reply from Gemini."
    return reply

# Webhook Route
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return "ok"

# Dispatcher
dp = Dispatcher(bot, None, workers=0)
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Home Route (for pinging)
@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

# Run App
if __name__ == "__main__":
    app.run(port=5000)