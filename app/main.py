from telegram.ext import ApplicationBuilder
from app.config import BOT_TOKEN
from app.sheets import SheetsClient
from app.event_monitor import monitor_events
from app.bot_photographers import register_handlers


def main():
    print("ENTERING MAIN", flush=True)

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    sheets = SheetsClient()
    application.bot_data["sheets"] = sheets

    register_handlers(application)

    print("JOB QUEUE:", application.job_queue, flush=True)

    sheets = SheetsClient()

    application.job_queue.run_repeating(
        lambda context: monitor_events(application, sheets),
        interval=60,
        first=10,
    )

    print("Bot started...", flush=True)

    application.run_polling()


if __name__ == "__main__":
    main()