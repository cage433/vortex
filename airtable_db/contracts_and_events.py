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

    def ticket_price(self, price_level: TicketPriceLevel) -> int:
        price = self._airtable_value(ContractsColumns.ticket_price_column(price_level))
        if price is None:
            price = self._airtable_value(ContractsColumns.ticket_price_column(TicketPriceLevel.FULL))
        return price


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

    @property
    def num_free_tickets(self) -> int:
        return self._airtable_value(EventColumns.PROMO_TICKETS, default=0)

    @property
    def other_ticket_sales(self) -> float:
        return self._airtable_value(EventColumns.OTHER_TICKET_SALES, default=0)

    def ticket_sales_override(self, level: TicketPriceLevel) -> Optional[float]:
        return self._airtable_value(EventColumns.sales_override_column(level))

    @property
    def bar_takings(self) -> float:
        return self._airtable_value(EventColumns.BAR_TAKINGS, default=0)

    @property
    def hire_fee(self) -> float:
        return self._airtable_value(EventColumns.HIRE_FEE, default=0)


class ContractAndEvents:
    def __init__(self, contract: ContractRecord, events: list[EventRecord]):
        self.contract = checked_type(contract, ContractRecord)
        self.events = checked_list_type(events, EventRecord)

    def ticket_sales(self, price_level: TicketPriceLevel) -> float:
        sales = 0
        for e in self.events:
            if e.ticket_sales_override(price_level) is not None:
                sales += e.ticket_sales_override(price_level)
            else:
                num_tickets = e.num_paid_tickets(price_level=price_level)
                ticket_price = self.contract.ticket_price(price_level)
                sales += num_tickets * ticket_price
        return sales


class GigsInfo:
    def __init__(self, contracts_and_events: list[ContractAndEvents]):
        self.contracts_and_events = checked_list_type(contracts_and_events, ContractAndEvents)

    def restrict_to_period(self, period: DateRange) -> 'GigsInfo':
        return GigsInfo(
            [c for c in self.contracts_and_events if period.contains_day(c.contract.performance_date)])

    def num_paid_tickets(self, category: Optional[TicketCategory] = None,
                         price_level: Optional[TicketPriceLevel] = None) -> int:
        return self._event_sum(lambda e: e.num_paid_tickets(category, price_level))

    def _event_sum(self, func):
        return sum(func(e) for ce in self.contracts_and_events for e in ce.events)

    @property
    def num_free_tickets(self) -> int:
        return self._event_sum(lambda e: e.num_free_tickets)

    @property
    def total_tickets(self):
        return self._event_sum(lambda e: e.num_free_tickets + e.num_paid_tickets())

    def ticket_sales(self, price_level: TicketPriceLevel) -> float:
        return sum(ce.ticket_sales(price_level) for ce in self.contracts_and_events)

    @property
    def other_ticket_sales(self) -> float:
        return self._event_sum(lambda e: e.other_ticket_sales)

    @property
    def hire_fees(self) -> float:
        return self._event_sum(lambda e: e.hire_fee)

    @property
    def bar_takings(self):
        return self._event_sum(lambda e: e.bar_takings)