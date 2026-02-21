from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler, filters
from app.locks import event_lock
from datetime import datetime

GROUP_CHAT_ID = -1003824519107 # ← вставь реальный ID группы заявки_Yakutia.media


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
    print("MY ORDERS CLICKED", flush=True)

    sheets = context.bot_data["sheets"]
    tg_id = update.effective_user.id

    assignments = sheets.sheet_assignments.get_all_records()
    print("ASSIGNMENTS:", assignments, flush=True)

    my_rows = [
        r for r in assignments
        if str(r["Telegram ID"]) == str(tg_id)
        and r["Статус"] == "принял"
    ]

    print("MY_ROWS:", my_rows, flush=True)

    # Определяем источник сообщения
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message

    if not my_rows:
        await message.reply_text("У вас нет активных заказов.")
        return

    # Получаем события
    events = sheets.sheet_events.get_all_records()

    # Создаём словарь ID → событие
    events_map = {
        str(e.get("ID")): e
        for e in events
    }

    keyboard = []

    for r in my_rows:
        event_id = str(r["ID события"])
        event = events_map.get(event_id)

        if not event:
            continue

        button_text = (
            f"🆔 {event_id} | "
            f"{event.get('Тип', '')} | "
            f"{event.get('Дата мероприятия', '')} | "
            f"{event.get('Время начала', '')} | "
            f"{event.get('Категория', '')}"
        )

        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"order_{event_id}"
            )
        ])

    await message.reply_text(
        "Ваши заказы:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
        f"🆔 ID события: {event_id}\n\n"
        f"👤 Заказчик: {event.get('Заказчик', '')}\n"
        f"📞 Телефон: {event.get('Контактные данные', '')}\n\n"
        f"📝 Описание:\n{event.get('Описание мероприятия', '')}\n\n"
        f"📍 Место: {event.get('Место проведения', '')}\n\n"
        f"📅 Дата: {event.get('Дата мероприятия', '')}\n"
        f"⏰ Время: {event.get('Время начала', '')}\n"
        f"📂 Тип: {event.get('Тип', '')}\n"
        f"🏷 Категория: {event.get('Категория', '')}"
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
    await my_orders(update, context)

from datetime import datetime

async def accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("ACCEPT CLICKED", flush=True)

    query = update.callback_query
    await query.answer()

    tg_id = query.from_user.id
    event_id = query.data.replace("accept_", "", 1)

    sheets = context.bot_data["sheets"]

    async with event_lock:

        # -----------------------------
        # 1. Получаем событие
        # -----------------------------
        events = sheets.sheet_events.get_all_records()

        event = next(
            (e for e in events if str(e.get("ID")) == str(event_id)),
            None
        )

        if not event:
            await query.answer("Событие не найдено.", show_alert=True)
            return

        try:
            required_count = int(event.get("Количество фотографов") or 0)
        except:
            required_count = 0

        if required_count <= 0:
            await query.answer("Некорректное количество фотографов.", show_alert=True)
            return

        print("REQUIRED:", required_count, flush=True)

        # -----------------------------
        # 2. Получаем текущие назначения
        # -----------------------------
        assignments = sheets.sheet_assignments.get_all_records()

        event_assignments = [
            r for r in assignments
            if str(r.get("ID события")) == str(event_id)
            and r.get("Статус") == "принял"
        ]

        print("CURRENT ACCEPTS BEFORE:", len(event_assignments), flush=True)

        # Уже принял?
        if any(str(r.get("Telegram ID")) == str(tg_id) for r in event_assignments):
            await query.answer(
                "Вы уже приняли это мероприятие.",
                show_alert=True
            )
            return

        # Лимит уже достигнут?
        if len(event_assignments) >= required_count:
            await query.answer(
                "Набрано необходимое количество фотографов.",
                show_alert=True
            )
            return

        # -----------------------------
        # 3. Записываем принятие
        # -----------------------------
        sheets.sheet_assignments.append_row([
            event_id,
            tg_id,
            query.from_user.first_name,
            "принял",
            datetime.utcnow().isoformat(),
            "",
            ""
        ])

        print("SUCCESS ACCEPT:", tg_id, flush=True)

        # -----------------------------
        # 4. Повторная проверка после записи
        # -----------------------------
        assignments_after = sheets.sheet_assignments.get_all_records()

        event_assignments_after = [
            r for r in assignments_after
            if str(r.get("ID события")) == str(event_id)
            and r.get("Статус") == "принял"
        ]

        print("CURRENT ACCEPTS AFTER:", len(event_assignments_after), flush=True)

        event_is_full = len(event_assignments_after) >= required_count

        if event_is_full:
            print("EVENT FULL → SETTING STATUS", flush=True)

            # Обновляем статус события
            for idx, row in enumerate(
                sheets.sheet_events.get_all_records(), start=2
            ):
                if str(row.get("ID")) == str(event_id):
                    sheets.sheet_events.update_cell(idx, 3, "укомплектовано")
                    break

    # -------------------------------------------------
    # Ниже уже вне LOCK
    # -------------------------------------------------

    # Обновляем сообщение принявшему
    await query.edit_message_text(
        f"✅ Вы приняли мероприятие {event_id}"
    )

    # Если событие стало полностью укомплектовано —
    # уведомляем остальных фотографов
    if event_is_full:

        photographers = sheets.sheet_photographers.get_all_records()

        for p in photographers:
            other_id = p.get("Telegram ID")

            if not other_id:
                continue

            if str(other_id) == str(tg_id):
                continue

            try:
                await context.application.bot.send_message(
                    chat_id=other_id,
                    text=f"⚠️ Мероприятие {event_id} полностью укомплектовано."
                )
            except Exception as e:
                print("Notify error:", other_id, e, flush=True)

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("CANCEL CLICKED", flush=True)

    query = update.callback_query
    await query.answer()

    tg_id = query.from_user.id
    event_id = query.data.replace("cancel_", "", 1)

    sheets = context.bot_data["sheets"]

    async with event_lock:

        # 1️⃣ Получаем назначения
        assignments = sheets.sheet_assignments.get_all_records()

        updated = False

        for idx, row in enumerate(assignments, start=2):

            if (
                str(row.get("ID события")) == str(event_id)
                and str(row.get("Telegram ID")) == str(tg_id)
                and row.get("Статус") == "принял"
            ):
                sheets.sheet_assignments.update_cell(idx, 4, "отменил")
                updated = True
                break

        if not updated:
            await query.answer("Назначение не найдено.", show_alert=True)
            return

        print("CANCEL SUCCESS", flush=True)

        # 2️⃣ Проверяем событие
        events = sheets.sheet_events.get_all_records()

        for idx, event in enumerate(events, start=2):

            if str(event.get("ID")) == str(event_id):

                if event.get("Статус") == "укомплектовано":

                    print("REOPEN EVENT", flush=True)

                    sheets.sheet_events.update_cell(
                        idx,
                        3,
                        "в работу"
                    )

                break

    # 3️⃣ Обновляем сообщение
    await query.edit_message_text(
        f"❌ Вы отменили участие в мероприятии {event_id}"
    )

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

async def start_upload_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    event_id = query.data.replace("upload_", "", 1)

    context.user_data["awaiting_link"] = event_id

    await query.edit_message_text(
        f"🆔 ID события: {event_id}\n\n"
        f"Отправьте ссылку на фотографии."
    )

async def handle_link_input(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "awaiting_link" not in context.user_data:
        return

    event_id = context.user_data.pop("awaiting_link")
    link = update.message.text.strip()
    tg_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    sheets = context.bot_data["sheets"]

    async with event_lock:

        assignments = sheets.sheet_assignments.get_all_records()

        # --- 1. Обновляем назначение ---
        for idx, row in enumerate(assignments, start=2):

            if (
                str(row.get("ID события")) == str(event_id)
                and str(row.get("Telegram ID")) == str(tg_id)
                and row.get("Статус") == "принял"
            ):

                # Статус → завершил
                sheets.sheet_assignments.update_cell(idx, 4, "завершил")

                # Время завершения
                sheets.sheet_assignments.update_cell(
                    idx,
                    6,
                    datetime.utcnow().isoformat()
                )

                # Ссылка
                sheets.sheet_assignments.update_cell(
                    idx,
                    7,
                    link
                )

                break

        # --- 2. Проверяем, все ли завершили ---
        assignments_after = sheets.sheet_assignments.get_all_records()

        finished = [
            a for a in assignments_after
            if str(a.get("ID события")) == str(event_id)
            and a.get("Статус") == "завершил"
        ]

        events = sheets.sheet_events.get_all_records()

        for idx, event in enumerate(events, start=2):

            if str(event.get("ID")) == str(event_id):

                required = int(event.get("Количество фотографов") or 0)

                if len(finished) >= required:

                    sheets.sheet_events.update_cell(
                        idx,
                        3,
                        "завершено"
                    )

                    await context.application.bot.send_message(
                        chat_id=GROUP_CHAT_ID,
                        text=(
                            f"🏁 Событие полностью завершено\n\n"
                            f"🆔 ID: {event_id}\n"
                            f"Фотографов: {required}"
                        )
                    )

                break

    # --- 3. Подтверждение пользователю ---
    await update.message.reply_text(
        f"✅ Ссылка сохранена для события {event_id}"
    )

    # --- 4. Уведомление в группу о конкретном фотографе ---
    try:
        await context.application.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=(
                f"📸 Завершено фотографом\n\n"
                f"🆔 ID: {event_id}\n"
                f"👤 @{username}\n"
                f"🔗 {link}"
            )
        )
    except Exception as e:
        print("GROUP SEND ERROR:", e, flush=True)

def register_handlers(application):

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex("Мои заказы"),
            my_orders
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex("Выключить бота|Включить бота"),
            toggle_status
        )
    )

    application.add_handler(
        CallbackQueryHandler(open_order, pattern="^order_")
    )

    application.add_handler(
        CallbackQueryHandler(back_to_orders, pattern="^back_orders")
    )

    application.add_handler(
        CallbackQueryHandler(accept_order, pattern="^accept_")
    )

    application.add_handler(
        CallbackQueryHandler(cancel_order, pattern="^cancel_")
    )

    application.add_handler(
        CallbackQueryHandler(start_upload_link, pattern="^upload_")
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link_input)
    )