import asyncio

# Глобальный lock для accept
event_lock = asyncio.Lock()