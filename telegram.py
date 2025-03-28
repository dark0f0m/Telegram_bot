import requests
import schedule
import time
import datetime
import pytz
import logging
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = "7842539374:AAGuHhEgAcS6dAHKvCqEXjzVksgJD83fOkQ"
CHAT_ID = "1125069128"  # ID чата
WEATHER_API_KEY = "cdc958826226e0655a3eab011eaaebf5"
NEWS_API_KEY = "YOUR_NEWSAPI_KEY"
TIMEZONE = "Europe/Moscow"  # Часовой пояс

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# === ДАННЫЕ ===
BIRTHDAYS = {
    "Аня": "2025-03-29",
    "Сергей": "2025-03-30"
}

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# === ФУНКЦИИ ===

def get_weather():
    """Получает погоду в Луганске"""
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Луганск,ru&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        response = requests.get(url).json()
        if response.get("main"):
            temp = response["main"]["temp"]
            description = response["weather"][0]["description"]
            return f"☀️ Погода в Луганске:\nТемпература: {temp}°C\n{description.capitalize()}"
        return "❌ Ошибка получения погоды."
    except Exception as e:
        logging.error(f"Ошибка погоды: {e}")
        return "❌ Ошибка получения погоды."

def check_birthdays():
    """Проверяет дни рождения на ближайшие 3 дня"""
    today = datetime.date.today()
    upcoming = []

    for name, date in BIRTHDAYS.items():
        bday = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        delta = (bday - today).days
        if 0 <= delta <= 3:
            upcoming.append(f"🎉 {name} — {bday.strftime('%d.%m.%Y')} ({delta} дн.)")

    return "🎂 Ближайшие дни рождения:\n" + "\n".join(upcoming) if upcoming else "❌ Дней рождений нет."

def get_news():
    """Получает главные новости"""
    url = f"https://newsapi.org/v2/top-headlines?country=ru&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url).json()
        if response.get("articles"):
            news = response["articles"][:3]
            return "📰 Главные новости:\n" + "\n\n".join([f"• {n['title']}" for n in news])
        return "❌ Ошибка загрузки новостей."
    except Exception as e:
        logging.error(f"Ошибка новостей: {e}")
        return "❌ Ошибка загрузки новостей."

def send_daily_report():
    """Отправляет утренний отчет"""
    message = f"{get_weather()}\n\n{check_birthdays()}\n\n{get_news()}"
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
        logging.info("✅ Утренний отчет отправлен.")
    except Exception as e:
        logging.error(f"Ошибка отправки отчета: {e}")

# === КОМАНДЫ ДЛЯ БОТА ===

def weather_command(update: Update, context: CallbackContext):
    update.message.reply_text(get_weather())

def birthdays_command(update: Update, context: CallbackContext):
    update.message.reply_text(check_birthdays())

def news_command(update: Update, context: CallbackContext):
    update.message.reply_text(get_news())

def report_command(update: Update, context: CallbackContext):
    send_daily_report()
    update.message.reply_text("✅ Утренний отчет отправлен!")

# === ЗАПУСК БОТА ===
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Добавляем команды
    dp.add_handler(CommandHandler("weather", weather_command))
    dp.add_handler(CommandHandler("birthdays", birthdays_command))
    dp.add_handler(CommandHandler("news", news_command))
    dp.add_handler(CommandHandler("report", report_command))

    # Запуск планировщика
    schedule.every().day.at("07:00").do(send_daily_report)

    def scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    # Запускаем бота и планировщик параллельно
    from threading import Thread
    Thread(target=scheduler).start()

    logging.info("🚀 Бот запущен...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
