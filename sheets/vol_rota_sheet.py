from date_range.month import Month
from env import TEST_SHEET_ID
from sheets.worksheet import Worksheet

__all__ = ["VolRotaSheet"]


class VolRotaSheet(Worksheet):
    def __init__(self, month: Month):
        super.__init__(TEST_SHEET_ID, month.tab_name)
