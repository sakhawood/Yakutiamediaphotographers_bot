print("MAIN FILE LOADED")

from telegram.ext import ApplicationBuilder
from app.config import BOT_TOKEN
from app.sheets import SheetsClient
from app.event_monitor import monitor_events


def main():
    print("BOT TOKEN PREFIX:", BOT_TOKEN[:10])

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    print("JOB QUEUE:", application.job_queue)
    sheets = SheetsClient()

    application.job_queue.run_repeating(
        lambda context: monitor_events(application, sheets),
        interval=60,
        first=10,
    )

    print("Bot started...")
    application.run_polling()