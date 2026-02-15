from telegram.ext import ApplicationBuilder
from app.config import BOT_TOKEN
from app.sheets import SheetsClient
from app.event_monitor import monitor_events


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    sheets = SheetsClient()

    application.job_queue.run_repeating(
        lambda context: monitor_events(application, sheets),
        interval=60,
        first=10,
    )

    print(application.job_queue)

    application.run_polling()


if __name__ == "__main__":
    main()