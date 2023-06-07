from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource

from env import TEST_SHEET_ID
from utils import checked_type

__all__ = ["Workbook"]


class Workbook:
    def __init__(self, sheet_id: str):
        self.sheet_id = checked_type(sheet_id, str)
        self._service = self._get_service()
        self._resource = self._service.spreadsheets()

    @staticmethod
    def _get_service() -> Resource:
        token_path = Path(__file__).parent.parent / "token.json"
        creds = Credentials.from_authorized_user_file(str(token_path))
        return build('sheets', 'v4', credentials=creds)

    def sheet_ids_by_name(self) -> dict[str, int]:
        metadata = self._resource.get(spreadsheetId=TEST_SHEET_ID).execute()
        sheets = metadata.get('sheets')
        return {
            sheet["properties"]["title"]:sheet["properties"]["sheetId"]
            for sheet in sheets
        }

    def create_sheet(self, name):
        request = {
            'add_sheet': {
                'properties': {
                    'title': name,
                    'grid_properties': {'hide_gridlines': True}

                }
            }
        }
        requests = [request]
        body = {
            'requests': requests
        }
        self._resource.batchUpdate(
            spreadsheetId = self.sheet_id,
            body=body
        ).execute()

    def delete_sheet(self, name: str):
        sheet_id = self.sheet_ids_by_name()[name]
        request = {
            'delete_sheet': {
                'sheet_id': sheet_id
            }
        }
        requests = [request]
        body = {
            'requests': requests
        }
        self._resource.batchUpdate(
            spreadsheetId = self.sheet_id,
            body=body
        ).execute()



