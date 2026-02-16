import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Кэш уже обработанных событий (в памяти контейнера)
PROCESSED_EVENTS = set()


async def monitor_events(context):
    sheets = context.job.data["sheets"]

    try:
        print("=== MONITOR START ===", flush=True)

        records = sheets.sheet_events.get_all_records()
        print("Total rows:", len(records), flush=True)

        for idx, row in enumerate(records, start=2):

            event_id = str(row.get("ID")).strip()
            status = str(row.get("Статус")).strip()
            photographers_needed = row.get("Количество фотографов")
            duration = row.get("Продолжительность")
            distributed = row.get("Распределение запущено")

            print(
                f"Check event {event_id} | status={status} | "
                f"N={photographers_needed} | duration={duration}",
                flush=True
            )

            # -------------------------------
            # 1️⃣ Проверка базовых условий
            # -------------------------------
            if not (
                status == "в работу"
                and photographers_needed
                and duration
            ):
                continue

            # -------------------------------
            # 2️⃣ Проверка: уже рассылали?
            # -------------------------------
            if distributed:
                continue

            # -------------------------------
            # 3️⃣ Запускаем рассылку
            # -------------------------------
            await start_distribution(
                context.application,
                sheets,
                event_id
            )

            # -------------------------------
            # 4️⃣ Фиксируем, что рассылка была
            # -------------------------------
            sheets.sheet_events.update_cell(idx, 15, 1)

        print("=== MONITOR END ===", flush=True)

    except Exception as e:
        print("Error in monitor_events:", e, flush=True)
        await asyncio.sleep(5)


async def start_distribution(application, sheets, event_id):

    print(f"Distributing event {event_id}", flush=True)

    photographers = sheets.sheet_photographers.get_all_records()
    notifications = sheets.sheet_notifications.get_all_records()

    active_photographers = [
        p for p in photographers
        if str(p.get("Активен", "1")).strip() == "1"
    ]

    for photographer in active_photographers:

        tg_id = photographer.get("Telegram ID")
        if not tg_id:
            continue

        # Проверяем — уже уведомляли?
        already_notified = any(
            str(n.get("ID события")) == str(event_id)
            and str(n.get("Telegram ID")) == str(tg_id)
            for n in notifications
        )

        if already_notified:
            continue

        try:
            await application.bot.send_message(
                chat_id=tg_id,
                text=f"📸 Новый заказ {event_id}\nНажмите принять.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "✅ Принять",
                        callback_data=f"accept_{event_id}"
                    )]
                ])
            )

            # Фиксируем факт уведомления
            sheets.sheet_notifications.append_row([
                event_id,
                tg_id
            ])

            print("NOTIFIED:", tg_id, flush=True)

        except Exception as e:
            print("Send error:", e, flush=True)