from typing import Optional

from pyasn1.type.univ import Boolean

from bank_statements.categorized_transaction import CategorizedTransactions
from bank_statements.payee_categories import PayeeCategory
from date_range import Day
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from google_sheets.statements.statements_tab import StatementsTab


def all_transactions_from_tabs(force: Boolean) -> CategorizedTransactions:
    first_month = AccountingMonth.from_calendar_month(Month(2019, 9))
    last_month = AccountingMonth.containing(Day.today())
    period = SimpleDateRange(first_month.first_day, last_month.last_day)
    return StatementsTab.categorized_transactions(period, force)


if __name__ == '__main__':
    trans = all_transactions_from_tabs(force=False)
    # trans = trans.restrict_to_period(SimpleDateRange(Day(2023, 1, 1), Day(2023, 12, 31)))
    trans = trans.restrict_to_category(PayeeCategory.MEMBERSHIPS)
    # trans = trans.restrict_to_user("1994")
    ts = sorted(trans.transactions, key=lambda t: t.transaction.payment_date)
    for t in ts:
        print(t)

