import datetime
import logging
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, Updater, Dispatcher
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Пример данных для дней рождения
BIRTHDAYS = {
    "Аня": {"date": "2025-03-29", "profile_link": "https://t.me/anya_profile", "info": "Творческая личность, любит путешествовать."},
    "Сергей": {"date": "2025-03-30", "profile_link": "https://t.me/sergey_profile", "info": "Спортивный энтузиаст и фанат науки."},
    # Добавьте других пользователей здесь
}

# Токен бота
TELEGRAM_BOT_TOKEN = "7842539374:AAGuHhEgAcS6dAHKvCqEXjzVksgJD83fOkQ"  # Токен, полученный от @BotFather
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Создаем Flask приложение
app = Flask(__name__)

# Функция получения прогноза погоды (пример с OpenWeatherAPI)
def get_weather():
    API_KEY = "cdc958826226e0655a3eab011eaaebf5"  # Ваш API-ключ для погоды
    CITY = "Moscow"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    data = response.json()
    weather = data['weather'][0]['description']
    temp = data['main']['temp']
    return f"Погода в {CITY}: {weather}, температура: {temp}°C"

# Функция для проверки ближайших дней рождения
def check_birthdays():
    today = datetime.date.today()
    upcoming = []

    for name, details in BIRTHDAYS.items():
        bday = datetime.datetime.strptime(details["date"], "%Y-%m-%d").date()
        delta = (bday - today).days
        if 0 <= delta <= 3:
            upcoming.append(f"🎉 {name} — {bday.strftime('%d.%m.%Y')} ({delta} дн.)\n"
                            f"💬 Профиль: {details['profile_link']}\n"
                            f"📝 Информация: {details['info']}\n"
                            f"📅 Дата рождения: {bday.strftime('%d.%m.%Y')}\n"
                            f"📌 Возраст в день рождения: {bday.year - today.year} лет")

    return "🎂 Ближайшие дни рождения:\n" + "\n\n".join(upcoming) if upcoming else "❌ Дней рождений нет."

# Обработчик команды /start
def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Погода", callback_data='weather')],
        [InlineKeyboardButton("Дни рождения", callback_data='birthdays')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Привет! Чем могу помочь?', reply_markup=reply_markup)

# Обработчик кнопок
def button(update, context):
    query = update.callback_query
    query.answer()

    if query.data == 'weather':
        query.edit_message_text(text=get_weather())
    elif query.data == 'birthdays':
        query.edit_message_text(text=check_birthdays())

# Роут для обработки обновлений через webhook
@app.route('/' + TELEGRAM_BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = Update.de_json(json_str, bot)
    dispatcher.process_update(update)
    return 'ok'

# Запуск бота через webhook
def run_bot():
    global dispatcher
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)  # Используем переменную TELEGRAM_BOT_TOKEN
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Настройка webhook
    bot.set_webhook(url=f'https://telegrambot-production-12af.up.railway.app/{TELEGRAM_BOT_TOKEN}')

if __name__ == '__main__':
    run_bot()
    app.run(host='0.0.0.0', port=5000)
