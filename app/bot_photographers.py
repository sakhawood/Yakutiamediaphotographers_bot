from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    tg_id = user.id
    name = user.first_name or ""
    username = user.username or ""

    sheets = context.bot_data.get("sheets")

    # Получаем всех фотографов
    rows = sheets.sheet_photographers.get_all_records()

    exists = any(str(r["Telegram ID"]) == str(tg_id) for r in rows)

    if not exists:
        sheets.sheet_photographers.append_row([
            tg_id,
            name,
            username,
            0,   # Время рассылки (по умолчанию 0)
            0,   # Принял
            0,   # Отменил
            0    # Просрочил
        ])

        await update.message.reply_text("Вы зарегистрированы в системе.")
    else:
        await update.message.reply_text("Вы уже зарегистрированы.")
        

def register_handlers(application):
    application.add_handler(CommandHandler("start", start))