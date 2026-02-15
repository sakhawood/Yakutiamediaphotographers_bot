import os
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

GOOGLE_CREDENTIALS = json.loads(
    os.getenv("GOOGLE_CREDENTIALS_JSON")
)

BOOK_EVENTS = "Order_Yakutia.media"
BOOK_PHOTOGRAPHERS = "Order_Photographers"

CHECK_INTERVAL = 60  # секунд