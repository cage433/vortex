from decimal import Decimal
from numbers import Number
from pathlib import Path
from time import sleep
from typing import Union

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from utils import checked_type

__all__ = ["Workbook"]


class Workbook:
    def __init__(self, sheet_id: str):
        self.sheet_id = checked_type(sheet_id, str)
        self._service = self._get_service()
        self._resource = self._service.spreadsheets()

    def retry_on_http_error(self, resource_func):
        num_tries = 0
        sleep_seconds = 5
        while num_tries < 5:
            try:
                return resource_func()
            except HttpError as e:
                if e.resp.status in [429]:
                    num_tries += 1
                    print(f"Retrying after error {e.resp.status} ({num_tries}/5)")
                    sleep(sleep_seconds)
                    sleep_seconds *= 2
                else:
                    raise e
        raise ValueError("Failed to get result after 5 retries due to HTTP")

    @staticmethod
    def _get_service() -> Resource:
        token_path = Path(__file__).parent.parent / "token.json"
        creds = Credentials.from_authorized_user_file(str(token_path))
        return build('sheets', 'v4', credentials=creds)

    def tab_ids_by_name(self) -> dict[str, int]:
        metadata = self.retry_on_http_error(lambda: self._resource.get(spreadsheetId=self.sheet_id).execute())
        sheets = metadata.get('sheets')
        return {
            sheet["properties"]["title"]: sheet["properties"]["sheetId"]
            for sheet in sheets
        }

    def _row_or_column_groups_for_tab_id(self, tab_id: int, is_rows: bool):
        groupsName = "rowGroups" if is_rows else "columnGroups"
        metadata = self.retry_on_http_error(lambda: self._resource.get(spreadsheetId=self.sheet_id).execute())

        sheets = metadata.get('sheets')
        for sheet in sheets:
            if sheet["properties"]["sheetId"] == tab_id:
                groups = []
                for row_group in sheet.get(groupsName, []):
                    start_index = row_group["range"]["startIndex"]
                    end_index = row_group["range"]["endIndex"]
                    depth = row_group["depth"]
                    groups.append((start_index, end_index, depth))
                return groups
        raise ValueError("No sheet with id # found")

    def row_groups_for_tab_id(self, tab_id: int):
        return self._row_or_column_groups_for_tab_id(tab_id, is_rows=True)

    def column_groups_for_tab_id(self, tab_id: int):
        return self._row_or_column_groups_for_tab_id(tab_id, is_rows=False)

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
        return self.retry_on_http_error(
            lambda: self._resource.batchUpdate(
                spreadsheetId=self.sheet_id,
                body=batch_update_values_request_body
            ).execute())

    def batch_update_values(self, value_ranges: list[tuple['TabRange', list[list[any]]]],
                            value_input_option: str = "USER_ENTERED"):
        def match_dimensions(range, values):
            if not isinstance(values, list):
                assert range.is_single_cell, "Value must be a list if range is not a single cell"
                return [[values]]

            assert len(values) > 0, "Can't have an empty list of values"
            if not isinstance(values[0], list):
                if range.is_row:
                    return [values]
                if range.is_column:
                    return [[value] for value in values]
                raise ValueError(f"Mismatch of range and value dimensions")
            return values

        def transform_values(values):
            def to_excel(value):
                if isinstance(value, Decimal):
                    return float(value)
                if isinstance(value, Number):
                    return value
                return str(value)

            return [
                [to_excel(value) for value in row]
                for row in values
            ]

        batch_update_values_request_body = {
            "valueInputOption": value_input_option,
            "data": [
                {"range": range.full_range_name,
                 "values": transform_values(match_dimensions(range, values))}
                for range, values in value_ranges
            ]
        }

        return self.retry_on_http_error(
            lambda: self._resource.values().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=batch_update_values_request_body
            ).execute())

    def has_tab(self, name) -> bool:
        return name in self.tab_ids_by_name()

    def add_tab(self, name):
        if self.has_tab(name):
            raise ValueError(f"Sheet called {name} already exists")
        request = {
            "add_sheet": {
                "properties": {
                    "title": name,
                    "grid_properties": {"hide_gridlines": True}
                }
            }
        }
        self.batch_update(request)
        print(f"Created tab for {name}")
