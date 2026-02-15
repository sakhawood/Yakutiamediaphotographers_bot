import asyncio

# кэш обработанных событий
PROCESSED_EVENTS = set()


async def monitor_events(application, sheets):
    try:
        print("=== MONITOR START ===", flush=True)

        records = sheets.sheet_events.get_all_records()
        print(f"Total rows: {len(records)}", flush=True)

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

            if (
                status == "в работу"
                and photographers_needed
                and duration
                and event_id not in PROCESSED_EVENTS
            ):
                print(f"Start distribution for event {event_id}", flush=True)

                PROCESSED_EVENTS.add(event_id)

                await start_distribution(application, sheets, event_id)

        print("=== MONITOR END ===", flush=True)

    except Exception as e:
        print("Error in monitor_events:", e, flush=True)
        await asyncio.sleep(5)


async def start_distribution(application, sheets, event_id):
    print(f"Distributing event {event_id}", flush=True)