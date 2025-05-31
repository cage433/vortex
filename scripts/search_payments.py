from typing import Optional

from bank_statements.categorized_transaction import CategorizedTransaction
from date_range import Day
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from google_sheets.statements.categorised_transactions import current_account_transactions_from_tabs


def report_matching_transactions(name: str, last_month: AccountingMonth, force_from: Optional[AccountingMonth]):
    first_month = AccountingMonth.from_calendar_month(Month(2021, 9))
    m = first_month
    force = False
    while m <= last_month:
        if force_from and m >= force_from:
            force = True
        trans = current_account_transactions_from_tabs(m, force)
        matching = [t for t in trans.transactions if name.lower() in t.transaction.payee.lower()]
        for t in matching:
            print(f"{m} {t.transaction.payment_date} {t.transaction.payee} {t.transaction.amount} {t.category}")
        m = m + 1


if __name__ == '__main__':
    name = "direct"
    report_matching_transactions(
        name,
        last_month=AccountingMonth.from_calendar_month(Month(2025, 5)),
        force_from=None
    )
