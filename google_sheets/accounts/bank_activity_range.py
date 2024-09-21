from bank_statements import BankActivity
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type


class BankActivityRange(TabRange):
    DATE_COLUMN, ACCOUNT_COLUMN, PAYEE_COLUMN, AMOUNT_COLUMN = range(4)

    def __init__(self, top_left_cell: TabCell, bank_activity: BankActivity):
        super().__init__(top_left_cell, 2 + bank_activity.num_transactions, 4)
        self.bank_activity = checked_type(bank_activity, BankActivity)

    def format_requests(self):
        return [
            self.outline_border_request(),
            self[0].set_bold_text_request(),
            self[2:].set_decimal_format_request("#,##0.00")
        ]

    def values(self):
        transactions = sorted(self.bank_activity.sorted_transactions, key=lambda t: t.amount)
        return [
            (self[0], ["Date", "Account", "Payee", "Amount"]),
            (self[2:, self.DATE_COLUMN], [t.payment_date.date for t in transactions]),
            (self[2:, self.ACCOUNT_COLUMN], [t.account.name for t in transactions]),
            (self[2:, self.PAYEE_COLUMN], [t.payee for t in transactions]),
            (self[2:, self.AMOUNT_COLUMN], [float(t.amount) for t in transactions])
        ]
