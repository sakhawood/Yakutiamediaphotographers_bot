import asyncio

# кэш обработанных событий (в памяти контейнера)
PROCESSED_EVENTS = set()


async def monitor_events(application, sheets):
    """
    Проверяет лист СОБЫТИЯ раз в 60 секунд.
    Находит события со статусом 'в работу'
    и запускает распределение.
    """

    try:
        print("Monitoring events...")

        # 1️⃣ Получить все строки (один запрос к Sheets)
        records = sheets.sheet_events.get_all_records()

        for row in records:

            event_id = str(row.get("ID")).strip()
            status = str(row.get("Статус")).strip()
            photographers_needed = row.get("Количество фотографов")
            duration = row.get("Продолжительность")

            # 2️⃣ Проверка условий запуска
            if (
                status == "в работу"
                and photographers_needed
                and duration
                and event_id not in PROCESSED_EVENTS
            ):

                print(f"Start distribution for event {event_id}")

                # 3️⃣ Добавляем в кэш, чтобы не запускать повторно
                PROCESSED_EVENTS.add(event_id)

                # 4️⃣ Запускаем распределение
                await start_distribution(application, sheets, event_id)

        print("Monitoring complete")

    except Exception as e:
        print("Error in monitor_events:", e)
        await asyncio.sleep(5)

async def start_distribution(application, sheets, event_id):
    """
    Заглушка запуска распределения.
    Здесь позже будет логика рассылки.
    """
    print(f"Distributing event {event_id}")