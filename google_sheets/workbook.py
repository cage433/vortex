from numbers import Number
from pathlib import Path
from typing import Union

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

    def tab_ids_by_name(self) -> dict[str, int]:
        metadata = self._resource.get(spreadsheetId=TEST_SHEET_ID).execute()
        sheets = metadata.get('sheets')
        return {
            sheet["properties"]["title"]: sheet["properties"]["sheetId"]
            for sheet in sheets
        }

    def delete_tab(self, name: str):
        sheet_id = self.tab_ids_by_name()[name]
        request = {
            'delete_sheet': {
                'sheet_id': sheet_id
            }
        }
        self.batch_update(request)

    def batch_update(self, requests: Union[dict, list[dict]]):
        if isinstance(requests, dict):
            requests = [requests]
        batch_update_values_request_body = {
            'requests': requests
        }
        return self._resource.batchUpdate(
            spreadsheetId=self.sheet_id,
            body=batch_update_values_request_body
        ).execute()

    def batch_update_values(self, value_ranges: dict['TabRange', list[list[any]]]):
        def transform_values(values):
            def to_excel(value):
                return value if isinstance(value, Number) else str(value)

            return [
                [to_excel(value) for value in row]
                for row in values
            ]


        batch_update_values_request_body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range":range.full_range_name,
                 "values": transform_values(values)}
                for range, values in value_ranges.items()
            ]
        }

        return self._resource.values().batchUpdate(
            spreadsheetId=self.sheet_id,
            body=batch_update_values_request_body
        ).execute()

    def has_tab(self, name) -> bool:
        return name in self.tab_ids_by_name()

    def add_tab(self, name):
        if self.has_tab(name):
            raise ValueError("Sheet called #{name} already exists")
        request = {
            "add_sheet": {
                "properties": {
                    "title": name,
                    "grid_properties": {"hide_gridlines": True}
                }
            }
        }
        self.batch_update(request)
        print(f"Created tab for #{name}")
