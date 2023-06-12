import itertools

from pyairtable import Table
from pyairtable.formulas import FIELD, OR

from airtable_db.contracts_and_events import EventRecord
from airtable_db.contracts_table import ContractsTable
from airtable_db.table_columns import EventColumns, ContractsColumns, TicketPriceLevel, TicketCategory
from date_range.month import Month
from env import VORTEX_DATABASE_ID, AIRTABLE_TOKEN

class EventsTable:
    TABLE = "Events"


    def __init__(self):
        self.table = Table(AIRTABLE_TOKEN, VORTEX_DATABASE_ID, EventsTable.TABLE)

    def records_for_contracts(self, contracts, *fields) -> list[EventRecord]:
        ids = list(itertools.chain(*[c.events_link for c in contracts]))
        formula = OR(*[f"{FIELD(EventColumns.EVENT_ID)} = '{id}'" for id in ids])
        return [
            EventRecord(rec)
            for rec in self.table.all(formula=formula, fields=fields)
        ]


if __name__ == '__main__':
    c = ContractsTable()
    period = Month(2023, 1)
    contracts = c.records_for_date_range(period, [ContractsColumns.RECORD_ID, ContractsColumns.EVENTS_LINK])
    e = EventsTable()
    events = e.records_for_contracts(contracts, EventColumns.EVENT_ID, EventColumns.SHEETS_EVENT_TITLE)
    for event in events:
        print(event.title)
