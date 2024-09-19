from accounting.accounting_activity import AccountingActivity
from bank_statements import BankActivity
from date_range import DateRange
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from myopt.opt import Opt
from utils.collection_utils import group_into_dict


def report_on_mismatching_items(period: DateRange, force: bool):
    print(f"Reporting on {period}")
    activity_period = SimpleDateRange(period.first_day - 31, period.last_day + 31)
    activity = AccountingActivity.activity_for_period(activity_period, force=force, force_bank=True)
    restricted_bank_transactions = sorted(
        activity.bank_activity.restrict_to_period(period).sorted_transactions,
        key=lambda t: t.amount
    )
    transactions_by_category = group_into_dict(restricted_bank_transactions, lambda t: t.category)
    categories = [key for key in transactions_by_category]
    for c in categories:
        print(c, len(transactions_by_category[c]), sum(t.amount for t in transactions_by_category[c]))
    unknown = transactions_by_category[Opt.of(None)]
    print(len(unknown))
    unknown = sorted(unknown, key=lambda t: t.payment_date)
    for u in unknown:
        print(u.payment_date, u.ftid, u.payee, u.amount)


if __name__ == '__main__':

    report_on_mismatching_items(
        AccountingMonth.from_calendar_month(Month(2024, 1)),
        force=False
    )
