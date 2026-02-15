import asyncio
from app.config import CHECK_INTERVAL

processed_events = set()

async def monitor_events(app, sheets):

    while True:

        events = sheets.get_active_events()

        for event in events:
            event_id = event["ID"]

            if event_id not in processed_events:
                processed_events.add(event_id)

                app.create_task(
                    app.distributor.start_distribution(event)
                )

        await asyncio.sleep(CHECK_INTERVAL)