from sheets import Workbook
from utils import checked_type

__all__ = ["Worksheet"]

class Worksheet:
    def __init__(self, workbook: Workbook, sheet_name: str):
        self.workbook: Workbook = checked_type(workbook, Workbook)
        self.sheet_name: str = checked_type(sheet_name, str)

    def sheet_id(self):
        return self.workbook.sheet_ids_by_name()[self.sheet_name]

