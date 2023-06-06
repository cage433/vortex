from date_range.month import Month
from sheets import Workbook
from sheets.worksheet import Worksheet
from utils import checked_type
from env import TEST_SHEET_ID

__all__ = ["VolRotaSheet"]


class VolRotaSheet(Worksheet):
    def __init__(self, month: Month):
        super.__init__(TEST_SHEET_ID, month)
        self.workbook: Workbook = checked_type(workbook, Workbook)
        self.sheet_name: str = checked_type(sheet_name, str)
