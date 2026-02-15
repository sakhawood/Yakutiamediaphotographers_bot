from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    tg_id = user.id
    name = user.first_name or ""
    username = user.username or ""

    sheets = context.bot_data.get("sheets")

    # Получаем значения листа
    values = sheets.sheet_photographers.get_all_values()

    if len(values) <= 1:
        rows = []
    else:
        rows = sheets.sheet_photographers.get_all_records()

    exists = any(str(r["Telegram ID"]) == str(tg_id) for r in rows)

    if not exists:
        sheets.sheet_photographers.append_row([
            tg_id,
            name,
            username,
            0,   # Время рассылки
            0,   # Принял
            0,   # Отменил
            0    # Просрочил
        ])

        await update.message.reply_text("Вы зарегистрированы в системе.")
    else:
        await update.message.reply_text("Вы уже зарегистрированы.")


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
    application.add_handler(CallbackQueryHandler(handle_accept, pattern="^accept_"))