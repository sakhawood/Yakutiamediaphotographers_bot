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

            print(
                f"Check event {event_id} | status={status} | "
                f"N={photographers_needed} | duration={duration}",
                flush=True
            )

            # 1️⃣ Базовые условия
            if not (
                status == "в работу"
                and photographers_needed
                and duration
            ):
                continue

            assignments = sheets.sheet_assignments.get_all_records()

            current_accepts = [
                a for a in assignments
                if str(a.get("ID события")) == str(event_id)
                and a.get("Статус") == "принял"
            ]

            required_count = int(photographers_needed or 0)

            # 2️⃣ Если уже укомплектовано — меняем статус
            if len(current_accepts) >= required_count:
                print("SET TO COMPLETED", flush=True)
                sheets.sheet_events.update_cell(idx, 3, "укомплектовано")
                continue

            # 3️⃣ Запускаем рассылку
            await start_distribution(
                context.application,
                sheets,
                event_id
            )

        print("=== MONITOR END ===", flush=True)

    except Exception as e:
        print("Error in monitor_events:", repr(e), flush=True)
        await asyncio.sleep(5)

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