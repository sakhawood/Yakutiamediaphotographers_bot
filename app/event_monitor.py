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

        # Количество требуемых фотографов
        try:
            required_count = int(event.get("Количество фотографов") or 0)
        except ValueError:
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
            print("ALREADY FULL", flush=True)
            return

        # --- 3. Получаем активных фотографов ---
        photographers = sheets.sheet_photographers.get_all_records()

        active_photographers = [
            p for p in photographers
            if str(p.get("Активен", "1")).strip() == "1"
        ]

        print("Active photographers:", len(active_photographers), flush=True)

        if not active_photographers:
            print("NO ACTIVE PHOTOGRAPHERS", flush=True)
            return

        # --- 4. Проверяем NOTIFICATIONS (чтобы не спамить) ---
        notifications = sheets.sheet_notifications.get_all_records()

        for photographer in active_photographers:

            tg_id = photographer.get("Telegram ID")

            if not tg_id:
                continue

            # Проверка: уже отправляли этому фотографу?
            already_sent = any(
                str(n.get("ID события")) == str(event_id)
                and str(n.get("Telegram ID")) == str(tg_id)
                for n in notifications
            )

            if already_sent:
                continue

            # --- 5. Отправляем сообщение ---
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
                await application.bot.send_message(
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

                # --- 6. Фиксируем в NOTIFICATIONS ---
                sheets.sheet_notifications.append_row([
                    event_id,
                    tg_id,
                    datetime.utcnow().isoformat()
                ])

            except Exception as e:
                print("SEND ERROR:", e, flush=True)

        print("DISTRIBUTION FINISHED", flush=True)

    except Exception as e:
        print("DISTRIBUTION ERROR:", e, flush=True)