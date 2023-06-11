from date_range.month import Month
from google_sheets import Workbook
from google_sheets.tab import Tab

__all__ = ["VolRotaSheet"]


class VolRotaSheet(Tab):
    def __init__(self, workbook: Workbook, month: Month):
        super().__init__(workbook, month.tab_name)

