from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource

from utils import checked_type

__all__ = ["Workbook"]


class Workbook:
    def __init__(self, sheet_id: str):
        self.sheet_id = checked_type(sheet_id, str)
        self._service = self._get_service()

    @staticmethod
    def _get_service() -> Resource:
        token_path = Path(__file__).parent.parent / "token.json"
        creds = Credentials.from_authorized_user_file(str(token_path))
        return build('sheets', 'v4', credentials=creds)
