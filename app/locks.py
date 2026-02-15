import asyncio
from collections import defaultdict

event_locks = defaultdict(asyncio.Lock)