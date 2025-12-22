from typing import Optional

from airtable_db.airtable_record import AirtableRecord
from airtable_db.table_columns import EventColumns, TicketCategory, TicketPriceLevel


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
        if level == TicketPriceLevel.OTHER:
            return None
        return self._airtable_value(EventColumns.sales_override_column(level), allow_missing=True)

    @property
    def bar_takings(self) -> float:
        return self.column_float_value(EventColumns.BAR_TAKINGS, allow_missing=True) or 0.0

    @property
    def hire_fee(self) -> float:
        return self.column_float_value(EventColumns.HIRE_FEE, allow_missing=True) or 0.0
