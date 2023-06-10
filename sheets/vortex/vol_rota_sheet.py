from date_range.month import Month
from sheets import Workbook
from sheets.worksheet import Worksheet

__all__ = ["VolRotaSheet"]


class VolRotaSheet(Worksheet):
    def __init__(self, workbook: Workbook, month: Month):
        super().__init__(workbook, month.tab_name)

