from typing import List

from bank_statements import BankActivity, Transaction
from date_range import DateRange
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type


class StatementsRange(TabRange):

    HEADINGS = ["Date", "Payee", "Amount", "Transaction Type", "FTID", "Balance", "Category", "Confirmed"]
    (DATE, PAYEE, AMOUNT, TYPE, FTID, BALANCE, CATEGORY, CONFIRMED) = range(len(HEADINGS))
    def __init__(
            self,
            top_left_cell: TabCell,
            title: str,
            period: DateRange,
            bank_activity: BankActivity,
    ):
        super().__init__(top_left_cell, num_rows=1000, num_cols=len(self.HEADINGS))
        self.title = checked_type(title, str)
        self.period: DateRange = checked_type(period, DateRange)
        self.bank_activity: BankActivity = checked_type(bank_activity, BankActivity)
        if len(self.bank_activity.sorted_transactions) > 1000:
            raise ValueError("Make statements range larger")

    def format_requests(self):
        return [
            self.outline_border_request(),
            self.tab.group_columns_request(self.TYPE, self.FTID)
        ]

    def transaction_from_sheet(self) -> List[Transaction]:
        pass


