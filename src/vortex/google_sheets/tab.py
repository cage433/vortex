from google_sheets import Workbook
from utils import checked_type

__all__ = ["Tab"]


class Tab:
    def __init__(self, workbook: Workbook, tab_name: str):
        self.workbook: Workbook = checked_type(workbook, Workbook)
        self.tab_name: str = checked_type(tab_name, str)
        self._tab_id: int = None

    @property
    def tab_id(self):
        if self._tab_id is None:
            self._tab_id = self.workbook.tab_ids_by_name()[self.tab_name]
        return self._tab_id

    def cell(self, coordinates):
        from google_sheets.tab_range import CellCoordinates, TabCell
        if isinstance(coordinates, str):
            coordinates = CellCoordinates(text=coordinates)
        return TabCell(tab=self, coordinates=coordinates)

    def update_all_cells_request(self, fields: list[str]) -> dict:
        return {
            "update_cells": {
                "range": {"sheet_id": self.tab_id},
                "fields": ",".join(fields)
            }
        }

    def unmerge_all_request(self):
        return {
            "unmerge_cells": {
                "range": {
                    "sheet_id": self.tab_id
                }
            }
        }

    def num_rows(self) -> int:
        return self.workbook.retry_on_http_error(
            lambda: self.workbook._resource.get(
                spreadsheetId=self.workbook.sheet_id,
                ranges=[f"{self.tab_name}!A:A"],
                includeGridData=False
            ).execute().get("sheets", [])[0].get("properties", {}).get("gridProperties", {}).get("rowCount", 0)
        )

    def read_values_for_columns(self, column_range: str) -> list[list[any]]:
        values = self.workbook.retry_on_http_error(
            lambda: self.workbook._resource.values().get(
                spreadsheetId=self.workbook.sheet_id,
                range=f"{self.tab_name}!{column_range}",
            ).execute())
        return values.get("values") or []

    def clear_values_and_formats_requests(self) -> list[dict]:
        return [
            self.update_all_cells_request(
                ["userEnteredValue", "userEnteredFormat"]
            ),
            self.unmerge_all_request(),
        ] + self.delete_all_groups_requests() + [self.freeze_rows_request(i_frozen_row=0)]

    def group_rows_request(self, i_first_row, i_last_row):
        return {
            "add_dimension_group": {
                "range": {
                    "sheet_id": self.tab_id,
                    "dimension": "ROWS",
                    "start_index": i_first_row,
                    "end_index": i_last_row + 1
                },
            }
        }

    def group_columns_request(self, i_first_col, i_last_col):
        return {
            "add_dimension_group": {
                "range": {
                    "sheet_id": self.tab_id,
                    "dimension": "COLUMNS",
                    "start_index": i_first_col,
                    "end_index": i_last_col + 1
                },
            }
        }

    def freeze_rows_request(self, i_frozen_row):
        return {
            'updateSheetProperties': {
                'properties': {
                    'sheetId': self.tab_id,
                    'gridProperties': {
                        'frozenRowCount': i_frozen_row
                    }
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        }

    def set_num_rows_request(self, row_count: int):
        return {
            'updateSheetProperties': {
                'properties': {
                    'sheetId': self.tab_id,
                    'gridProperties': {
                        'rowCount': row_count
                    }
                },
                'fields': 'gridProperties.rowCount'
            }
        }

    def collapse_all_groups_requests(self):
        def collapse_request(start_index, end_index, depth, dimension):
            return {
                "update_dimension_group": {
                    "dimension_group": {
                        "range": {
                            "sheet_id": self.tab_id,
                            "dimension": dimension,
                            "start_index": start_index,
                            "end_index": end_index
                        },
                        "depth": depth,
                        "collapsed": True
                    },
                    "fields": "collapsed"
                }
            }

        collapse_rows_requests = [
            collapse_request(start_index, end_index, depth, "ROWS")
            for (start_index, end_index, depth) in self.row_groups()
        ]
        collapse_cols_requests = [
            collapse_request(start_index, end_index, depth, "COLUMNS")
            for (start_index, end_index, depth) in self.column_groups()
        ]
        return collapse_rows_requests + collapse_cols_requests

    def row_groups(self) -> list[tuple[int, int, int]]:
        return self.workbook.row_groups_for_tab_id(self.tab_id)

    def column_groups(self) -> list[tuple[int, int, int]]:
        return self.workbook.column_groups_for_tab_id(self.tab_id)

    def delete_all_groups_requests(self):
        def deletion_request(start_index, end_index, dimension):
            return {
                "delete_dimension_group": {
                    "range": {
                        "sheet_id": self.tab_id,
                        "dimension": dimension,
                        "start_index": start_index,
                        "end_index": end_index
                    }
                }
            }

        row_deletions = [
            deletion_request(start_index, end_index, "ROWS")
            for (start_index, end_index, _) in self.row_groups()
        ]
        column_deletions = [
            deletion_request(start_index, end_index, "COLUMNS")
            for (start_index, end_index, _) in self.column_groups()
        ]
        return row_deletions + column_deletions

    def _unhide_rows_or_columns_request(self, dimension: str):
        end_index = 1000
        if dimension == "COLUMNS":
            end_index = 20
        return {
            "updateDimensionProperties": {
                "properties": {
                    "hiddenByUser": False
                },
                "fields": "hiddenByUser",
                "range": {
                    "sheet_id": self.tab_id,
                    "dimension": dimension,
                    "start_index": 0,
                    "end_index": end_index
                },
            }
        }

    def unhide_rows_request(self):
        return self._unhide_rows_or_columns_request("ROWS")

    def unhide_columns_request(self):
        return self._unhide_rows_or_columns_request("COLUMNS")

    def set_column_width_request(self, i_col: int, width: int):
        return self.set_columns_width_request(i_col, i_col, width)

    def set_columns_width_request(self, i_first_col: int, i_last_col: int, width: int):
        return {
            "update_dimension_properties": {
                "range": {
                    "sheet_id": self.tab_id,
                    "dimension": "COLUMNS",
                    "start_index": i_first_col,
                    "end_index": i_last_col + 1
                },
                "properties": {
                    "pixel_size": width
                },
                "fields": "pixel_size"
            }
        }
