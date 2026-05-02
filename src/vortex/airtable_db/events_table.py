import itertools

from pyairtable import Table
from pyairtable.formulas import OR, Field, AND

from vortex.airtable_db.contracts_table import ContractsTable
from vortex.airtable_db.event_record import EventRecord
from vortex.airtable_db.table_columns import EventColumns, ContractsColumns
from vortex.date_range import DateRange
from vortex.date_range.month import Month
from env import VORTEX_DATABASE_ID, AIRTABLE_TOKEN


class EventsTable:
    TABLE = "Events"


    def __init__(self):
        self.table = Table(AIRTABLE_TOKEN, VORTEX_DATABASE_ID, EventsTable.TABLE)

    def records_in_range(self, date_range: DateRange, *fields) -> list[EventRecord]:
        first_day, last_day = date_range.first_day, date_range.last_day
        fields = list(fields)
        if EventColumns.EVENT_DATE not in fields:
            fields += [EventColumns.EVENT_DATE]
        first_date_constraint = f"{Field(EventColumns.EVENT_DATE)} >= '{(first_day - 1).iso_repr}'"
        last_date_constraint = f"{Field(EventColumns.EVENT_DATE)} <= '{(last_day + 1).iso_repr}'"
        formula = AND(first_date_constraint, last_date_constraint)
        return [
            EventRecord(rec)
            for rec in self.table.all(formula=formula, fields=fields)
        ]

    def records_for_contracts(self, contracts, *fields) -> list[EventRecord]:
        ids = list(itertools.chain(*[c.events_link for c in contracts]))
        formula = OR(*[f"{Field(EventColumns.EVENT_ID)} = '{id}'" for id in ids])
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
