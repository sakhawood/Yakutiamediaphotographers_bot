from telegram.ext import ApplicationBuilder
from app.config import BOT_TOKEN
from app.sheets import SheetsClient
from app.event_monitor import monitor_events
from app.bot_photographers import register_handlers


def main():
    print("ENTERING MAIN", flush=True)

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    print("JOB QUEUE:", application.job_queue)

    sheets = SheetsClient()

    # 👇 ВАЖНО: передаем sheets во все handlers
    application.bot_data["sheets"] = sheets

    # 👇 регистрируем команды и callbacks
    register_handlers(application)

    application.job_queue.run_repeating(
        monitor_events,
        interval=60,
        first=10,
        name="event_monitor",
        job_kwargs={"max_instances": 1},
        data={"sheets": sheets},
    )

    print("Bot started...", flush=True)

    application.run_polling()


if __name__ == "__main__":
    main()