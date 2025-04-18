from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
import requests
import os
from telegram.ext import InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from uuid import uuid4
from telegram.ext import CommandHandler

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

def send_long_message(bot, chat_id, text):
    max_length = 4096
    for i in range(0, len(text), max_length):
        bot.send_message(chat_id=chat_id, text=text[i:i+max_length])

# Handler for incoming Telegram messages
def handle_message(update, context):
    message = update.message
    user_text = message.text
    bot_username = context.bot.username
    # If the message is from a group and the bot is mentioned
    if message.chat.type in ['group', 'supergroup']:
        if f"@{bot_username}" in user_text:
            clean_text = user_text.replace(f"@{bot_username}", "").strip()
            gemini_response = get_gemini_reply(clean_text)
            send_long_message(context.bot, message.chat_id, gemini_response)
    
    # If the message is from a private chat (DM)
    elif message.chat.type == 'private':
        gemini_response = get_gemini_reply(user_text)
        send_long_message(context.bot, message.chat_id, gemini_response)

def inline_query(update, context):
    query = update.inline_query.query

    if not query:
        return  # No query, do nothing
        

    # Get Gemini reply
    gemini_response = get_gemini_reply(query)

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Ask Gemini",
            input_message_content=InputTextMessageContent(gemini_response)
        )
    ]

    update.inline_query.answer(results, cache_time=1)

def handle_message(update, context):
    message = update.message
    user_text = message.text.lower()  # lowercase for safe matching

    if message.chat.type in ['group', 'supergroup']:
        if "gemini" in user_text:
            gemini_response = get_gemini_reply(user_text)
            send_long_message(context.bot, message.chat.id, gemini_response)

    elif message.chat.type == 'private':
        gemini_response = get_gemini_reply(user_text)
        send_long_message(context.bot, message.chat.id, gemini_response)
def overthink(update, context):
    message = update.message

    if message.reply_to_message:
        target_text = message.reply_to_message.text
    elif context.args:
        target_text = ' '.join(context.args)
    else:
        message.reply_text("Please reply to a message or provide text to overthink.")
        return

    prompt = f"Overthink this message thoroughly. List all possible specific scenarios, outcomes, their descriptions, and give a likelihood rating out of 10 for each. try exploring all aspects:\n\n\"{target_text}\""

    gemini_response = get_gemini_reply(prompt)
    send_long_message(context.bot, message.chat.id, gemini_response)



# Set up dispatcher
dispatcher = Dispatcher(bot, None, workers=4)
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_handler(InlineQueryHandler(inline_query))
dispatcher.add_handler(CommandHandler("overthink", overthink))

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
