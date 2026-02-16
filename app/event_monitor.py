import asyncio
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Кэш уже обработанных событий (в памяти контейнера)
PROCESSED_EVENTS = set()


async def monitor_events(context):
    sheets = context.job.data["sheets"]

    try:
        print("=== MONITOR START ===", flush=True)

        events = sheets.sheet_events.get_all_records()
        assignments = sheets.sheet_assignments.get_all_records()

        for idx, event in enumerate(events, start=2):

            event_id = str(event.get("ID")).strip()
            status = str(event.get("Статус")).strip()

            if status != "в работу":
                continue

            try:
                required = int(event.get("Количество фотографов") or 0)
            except:
                required = 0

            if required <= 0:
                continue

            # Считаем принятых
            accepted = [
                a for a in assignments
                if str(a.get("ID события")) == event_id
                and a.get("Статус") == "принял"
            ]

            if len(accepted) >= required:
                print("EVENT FULL → SETTING STATUS", flush=True)
                sheets.sheet_events.update_cell(idx, 3, "укомплектовано")
                continue

            # Запускаем распределение
            await start_distribution(
                context.application,
                sheets,
                event_id,
                required,
                accepted
            )

        print("=== MONITOR END ===", flush=True)

    except Exception as e:
        print("MONITOR ERROR:", repr(e), flush=True)

async def start_distribution(application, sheets, event_id, required, accepted):

    print("Distributing event", event_id, flush=True)

    try:
        accepted_ids = {
            str(a.get("Telegram ID"))
            for a in accepted
        }

        photographers = sheets.sheet_photographers.get_all_records()

        active_photographers = [
            p for p in photographers
            if str(p.get("Активен", "")).strip() == "1"
        ]

        # Загружаем уведомления
        notifications_raw = sheets.sheet_notifications.get_all_values()

        if len(notifications_raw) <= 1:
            notifications = []
        else:
            headers = notifications_raw[0]
            notifications = [
                dict(zip(headers, row))
                for row in notifications_raw[1:]
                if len(row) == len(headers)
            ]

        notified_ids = {
            str(n.get("Telegram ID"))
            for n in notifications
            if str(n.get("ID события")) == event_id
        }

        # Кому можно отправлять?
        eligible = [
            p for p in active_photographers
            if str(p.get("Telegram ID")) not in accepted_ids
            and str(p.get("Telegram ID")) not in notified_ids
        ]

        if not eligible:
            print("NO ELIGIBLE PHOTOGRAPHERS", flush=True)
            return

        for p in eligible:

            tg_id = int(str(p.get("Telegram ID")).split(".")[0])

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Принять",
                        callback_data=f"accept_{event_id}"
                    )
                ]
            ]

            msg = await application.bot.send_message(
                chat_id=tg_id,
                text=(
                    f"📌 Новое мероприятие\n\n"
                    f"🆔 ID: {event_id}\n"
                    f"Количество фотографов: {required}"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            print("SENT TO:", tg_id, flush=True)

            sheets.sheet_notifications.append_row([
                event_id,
                tg_id,
                datetime.utcnow().isoformat()
            ])

    except Exception as e:
        print("DISTRIBUTION ERROR:", repr(e), flush=True)