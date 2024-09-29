from typing import Optional

from airtable_db.contract_and_events import ContractAndEvents
from airtable_db.table_columns import ContractsColumns, EventColumns, TicketCategory, TicketPriceLevel
from date_range import DateRange
from myopt.something import Something
from utils import checked_list_type


class GigsInfo:
    def __init__(self, contracts_and_events: list[ContractAndEvents]):
        self.contracts_and_events = checked_list_type(contracts_and_events, ContractAndEvents)

    @property
    def number_of_gigs(self):
        return len(
            [
                ce for ce in
                self.contracts_and_events
                if ce.contract.contract_type in [Something("Performance"), Something("Hire")]
            ]
        )

    @property
    def first_day(self):
        return min(ce.contract.performance_date for ce in self.contracts_and_events)

    @property
    def last_day(self):
        return max(ce.contract.performance_date for ce in self.contracts_and_events)

    def restrict_to_period(self, period: DateRange) -> 'GigsInfo':
        return GigsInfo(
            [c for c in self.contracts_and_events if period.contains_day(c.contract.performance_date)])

    def restrict_to_gigs(self) -> 'GigsInfo':
        return GigsInfo(
            [c for c in self.contracts_and_events if
             c.contract.contract_type in [Something("Performance"), Something("Hire")]])

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
    def total_walk_in_tickets(self):
        return self._event_sum(lambda e: e.num_free_tickets + e.num_paid_tickets())

    @property
    def total_walk_in_sales(self) -> float:
        return sum(
            ce.walk_in_sales(price_level)
            for ce in self.contracts_and_events
            for price_level in [TicketPriceLevel.FULL, TicketPriceLevel.MEMBER, TicketPriceLevel.CONCESSION]
        ) + self.other_ticket_sales

    @property
    def total_ticket_sales(self) -> float:
        return sum(
            self.ticket_sales(p) for p in
            [TicketPriceLevel.FULL, TicketPriceLevel.MEMBER, TicketPriceLevel.CONCESSION]
        ) + self.other_ticket_sales

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
