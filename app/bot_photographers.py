import os
import json
import asyncio
from datetime import datetime, timedelta

import gspread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger


# =============================
# ENV VARIABLES
# =============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

if not GOOGLE_CREDENTIALS:
    raise ValueError("GOOGLE_CREDENTIALS not set")


# =============================
# GOOGLE SHEETS
# =============================

creds_dict = json.loads(GOOGLE_CREDENTIALS)
gc = gspread.service_account_from_dict(creds_dict)

# Книга заявок
orders_book = gc.open("Order_Yakutia.media")
orders_sheet = orders_book.sheet1

# Книга фотографов
photographers_book = gc.open("Фотографы")
photographers_sheet = photographers_book.sheet1

# Лист назначений
assignments_sheet = photographers_book.worksheet("Назначения")


# =============================
# TELEGRAM MENU
# =============================

MAIN_KEYBOARD = [
    ["📅 Мероприятия сегодня"],
    ["📆 Мероприятия завтра"],
    ["📂 Мои заказы"]
]


# =============================
# START
# =============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот фотографов Yakutia.media",
        reply_markup=ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)
    )


# =============================
# CHECK NEW ORDERS
# =============================

async def check_orders(context: ContextTypes.DEFAULT_TYPE):
    """
    Проверяет заявки со статусом 'в работу'
    """

    print("Проверка заявок:", datetime.now())

    rows = orders_sheet.get_all_records()

    for row in rows:
        if row.get("status") == "в работу":
            event_id = row.get("id")

            # TODO:
            # Проверить сколько уже приняло
            # Если меньше лимита — запускать волну рассылки
            print("Найдена активная заявка:", event_id)


# =============================
# MAIN
# =============================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_orders,
        trigger=IntervalTrigger(minutes=1),
        args=[app]
    )
    scheduler.start()

    print("Бот фотографов запущен")

    app.run_polling()


if __name__ == "__main__":
    main()