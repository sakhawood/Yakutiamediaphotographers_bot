from datetime import datetime
from app.locks import event_locks


async def try_accept_event(sheets, event_id, tg_id, name, required_count):
    """
    Пытается принять мероприятие.
    Возвращает:
        True  — если успешно принят
        False — если лимит уже закрыт
    """

    async with event_locks[event_id]:

        print("TRY ACCEPT:", event_id, flush=True)

        # Получаем все значения листа (без get_all_records)
        values = sheets.sheet_assignments.get_all_values()

        # Если только заголовки или лист пустой
        if len(values) <= 1:
            accepted_count = 0
        else:
            accepted_count = 0

            for row in values[1:]:  # пропускаем заголовок
                try:
                    row_event_id = str(row[0]).strip()
                    row_status = str(row[3]).strip()
                except IndexError:
                    continue

                if (
                    row_event_id == str(event_id)
                    and row_status == "принял"
                ):
                    accepted_count += 1

        print("CURRENT ACCEPTED:", accepted_count, flush=True)

        # Проверка лимита
        if accepted_count >= required_count:
            print("LIMIT REACHED", flush=True)
            return False

        # Добавляем запись
        sheets.sheet_assignments.append_row([
            event_id,
            tg_id,
            name,
            "принял",
            datetime.now().isoformat(),
            "",
            ""
        ])

        print("APPENDED TO SHEET", flush=True)

        return True