import asyncio
import datetime
import logging
import os
import requests
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

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

# Токен бота и параметры берутся из переменных окружения
def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(f"Обязательная переменная окружения '{name}' не задана.")
    return value

TELEGRAM_BOT_TOKEN = _require_env("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = _require_env("WEBHOOK_URL")

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Создаем Flask приложение
app = Flask(__name__)

# Функция получения прогноза погоды (пример с OpenWeatherAPI)
def get_weather():
    api_key = _require_env("OWM_API_KEY")
    city = "Moscow"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    weather = data['weather'][0]['description']
    temp = data['main']['temp']
    return f"Погода в {city}: {weather}, температура: {temp}°C"

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
async def start(update: Update, context) -> None:
    keyboard = [
        [InlineKeyboardButton("Погода", callback_data='weather')],
        [InlineKeyboardButton("Дни рождения", callback_data='birthdays')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Привет! Чем могу помочь?', reply_markup=reply_markup)

# Обработчик кнопок
async def button(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'weather':
        await query.edit_message_text(text=get_weather())
    elif query.data == 'birthdays':
        await query.edit_message_text(text=check_birthdays())

# Роут для обработки обновлений через webhook
@app.route('/' + TELEGRAM_BOT_TOKEN, methods=['POST'])
def webhook():
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, application.bot)
    asyncio.run(application.process_update(update))
    return 'ok'

# Инициализация бота и настройка webhook
async def setup() -> None:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    await application.initialize()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")

if __name__ == '__main__':
    asyncio.run(setup())
    app.run(host='0.0.0.0', port=5000)
