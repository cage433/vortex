from vortex.airtable_db.contract_record import ContractRecord
from vortex.airtable_db.event_record import EventRecord
from vortex.airtable_db.table_columns import TicketCategory, TicketPriceLevel
from vortex.utils import checked_type, checked_list_type


class ContractAndEvents:
    def __init__(self, contract: ContractRecord, events: list[EventRecord]):
        self.contract = checked_type(contract, ContractRecord)
        self.events = checked_list_type(events, EventRecord)

    @property
    def performance_date(self):
        return self.contract.performance_date

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
    def event_titles(self) -> str:
        terms = []
        for e in self.events:
            if e.title is None:
                terms.append("No Title")
            elif isinstance(e.title, str):
                terms.append(e.title)
            elif isinstance(e.title, list):
                if len(e.title) == 0:
                    terms.append("No Title")
                else:
                    terms += e.title
            else:
                raise ValueError(f"Unexpected title type {e.title}, {type(e.title)}")
        terms = sorted(set(terms))
        return "/".join(terms)

    def walk_in_sales(self, price_level: TicketPriceLevel) -> float:
        sales = 0.0
        for e in self.events:
            num_tickets = e.num_paid_tickets(price_level=price_level, category=TicketCategory.WALK_IN)
            if num_tickets > 0:
                ticket_price = self.contract.ticket_price(price_level)
                sales += num_tickets * ticket_price
        return sales

    @property
    def other_ticket_sales(self) -> float:
        return sum([e.other_ticket_sales for e in self.events])

    @property
    def total_walk_in_sales(self) -> float:
        return sum([self.walk_in_sales(price_level) for price_level in
             [TicketPriceLevel.FULL, TicketPriceLevel.MEMBER, TicketPriceLevel.CONCESSION]]) + self.other_ticket_sales
