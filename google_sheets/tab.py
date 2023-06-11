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


