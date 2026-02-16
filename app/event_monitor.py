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

            distributed = row.get("Распределение запущено")

            if (
                status == "в работу"
                and photographers_needed
                and duration
                and not distributed
            ):

                print(f"Start distribution for event {event_id}", flush=True)

                sheets.sheet_events.update_cell(idx, 15, 1)

                PROCESSED_EVENTS.add(event_id)

                await start_distribution(
                    context.application,
                    sheets,
                    event_id,
                    int(photographers_needed)
                )

        print("=== MONITOR END ===", flush=True)

    except Exception as e:
        print("Error in monitor_events:", e, flush=True)
        await asyncio.sleep(5)


async def start_distribution(application, sheets, event_id, required_count):

    print(f"Distributing event {event_id}", flush=True)

    photographers = sheets.sheet_photographers.get_all_records()

    active_photographers = [
        p for p in photographers
        if str(p.get("Активен", "1")).strip() == "1"
    ]

    print("Active photographers:", len(active_photographers), flush=True)

    keyboard = [
        [
            InlineKeyboardButton(
                "Принять",
                callback_data=f"accept_{event_id}"
            )
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    for photographer in active_photographers:

        tg_id = photographer.get("Telegram ID")

        if not tg_id:
            continue

        print("SENDING TO:", tg_id, flush=True)

        try:
            await application.bot.send_message(
                chat_id=tg_id,
                text=f"Новое мероприятие {event_id}",
                reply_markup=markup
            )
        except Exception as e:
            print("SEND ERROR:", e, flush=True)