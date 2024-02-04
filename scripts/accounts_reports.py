from typing import List

from airtable_db.contracts_and_events import GigsInfo
from date_range import DateRange, Day
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from date_range.simple_date_range import SimpleDateRange
from env import YTD_ACCOUNTS_SPREADSHEET_ID, BBL_ACCOUNT_ID
from google_sheets import Workbook
from google_sheets.accounts.accounting_report_tab import read_nominal_ledger, gig_info, read_bank_activity, \
    AccountingReportTab


def create_accounting_tab(periods: List[DateRange], period_names: List[str], title: str, show_transactions: bool, force: bool):
    workbook = Workbook(YTD_ACCOUNTS_SPREADSHEET_ID)
    bounding_period = SimpleDateRange(periods[0].first_day, periods[-1].last_day)

    gigs_info_list = []
    for period in periods:
        period_info = gig_info(period, force)
        gigs_info_list += period_info.contracts_and_events
    gigs_info = GigsInfo(gigs_info_list)
    nominal_ledger = read_nominal_ledger(force).restrict_to_period(bounding_period)
    bank_activity = read_bank_activity(bounding_period, force=force)
    tab = AccountingReportTab(workbook, title,
                              periods, period_names, gigs_info, nominal_ledger, bank_activity, show_transactions)
    tab.update()


def create_month_tab(month: AccountingMonth, force: bool):
    weeks = month.weeks
    period_titles = [f"W{w.week_no}" for w in weeks]
    title = f"MTD {month.month_name}"
    create_accounting_tab(weeks, period_titles, title, show_transactions=True, force=force)


def create_ytd_tab(year: AccountingYear, show_transactions: bool, force: bool):
    print(f"Creating YTD tab for {year.y}")
    last_month = AccountingMonth(AccountingYear(2024), 11)
    months = [m for m in year.accounting_months if m <= last_month]
    period_titles = [m.month_name for m in months]
    title = f"YTD {year.y}"
    create_accounting_tab(months, period_titles, title, show_transactions=show_transactions, force=force)


def report_on_bank_pnl():
    m = AccountingMonth(AccountingYear(2018), 1)
    last_month = AccountingMonth(AccountingYear(2024), 11)
    full_period = SimpleDateRange(m.first_day, last_month.last_day)
    bank_activity = read_bank_activity(full_period, force=False).restrict_to_account(BBL_ACCOUNT_ID)
    while m <= last_month:
        pnl_change = bank_activity.balance_at_eod(m.last_day) - bank_activity.balance_at_sod(m.first_day)
        print(f"{m.month_name}: {pnl_change:1.2f}, end balance {bank_activity.balance_at_eod(m.last_day):1.2f}")
        m += 1


def find_transactions_for_payee(payee: str):
    full_period = SimpleDateRange(Day(2015, 1, 1), Day(2024, 12, 31))
    bank_activity = read_bank_activity(full_period, force=False)
    for tr in bank_activity.sorted_transactions:
        if payee.upper() in tr.payee.upper():
            print(tr)


if __name__ == '__main__':
    for y in range(2022, 2025):
        create_ytd_tab(AccountingYear(y), show_transactions=True, force=False)
    # for m in list(range(9, 13)) + list(range(1, 9)):
    #     create_month_tab(AccountingMonth(AccountingYear(2022), m))
    # create_month_tab(AccountingMonth(AccountingYear(2024), 11))
    # find_transactions_for_payee("pauline")
