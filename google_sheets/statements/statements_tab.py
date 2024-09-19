from typing import List

from bank_statements import BankActivity, Transaction
from date_range import DateRange, Day
from google_sheets import Tab, Workbook
from google_sheets.statements.statements_range import StatementsRange
from google_sheets.tab_range import TabRange
from myopt.nothing import Nothing
from myopt.opt import Opt


class StatementsTab(Tab):
    HEADINGS = ["Date", "Payee", "Amount", "Transaction Type", "FTID", "Balance", "Category", "Confirmed"]
    (DATE, PAYEE, AMOUNT, TYPE, FTID, BALANCE, CATEGORY, CONFIRMED) = range(len(HEADINGS))
    def __init__(
            self,
            workbook: Workbook,
            title: str,
            period: DateRange,
            bank_activity: BankActivity
    ):
        super().__init__(workbook, tab_name=title)
        self.heading_range = TabRange(self.cell("B1"), num_rows=1, num_cols=len(StatementsRange.HEADINGS))

    def transactions_from_tab(self) -> List[Transaction]:
        def to_opt(cell_value):
            if cell_value == "":
                return Nothing()
            return Opt.of(cell_value)

        transactions = []
        values = self.read_values_for_columns(self.heading_range.columns_in_a1_notation)
        # for row in values[1:]:
        #     try:
        #         payment_date = Day.parse(row[self.DATE])
        #         payee = row[self.PAYEE]
        #         email = to_opt(row[2])
        #         membership_type = row[3]
        #         expiration = to_opt(row[4]).map(Day.parse)
        #         cancelled = row[5]
        #         transactions.append(Member(
        #             name,
        #             email,
        #             membership_type,
        #             payment_date,
        #             expiration,
        #             cancelled.upper() == "TRUE"
        #         ))
        #     except Exception as e:
        #         pass
        return transactions
