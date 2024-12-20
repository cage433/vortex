from typing import List

from accounting.accounting_activity import AccountingActivity
from bank_statements import BankActivity
from date_range import DateRange, Day
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from env import YTD_ACCOUNTS_SPREADSHEET_ID, BBL_ACCOUNT_ID
from google_sheets import Workbook
from google_sheets.accounts.accounting_report_tab import AccountingReportTab
from google_sheets.statements.categorised_transactions import current_account_transactions_from_tabs


def create_accounting_tab(periods: List[DateRange], period_names: List[str], title: str, force: bool):
    workbook = Workbook(YTD_ACCOUNTS_SPREADSHEET_ID)
    bounding_period = SimpleDateRange(periods[0].first_day, periods[-1].last_day)

    accounting_activity = AccountingActivity.activity_for_period(bounding_period, force)
    tab = AccountingReportTab(workbook, title,
                              periods, period_names, accounting_activity)
    tab.update()


def create_month_tab(month: AccountingMonth, force: bool):
    weeks = month.weeks
    period_titles = [f"W{w.week_no}" for w in weeks]
    title = f"MTD {month.month_name}"
    create_accounting_tab(weeks, period_titles, title, force=force)


def create_ytd_tab(year: AccountingYear, force: bool):
    last_month = AccountingMonth.from_calendar_month(Day.today().month)
    months = [m for m in year.accounting_months if m <= last_month]
    if months:
        print(f"Creating YTD tab for {year.y}")
        period_titles = [m.month_name for m in months]
        title = f"YTD {year.y}"
        create_accounting_tab(months, period_titles, title, force=force)


def report_on_bank_pnl():
    m = AccountingMonth(AccountingYear(2018), 1)
    last_month = AccountingMonth(AccountingYear(2024), 11)
    full_period = SimpleDateRange(m.first_day, last_month.last_day)
    bank_activity = BankActivity.build(False).restrict_to_period(full_period).restrict_to_accounts(BBL_ACCOUNT_ID)
    while m <= last_month:
        pnl_change = bank_activity.balance_at_eod(m.last_day) - bank_activity.balance_at_sod(m.first_day)
        print(f"{m.month_name}: {pnl_change:1.2f}, end balance {bank_activity.balance_at_eod(m.last_day):1.2f}")
        m += 1


def find_transactions_for_payee(payee: str):
    full_period = SimpleDateRange(Day(2015, 1, 1), Day(2024, 12, 31))
    bank_activity = BankActivity.build(False).restrict_to_period(full_period)
    for tr in bank_activity.sorted_transactions:
        if payee.upper() in tr.payee.upper():
            print(tr)


if __name__ == '__main__':
    # acc_month = AccountingMonth.from_calendar_month(Month(2024, 2))
    # create_month_tab(acc_month, force=False)

    for y in range(2024, 2026):
        create_ytd_tab(AccountingYear(y), force=False)
    # for m in [1, 2, 3, 4]:
    #     create_month_tab(AccountingMonth(AccountingYear(2025), m), force=True)
    # for y in range(2025, 2026):
    #     create_ytd_tab(AccountingYear(y), show_transactions=True, force=True)
    # for m in list(range(9, 13)) + list(range(1, 9)):
    #     create_month_tab(AccountingMonth(AccountingYear(2022), m))
    # create_month_tab(AccountingMonth(AccountingYear(2024), 5), force=False)
    # find_transactions_for_payee("pauline")
