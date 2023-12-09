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

    def read_values_for_columns(self, column_range: str) -> list[list[any]]:
        values = self.workbook._resource.values().get(
            spreadsheetId=self.workbook.sheet_id,
            range=f"{self.tab_name}!{column_range}",
        ).execute()
        return values["values"]

    def clear_values_and_formats_requests(self) -> list[dict]:
        return [
            self.update_all_cells_request(
                ["userEnteredValue", "userEnteredFormat"]
            ),
            self.unmerge_all_request(),
            self.unhide_rows_request(),
        ]

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

    def collapse_all_group_rows_requests(self):
        foo = [
            {
                "update_dimension_group": {
                    "dimension_group": {
                        "range": {
                            "sheet_id": self.tab_id,
                            "dimension": "ROWS",
                            "start_index": start_index,
                            "end_index": end_index
                        },
                        "depth": depth,
                        "collapsed": True
                },
                    "fields": "collapsed"
                }
            }
            for (start_index, end_index, depth) in self.row_groups()
        ]
        return foo

    def row_groups(self) -> list[tuple[int, int, int]]:
        return self.workbook.row_groups_for_tab_id(self.tab_id)

    def delete_all_row_groups_requests(self):
        return [
            {
                "delete_dimension_group": {
                    "range": {
                        "sheet_id": self.tab_id,
                        "dimension": "ROWS",
                        "start_index": start_index,
                        "end_index": end_index
                    }
                }
            }
            for (start_index, end_index, _) in self.row_groups()
        ]

    def unhide_rows_request(self):
        return {
            "updateDimensionProperties": {
                "properties": {
                    "hiddenByUser": False
                },
                "fields": "hiddenByUser",
                "range": {
                    "sheet_id": self.tab_id,
                    "dimension": "ROWS",
                    "start_index": 0,
                    "end_index": 1000
                },
            }
        }

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
