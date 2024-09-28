from airtable_db.contract_record import ContractRecord
from airtable_db.event_record import EventRecord
from airtable_db.table_columns import TicketCategory, TicketPriceLevel
from utils import checked_type, checked_list_type



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

    def walk_in_sales(self, price_level: TicketPriceLevel) -> float:
        sales = 0.0
        for e in self.events:
            num_tickets = e.num_paid_tickets(price_level=price_level, category=TicketCategory.WALK_IN)
            if num_tickets > 0:
                ticket_price = self.contract.ticket_price(price_level)
                sales += num_tickets * ticket_price
        return sales

