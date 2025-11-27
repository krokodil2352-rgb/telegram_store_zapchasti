from flask import Flask, request
import requests
import os

TOKEN = os.environ.get("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Bot is running", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            requests.post(URL, json={
                "chat_id": chat_id,
                "text": "Бот запущен и работает."
            })

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
