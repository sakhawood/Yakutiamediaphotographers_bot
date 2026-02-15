from app.locks import event_locks

async def try_accept_event(sheets, event_id, tg_id, name, required_count):

    async with event_locks[event_id]:

        rows = sheets.sheet_assignments.get_all_records()

        accepted = [
            r for r in rows
            if r["ID события"] == event_id
            and r["Статус"] == "принял"
        ]

        if len(accepted) >= required_count:
            return False

        sheets.append_assignment([
            event_id,
            tg_id,
            name,
            "принял",
            "",
            "",
            ""
        ])

        return True