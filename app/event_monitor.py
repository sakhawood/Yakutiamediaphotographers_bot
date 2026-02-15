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
            distributed = row.get("Распределение запущено")

            if (
                status == "в работу"
                 and photographers_needed
                 and duration
                 and not distributed
            ):

                print(f"Start distribution for event {event_id}", flush=True)

                row_index = records.index(row) + 2  # +2 из-за заголовка
                sheets.sheet_events.update_cell(row_index, 15, 1)  # 15 — номер колонки

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


async def start_distribution(application, sheets, event_id):

    print(f"Distributing event {event_id}", flush=True)

    photographers = sheets.sheet_photographers.get_all_records()

    active_photographers = [
        p for p in photographers
        if str(p.get("Активен", "1")).strip() == "1"
    ]

    print("Active photographers:", len(active_photographers), flush=True)

    for photographer in active_photographers:

        tg_id = photographer.get("Telegram ID")

        keyboard = [
            [
                InlineKeyboardButton(
                    "Принять",
                    callback_data=f"accept_{event_id}"
                )
            ]
        ]

        await application.bot.send_message(
            chat_id=tg_id,
            text=f"Новое мероприятие {event_id}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )