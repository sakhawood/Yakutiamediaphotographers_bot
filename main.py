import asyncio
from telegram.ext import ApplicationBuilder
from app.config import BOT_TOKEN
from app.sheets import SheetsClient
from app.event_monitor import monitor_events
from app.distributor import try_accept_event

class AppContext:
    def __init__(self, application, sheets):
        self.application = application
        self.sheets = sheets

async def main():

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    sheets = SheetsClient()

    ctx = AppContext(application, sheets)

    application.create_task(
        monitor_events(ctx, sheets)
    )

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())