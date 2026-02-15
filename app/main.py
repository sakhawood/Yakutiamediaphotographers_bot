from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from sheets import SheetsClient
from event_monitor import monitor_events


def main():
    # 1️⃣ Создаем приложение
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # 2️⃣ Инициализация Google Sheets (один раз)
    sheets = SheetsClient()

    # 3️⃣ Планировщик проверки событий (раз в 60 секунд)
    application.job_queue.run_repeating(
        lambda context: monitor_events(application, sheets),
        interval=60,
        first=10,
    )

    print("Bot started...")
    
    # 4️⃣ Запуск polling
    application.run_polling()


if __name__ == "__main__":
    main()