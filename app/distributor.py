from app.locks import event_locks
import asyncio

async def try_accept_event(sheets, event_id, tg_id, name, required_count):

    required_count = int(required_count)

    async with event_locks[event_id]:

        rows = sheets.sheet_assignments.get_all_records()

        accepted = [
            r for r in rows
            if str(r["ID события"]).strip() == str(event_id)
            and r["Статус"] == "принял"
        ]

        if len(accepted) >= required_count:
            return False

        await asyncio.to_thread(
            sheets.append_assignment,
            [
                event_id,
                tg_id,
                name,
                "принял",
                "",
                "",
                ""
            ]
        )

        return True