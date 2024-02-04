from datetime import date

from airtable_db.contracts_table import ContractsTable
from airtable_db.table_columns import ContractsColumns
from data_objects.upcoming_gig import UpcomingGig
from date_range import Day
from date_range.month import Month
from date_range.simple_date_range import SimpleDateRange
from env import UPCOMING_GIGS_ID
from google_sheets import Workbook
from google_sheets.gigs.upcoming_gigs_tab import UpcomingGigsTab


def update_sheet():
    tab = UpcomingGigsTab(Workbook(UPCOMING_GIGS_ID))
    today = Day.from_date(date.today())
    date_range = SimpleDateRange(
        Month.containing(today).first_day,
        Day(2030, 1, 1)
    )
    contracts = ContractsTable().records_for_date_range(
        date_range,
        [ContractsColumns.PERFORMANCE_DATE,
         ContractsColumns.EVENT_TITLE,
         ContractsColumns.DOOR_TIME_1ST_SHOW,
         ContractsColumns.TYPE]
    )
    gigs = []
    for contract in contracts:
        if contract.contract_type == "Rehearsal":
            continue
        if contract.event_title(allow_missing=True) is None:
            continue
        gig = UpcomingGig(
            contract.performance_date,
            contract.door_time,
            contract.event_title(),
            contract.contract_type
        )
        gigs.append(gig)
    tab.update(gigs)


if __name__ == '__main__':
    update_sheet()
