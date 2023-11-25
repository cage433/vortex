from typing import Optional

from airtable_db.airtable_record import AirtableRecord
from airtable_db.table_columns import ContractsColumns, EventColumns, TicketCategory, TicketPriceLevel
from date_range import Day, DateRange
from utils import checked_type, checked_list_type


class ContractRecord(AirtableRecord):
    def __init__(self, airtable_rec: dict):
        super().__init__(airtable_rec)

    @property
    def performance_date(self):
        return Day.parse(self._airtable_value(ContractsColumns.PERFORMANCE_DATE, allow_missing=False))

    @property
    def record_id(self):
        return self._airtable_value(ContractsColumns.RECORD_ID, allow_missing=False)

    @property
    def events_link(self):
        return self._airtable_value(ContractsColumns.EVENTS_LINK, allow_missing=False)

    def ticket_price(self, price_level: TicketPriceLevel) -> int:
        price = self._airtable_value(ContractsColumns.ticket_price_column(price_level), allow_missing=True)
        if price is None:
            price = self._airtable_value(ContractsColumns.ticket_price_column(TicketPriceLevel.FULL), allow_missing=False)
        return price

    @property
    def is_hire(self):
        return self._airtable_value(ContractsColumns.TYPE, allow_missing=True) == "Hire"


class EventRecord(AirtableRecord):
    def __init__(self, airtable_rec: dict):
        super().__init__(airtable_rec)

    @property
    def event_id(self):
        return self._airtable_value(EventColumns.EVENT_ID, allow_missing=False)

    @property
    def title(self):
        return self._airtable_value(EventColumns.SHEETS_EVENT_TITLE, allow_missing=False)

    def num_paid_tickets(self, category: Optional[TicketCategory] = None,
                         price_level: Optional[TicketPriceLevel] = None) -> int:
        if category is None:
            return sum(self.num_paid_tickets(c, price_level) for c in TicketCategory)
        if price_level is None:
            return sum(self.num_paid_tickets(category, p) for p in TicketPriceLevel)
        if category == TicketCategory.ONLINE and price_level == TicketPriceLevel.OTHER:
            return 0
        column = EventColumns.num_tickets_column(category, price_level)
        return self._airtable_value(column, allow_missing=True) or 0

    @property
    def num_free_tickets(self) -> int:
        return self._airtable_value(EventColumns.PROMO_TICKETS, allow_missing=True) or 0

    @property
    def other_ticket_sales(self) -> float:
        return self._airtable_value(EventColumns.OTHER_TICKET_SALES, allow_missing=True) or 0

    def ticket_sales_override(self, level: TicketPriceLevel) -> Optional[float]:
        return self._airtable_value(EventColumns.sales_override_column(level), allow_missing=True)

    @property
    def bar_takings(self) -> float:
        return self.column_float_value(EventColumns.BAR_TAKINGS, allow_missing=True) or 0.0

    @property
    def hire_fee(self) -> float:
        return self.column_float_value(EventColumns.HIRE_FEE, allow_missing=True) or 0.0



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
                if num_tickets > 0:
                    ticket_price = self.contract.ticket_price(price_level)
                    sales += num_tickets * ticket_price
        return sales

    @property
    def is_hire(self):
        return self.contract.is_hire


class GigsInfo:
    def __init__(self, contracts_and_events: list[ContractAndEvents]):
        self.contracts_and_events = checked_list_type(contracts_and_events, ContractAndEvents)

    @property
    def number_of_gigs(self):
        return len(self.contracts_and_events)

    def restrict_to_period(self, period: DateRange) -> 'GigsInfo':
        return GigsInfo(
            [c for c in self.contracts_and_events if period.contains_day(c.contract.performance_date)])

    def num_paid_tickets(self, category: Optional[TicketCategory] = None,
                         price_level: Optional[TicketPriceLevel] = None) -> int:
        return self._event_sum(lambda e: e.num_paid_tickets(category, price_level))

    def _event_column_sum(self, column: str, allow_missing: bool):
        return self._event_sum(lambda e: e.column_float_value(column, allow_missing) or 0)

    def _event_sum(self, func):
        return sum(func(e) for ce in self.contracts_and_events for e in ce.events)

    def _contract_sum(self, func):
        return sum(func(ce.contract) for ce in self.contracts_and_events)

    def _contract_column_sum(self, column: str, allow_missing: bool):
        return self._contract_sum(lambda c: c.column_float_value(column, allow_missing) or 0)

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
        return self._event_column_sum(EventColumns.OTHER_TICKET_SALES, allow_missing=True) or 0

    @property
    def hire_fees(self) -> float:
        return self._event_column_sum(EventColumns.HIRE_FEE, allow_missing=True) or 0

    @property
    def bar_takings(self):
        return self._event_column_sum(EventColumns.BAR_TAKINGS, allow_missing=True) or 0

    @property
    def musicians_fees(self):
        return self._contract_column_sum(ContractsColumns.MUSICIANS_FEE, allow_missing=True) or 0

    @property
    def band_accommodation(self):
        return self._contract_column_sum(ContractsColumns.HOTELS_COST, allow_missing=True) or 0

    @property
    def band_catering(self):
        return self._contract_column_sum(ContractsColumns.FOOD_BUDGET, allow_missing=True) or 0

    @property
    def band_transport(self):
        return self._contract_column_sum(ContractsColumns.TRANSPORT_COST, allow_missing=True) or 0

    @property
    def prs_fee_ex_vat(self):
        return self._contract_column_sum(ContractsColumns.PRS_FEE_EX_VAT, allow_missing=True) or 0

    @property
    def evening_purchases(self):
        return self._event_column_sum(EventColumns.EVENING_PURCHASES, allow_missing=True) or 0

    @property
    def excluding_hires(self):
        return GigsInfo([ce for ce in self.contracts_and_events if not ce.contract.is_hire])