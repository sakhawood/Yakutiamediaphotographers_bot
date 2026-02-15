import gspread
from google.oauth2.service_account import Credentials
from app.config import GOOGLE_CREDENTIALS

print("AUTH OK", flush=True)

class SheetsClient:

    def __init__(self):
        print("INIT SHEETS START", flush=True)

        creds = Credentials.from_service_account_info(
            GOOGLE_CREDENTIALS,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )

        print("CREDS CREATED", flush=True)

        self.gc = gspread.authorize(creds)
        print("GSPREAD AUTHORIZED", flush=True)

        self.book_events = self.gc.open("Order_Yakutia.media")
        print("EVENT BOOK OPENED", flush=True)

        self.book_photographers = self.gc.open("Order_Photographers")
        print("PHOTO BOOK OPENED", flush=True)

        self.sheet_events = self.book_events.worksheet("СОБЫТИЯ")
        print("SHEET EVENTS OK", flush=True)

        self.sheet_assignments = self.book_events.worksheet("НАЗНАЧЕНИЯ")
        print("SHEET ASSIGNMENTS OK", flush=True)

        self.sheet_photographers = self.book_photographers.worksheet("ФОТОГРАФЫ")
        print("SHEET PHOTOGRAPHERS OK", flush=True)