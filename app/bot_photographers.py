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
        status = int(photographer.get("Активен", 1))

    await show_main_menu(update, context, status)

async def toggle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    tg_id = update.effective_user.id
    sheets = context.bot_data["sheets"]

    values = sheets.sheet_photographers.get_all_values()

    for idx, row in enumerate(values[1:], start=2):

        if str(row[0]) == str(tg_id):

            current_status = int(row[7])
            new_status = 0 if current_status == 1 else 1

            sheets.sheet_photographers.update_cell(idx, 8, new_status)

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

    await update.message.reply_text(
        status_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

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
            filters.TEXT & filters.Regex("Выключить|Включить"),
            toggle_status
        )
    )

    application.add_handler(
        CallbackQueryHandler(handle_accept, pattern="^accept_")
    )