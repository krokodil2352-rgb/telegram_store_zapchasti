import os
import telebot
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")  # переменная окружения
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет — бот запущен!")

# Webhook endpoint
@server.route('/webhook', methods=['POST'])
def telegram_webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@server.route('/', methods=['GET'])
def index():
    return "Бот живёт", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
