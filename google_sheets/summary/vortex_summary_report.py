from airtable_db.contracts_and_events import GigsInfo
from date_range import DateRange, Day
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from env import VORTEX_TICKET_SALES_SPREADSHEET_ID
from google_sheets import Workbook
from google_sheets.ticket_sales.vortex_summary_tab import VortexSummaryTab
from google_sheets.accounts.accounting_report_tab import gig_info, read_nominal_ledger


def run_report(period: DateRange, title: str):
    workbook = Workbook(VORTEX_TICKET_SALES_SPREADSHEET_ID)

    gigs_info_list = []
    force = False
    month = Month.containing(period.first_day)
    last_month = Month.containing(period.last_day)
    while month <= last_month:
        period_info = gig_info(month, force)
        gigs_info_list += period_info.contracts_and_events
        month += 1
    nominal_ledger = read_nominal_ledger(force)
    gigs_info = GigsInfo(gigs_info_list)
    tab = VortexSummaryTab(workbook, title, gigs_info, nominal_ledger)
    tab.update()

if __name__ == '__main__':
    period = SimpleDateRange(Day(2021, 1, 1), Day(2023, 11, 30))
    run_report(period, "Summary")