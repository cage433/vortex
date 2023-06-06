from utils import checked_type
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

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
