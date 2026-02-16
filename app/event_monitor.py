import asyncio
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Кэш уже обработанных событий (в памяти контейнера)
PROCESSED_EVENTS = set()


async def monitor_events(context):
    sheets = context.job.data["sheets"]

    try:
        print("=== MONITOR START ===", flush=True)

        records = sheets.sheet_events.get_all_records()
        print("Total rows:", len(records), flush=True)

        for row in records:

            event_id = str(row.get("ID")).strip()
            status = str(row.get("Статус")).strip()
            photographers_needed = row.get("Количество фотографов")
            duration = row.get("Продолжительность")

            print(
                f"Check event {event_id} | status={status} | "
                f"N={photographers_needed} | duration={duration}",
                flush=True
            )

            # ✅ Единственная проверка
            if (
                status == "в работу"
                and photographers_needed
                and duration
            ):
                await start_distribution(
                    context.application,
                    sheets,
                    event_id
                )

        print("=== MONITOR END ===", flush=True)

    except Exception as e:
        print("Error in monitor_events:", e, flush=True)
        await asyncio.sleep(5)


async def start_distribution(application, sheets, event_id):

    print(f"Distributing event {event_id}", flush=True)

    try:
        # --- 1. Получаем событие ---
        events = sheets.sheet_events.get_all_records()

        event = next(
            (e for e in events if str(e.get("ID")) == str(event_id)),
            None
        )

        if not event:
            print("EVENT NOT FOUND", flush=True)
            return

        try:
            required_count = int(event.get("Количество фотографов") or 0)
        except:
            required_count = 0

        if required_count <= 0:
            print("INVALID REQUIRED COUNT", flush=True)
            return

        # --- 2. Проверяем текущее количество принятых ---
        assignments = sheets.sheet_assignments.get_all_records()

        current_accepts = [
            a for a in assignments
            if str(a.get("ID события")) == str(event_id)
            and a.get("Статус") == "принял"
        ]

        print("CURRENT ACCEPTS:", len(current_accepts), flush=True)

        if len(current_accepts) >= required_count:
            print("ALREADY FULL → SET STATUS", flush=True)

            # обновляем статус события
            for idx2, e in enumerate(events, start=2):
                if str(e.get("ID")) == str(event_id):
                    sheets.sheet_events.update_cell(idx2, 3, "укомплектовано")
            break

        return

        # --- 3. Получаем активных фотографов ---
        photographers = sheets.sheet_photographers.get_all_records()

        active_photographers = [
            p for p in photographers
            if str(p.get("Активен", "")).strip() == "1"
        ]

        print("Active photographers:", len(active_photographers), flush=True)

        if not active_photographers:
            print("NO ACTIVE PHOTOGRAPHERS", flush=True)
            return

        # --- 4. Загружаем уведомления ---
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

        # --- 5. Рассылка ---
        for photographer in active_photographers:

            tg_id_raw = photographer.get("Telegram ID")

            if not tg_id_raw:
                continue

            try:
                tg_id = int(str(tg_id_raw).split(".")[0])
            except:
                print("INVALID TG ID:", tg_id_raw, flush=True)
                continue

            already_sent = any(
                str(n.get("ID события")) == str(event_id)
                and str(n.get("Telegram ID")) == str(tg_id)
                for n in notifications
            )

            if already_sent:
                continue

            print("SENDING TO:", tg_id, flush=True)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Принять",
                        callback_data=f"accept_{event_id}"
                    )
                ]
            ]

            try:
                msg = await application.bot.send_message(
                    chat_id=tg_id,
                    text=(
                        f"📌 Новое мероприятие\n\n"
                        f"Тип: {event.get('Тип', '')}\n"
                        f"Категория: {event.get('Категория', '')}\n"
                        f"Дата: {event.get('Дата мероприятия', '')}\n"
                        f"Время: {event.get('Время начала', '')}"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

                print("SENT OK:", msg.message_id, flush=True)

                sheets.sheet_notifications.append_row([
                    event_id,
                    tg_id,
                    datetime.utcnow().isoformat()
                ])

            except Exception as e:
                print("SEND ERROR:", repr(e), flush=True)

        print("DISTRIBUTION FINISHED", flush=True)

    except Exception as e:
        print("DISTRIBUTION ERROR:", repr(e), flush=True)