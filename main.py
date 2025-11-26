import telebot
from flask import Flask, request

TOKEN = "8028772930:AAHBMCojrt9h9faF1-SvtO524WG_siRNyPk"

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "Добро пожаловать в Алёшкины АвтоСокровища!\n\n"
        "Здесь вы можете:\n"
        "• Найти автозапчасти\n"
        "• Выполнить VIN-подбор\n"
        "• Узнать цену и наличие\n"
        "• Добавить товары в корзину\n\n"
        "Введите название детали или номер запчасти."
    )
    bot.send_message(message.chat.id, text)

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([
        telebot.types.Update.de_json(
            request.stream.read().decode("utf-8")
        )
    ])
    return "OK", 200

@server.route("/", methods=['GET'])
def index():
    return "Бот работает!", 200

