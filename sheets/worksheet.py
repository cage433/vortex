from sheets import Workbook
from utils import checked_type

__all__ = ["Worksheet"]

class Worksheet:
    def __init__(self, workbook: Workbook, sheet_name: str):
        self.workbook: Workbook = checked_type(workbook, Workbook)
        self.sheet_name: str = checked_type(sheet_name, str)