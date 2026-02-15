from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler, filters

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    tg_id = user.id
    sheets = context.bot_data["sheets"]

    rows = sheets.sheet_photographers.get_all_records()

    photographer = next(
        (r for r in rows if str(r["Telegram ID"]) == str(tg_id)),
        None
    )

    if not photographer:
        sheets.sheet_photographers.append_row([
            tg_id,
            user.first_name or "",
            user.username or "",
            0,
            0,
            0,
            0,
            1   # активен
        ])
        status = 1
    else:
        raw_status = photographer.get("Активен", 1)

        if str(raw_status).strip() == "":
            status = 1
        else:
            status = int(raw_status)

    await show_main_menu(update, context, status)

async def toggle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("TOGGLE CLICKED", flush=True)

    tg_id = update.effective_user.id
    sheets = context.bot_data["sheets"]

    values = sheets.sheet_photographers.get_all_values()

    for idx, row in enumerate(values[1:], start=2):

        if str(row[0]) == str(tg_id):

            current_status = int(row[7] or 0)
            new_status = 0 if current_status == 1 else 1

            sheets.sheet_photographers.update_cell(idx, 8, new_status)

            print("STATUS UPDATED TO:", new_status, flush=True)

            await show_main_menu(update, context, new_status)
            return

async def show_main_menu(update, context, status):

    if status:
        status_text = "🟢 Статус: Активен"
        toggle_text = "⛔ Выключить бота"
    else:
        status_text = "🔴 Статус: Пауза"
        toggle_text = "▶ Включить бота"

    keyboard = [
        ["📂 Мои заказы"],
        [toggle_text]
    ]

    print("MENU BUILT", flush=True)

    await update.message.reply_text(
        status_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    tg_id = update.effective_user.id
    sheets = context.bot_data["sheets"]

    rows = sheets.sheet_assignments.get_all_records()

    print("ASSIGNMENTS:", rows, flush=True)

    my_rows = [
        r for r in rows
        if str(r.get("Telegram ID")) == str(tg_id)
    ]

    print("MY_ROWS:", my_rows, flush=True)

    if not my_rows:
        await update.message.reply_text("У вас нет назначений.")
        return
    print("INLINE SENT", flush=True)

async def open_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    event_id = query.data.split("_")[1]

    sheets = context.bot_data["sheets"]

    rows = sheets.sheet_events.get_all_records()

    event = next(
        (r for r in rows if str(r["ID"]) == str(event_id)),
        None
    )

    if not event:
        await query.edit_message_text("Событие не найдено.")
        return

    text = (
        f"Мероприятие: {event_id}\n"
        f"Дата: {event['Дата мероприятия']}\n"
        f"Время: {event['Время начала']}\n"
        f"Место: {event['Место проведения']}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📤 Отправить ссылку",
                callback_data=f"upload_{event_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отменить участие",
                callback_data=f"cancel_{event_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Назад",
                callback_data="back_orders"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_to_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Переиспользуем my_orders
    update._effective_message = query.message
    await my_orders(update, context)

async def handle_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # format: accept_EVENTID
    event_id = data.split("_")[1]

    sheets = context.bot_data.get("sheets")
    user = update.effective_user

    required = 1  # временно фиксировано для теста

    from app.locks import event_locks
    from app.distributor import try_accept_event

    success = await try_accept_event(
        sheets,
        event_id,
        user.id,
        user.first_name,
        required
    )

    if success:
        await query.edit_message_text("Вы приняли мероприятие.")
    else:
        await query.edit_message_text("Лимит закрыт.")

def register_handlers(application):

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        MessageHandler(
            filters.TEXT,
            route_text_buttons
        )
    )
async def route_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    print("TEXT RECEIVED:", text, flush=True)

    if "заказы" in text.lower():
        await my_orders(update, context)

    elif "выключить" in text.lower() or "включить" in text.lower():
        await toggle_status(update, context)


def register_handlers(application):

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        MessageHandler(
            filters.TEXT,
            route_text_buttons
        )
    )

    application.add_handler(
        CallbackQueryHandler(open_order, pattern="^order_")
    )

    application.add_handler(
        CallbackQueryHandler(back_to_orders, pattern="^back_orders")
    )

    application.add_handler(
        CallbackQueryHandler(handle_accept, pattern="^accept_")
    )