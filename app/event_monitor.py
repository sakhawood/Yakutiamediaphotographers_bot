import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Кэш уже обработанных событий (в памяти контейнера)
PROCESSED_EVENTS = set()


async def monitor_events(application, sheets):
    """
    Проверяет лист СОБЫТИЯ.
    Ищет события со статусом 'в работу'
    и запускает распределение.
    """

    try:
        print("=== MONITOR START ===", flush=True)

        records = sheets.sheet_events.get_all_records()
        print("Total rows:", len(records), flush=True)

        for row in records:

            print("ROW:", row, flush=True)

            event_id = str(row.get("ID")).strip()
            status = str(row.get("Статус")).strip()
            photographers_needed = row.get("Количество фотографов")
            duration = row.get("Продолжительность")

            print(
                f"Check event {event_id} | status={status} | "
                f"N={photographers_needed} | duration={duration}",
                flush=True
            )

            # Условия запуска
            if (
                status == "в работу"
                and photographers_needed
                and duration
                and event_id not in PROCESSED_EVENTS
            ):

                print(f"Start distribution for event {event_id}", flush=True)

                PROCESSED_EVENTS.add(event_id)

                await start_distribution(
                    application,
                    sheets,
                    event_id,
                    int(photographers_needed)
                )

        print("=== MONITOR END ===", flush=True)

    except Exception as e:
        print("Error in monitor_events:", e, flush=True)
        await asyncio.sleep(5)


async def start_distribution(application, sheets, event_id, required_count):
    """
    Отправляет уведомление фотографам.
    """

    print(f"Distributing event {event_id}", flush=True)

    photographers = sheets.sheet_photographers.get_all_records()

    print("PHOTOGRAPHERS:", photographers, flush=True)

    if not photographers:
        print("No photographers found", flush=True)
        return

    for p in photographers:

        try:
            tg_id = int(p["Telegram ID"])

            print("SENDING TO:", tg_id, flush=True)

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ Принять",
                        callback_data=f"accept_{event_id}"
                    )
                ]
            ])

            await application.bot.send_message(
                chat_id=tg_id,
                text=(
                    f"Новое мероприятие\n\n"
                    f"ID: {event_id}\n"
                    f"Требуется фотографов: {required_count}"
                ),
                reply_markup=keyboard
            )

        except Exception as e:
            print("Error sending to photographer:", e, flush=True)