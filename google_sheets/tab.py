from google_sheets import Workbook
from utils import checked_type

__all__ = ["Tab"]


class Tab:
    def __init__(self, workbook: Workbook, tab_name: str):
        self.workbook: Workbook = checked_type(workbook, Workbook)
        self.tab_name: str = checked_type(tab_name, str)

    @property
    def tab_id(self):
        return self.workbook.tab_ids_by_name()[self.tab_name]

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

    def clear_values_and_formats_requests(self) -> list[dict]:
        return [
            self.update_all_cells_request(
                ["userEnteredValue", "userEnteredFormat"]
            ),
            self.unmerge_all_request(),
        ]
