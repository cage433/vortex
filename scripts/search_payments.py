from typing import Optional, List


from bank_statements import Transaction
from bank_statements.payee_categories import PayeeCategory
from date_range import Day
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from google_sheets.statements.statements_tab import StatementsTab


def all_transactions_from_tabs(force: bool) -> List[Transaction]:
    first_month = AccountingMonth.from_calendar_month(Month(2019, 9))
    last_month = AccountingMonth.containing(Day.today())
    period = SimpleDateRange(first_month.first_day, last_month.last_day)
    return StatementsTab.transactions(period, force)


if __name__ == '__main__':
    trans = all_transactions_from_tabs(force=False)
    for c in Transaction.categories(trans):
        print(c)
    # trans = trans.restrict_to_period(SimpleDateRange(Day(2023, 1, 1), Day(2023, 12, 31)))
    trans = Transaction.restrict_to_category(trans, PayeeCategory.WORK_PERMITS)
    # trans = trans.restrict_to_user("lb hackney genfund")
    for t in trans:
        # if abs(t.amount) > 200:
            print(t)
    total = sum(t.amount for t in trans)
    abs_total = sum(abs(t.amount) for t in trans)
    min_amount = min(t.amount for t in trans)
    max_amount = max(t.amount for t in trans)
    sorted_trans = sorted(trans, key=lambda t: t.amount)
    print(f"Total: {total}, {abs_total}")
    print(sorted_trans[0])
    print(sorted_trans[-1])


