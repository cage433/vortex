from enum import Enum
from typing import Optional

from airtable_db.airtable_record import AirtableRecord
from airtable_db.table_columns import ContractsColumns, EventColumns, TicketCategory, TicketPriceLevel
from date_range import Day, DateRange
from utils import checked_type, checked_list_type


class ContractRecord(AirtableRecord):
    def __init__(self, airtable_rec: dict):
        self.airtable_rec = airtable_rec

    @property
    def performance_date(self):
        return Day.parse(self._airtable_value(ContractsColumns.PERFORMANCE_DATE))

    @property
    def record_id(self):
        return self._airtable_value(ContractsColumns.RECORD_ID)

    @property
    def events_link(self):
        return self._airtable_value(ContractsColumns.EVENTS_LINK)


class EventRecord(AirtableRecord):
    def __init__(self, airtable_rec: dict):
        super().__init__(airtable_rec)

    @property
    def event_id(self):
        return self._airtable_value(EventColumns.EVENT_ID)

    @property
    def title(self):
        return self._airtable_value(EventColumns.SHEETS_EVENT_TITLE)

    def num_paid_tickets(self, category: Optional[TicketCategory] = None,
                         price_level: Optional[TicketPriceLevel] = None) -> int:
        if category is None:
            return sum(self.num_paid_tickets(c, price_level) for c in TicketCategory)
        if price_level is None:
            return sum(self.num_paid_tickets(category, p) for p in TicketPriceLevel)
        if category == TicketCategory.ONLINE and price_level == TicketPriceLevel.OTHER:
            return 0
        column = EventColumns.num_tickets_column(category, price_level)
        return self._airtable_value(column, default=0)

    def num_free_tickets(self) -> int:
        return self._airtable_value(EventColumns.PROMO_TICKETS, 0)


class ContractAndEvents:
    def __init__(self, contract: ContractRecord, events: list[EventRecord]):
        self.contract = checked_type(contract, ContractRecord)
        self.events = checked_list_type(events, EventRecord)

    def num_paid_tickets(self, category: Optional[TicketCategory] = None,
                         price_level: Optional[TicketPriceLevel] = None) -> int:
        return sum(
            e.num_paid_tickets(category, price_level) for e in self.events
        )

    def num_free_tickets(self) -> int:
        return sum(
            e.num_free_tickets() for e in self.events
        )


class GigsInfo:
    def __init__(self, contracts_and_events: list[ContractAndEvents]):
        self.contracts_and_events = checked_list_type(contracts_and_events, ContractAndEvents)

    def restrict_to_period(self, period: DateRange) -> 'GigsInfo':
        return GigsInfo(
            [c for c in self.contracts_and_events if period.contains_day(c.contract.performance_date)])

    def num_paid_tickets(self, category: Optional[TicketCategory] = None,
                         price_level: Optional[TicketPriceLevel] = None) -> int:
        return sum(ce.num_paid_tickets(category, price_level) for ce in self.contracts_and_events)

    def num_free_tickets(self) -> int:
        return sum(
            e.num_free_tickets() for e in self.contracts_and_events
        )

    @property
    def total_tickets(self):
        return sum([ce.num_paid_tickets() + ce.num_free_tickets() for ce in self.contracts_and_events])
