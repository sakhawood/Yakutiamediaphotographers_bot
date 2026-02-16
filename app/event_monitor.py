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
                f"Check event {event_id} | status={status}",
                flush=True
            )

            # -------------------------
            # 1. Только если "в работу"
            # -------------------------
            if status != "в работу":
                continue

            # -------------------------
            # 2. Если уже запускали — пропускаем
            # -------------------------
            if str(distributed).strip() == "1":
                continue

            print("START FIRST DISTRIBUTION", flush=True)

            # -------------------------
            # 3. Запускаем рассылку ОДИН РАЗ
            # -------------------------
            await start_distribution(
                context.application,
                sheets,
                event_id
            )

            # -------------------------
            # 4. Фиксируем запуск
            # (колонка 15 — проверь индекс)
            # -------------------------
            sheets.sheet_events.update_cell(idx, 15, 1)

        print("=== MONITOR END ===", flush=True)

    except Exception as e:
        print("Error in monitor_events:", repr(e), flush=True)

async def start_distribution(application, sheets, event_id):

    print(f"Distributing event {event_id}", flush=True)

    try:
        # ----------------------------------
        # 1. Получаем событие
        # ----------------------------------
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

        # ----------------------------------
        # 2. Проверяем текущее количество принявших
        # ----------------------------------
        assignments = sheets.sheet_assignments.get_all_records()

        accepted_ids = {
            str(a.get("Telegram ID"))
            for a in assignments
            if str(a.get("ID события")) == str(event_id)
            and a.get("Статус") == "принял"
        }

        print("CURRENT ACCEPTS:", len(accepted_ids), flush=True)

        if len(accepted_ids) >= required_count:
            print("ALREADY FULL — STOP DISTRIBUTION", flush=True)
            return

        # ----------------------------------
        # 3. Получаем активных фотографов
        # ----------------------------------
        photographers = sheets.sheet_photographers.get_all_records()

        active_photographers = [
            p for p in photographers
            if str(p.get("Активен", "")).strip() == "1"
        ]

        print("Active photographers:", len(active_photographers), flush=True)

        if not active_photographers:
            print("NO ACTIVE PHOTOGRAPHERS", flush=True)
            return

        # ----------------------------------
        # 4. Рассылка
        # ----------------------------------
        for photographer in active_photographers:

            tg_id_raw = photographer.get("Telegram ID")

            if not tg_id_raw:
                continue

            try:
                tg_id = str(int(float(tg_id_raw)))
            except:
                print("INVALID TG ID:", tg_id_raw, flush=True)
                continue

            # ❗ не отправляем тем, кто уже принял
            if tg_id in accepted_ids:
                print("SKIP — ALREADY ACCEPTED:", tg_id, flush=True)
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
                await application.bot.send_message(
                    chat_id=int(tg_id),
                    text=(
                        f"📌 Новое мероприятие\n\n"
                        f"🆔 ID события: {event_id}\n\n"
                        f"📂 Тип: {event.get('Тип', '')}\n"
                        f"🏷 Категория: {event.get('Категория', '')}\n"
                        f"📅 Дата: {event.get('Дата мероприятия', '')}\n"
                        f"⏰ Время: {event.get('Время начала', '')}"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

                print("SENT OK", flush=True)

            except Exception as e:
                print("SEND ERROR:", repr(e), flush=True)

        print("DISTRIBUTION FINISHED", flush=True)

    except Exception as e:
        print("DISTRIBUTION ERROR:", repr(e), flush=True)