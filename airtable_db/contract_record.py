from airtable_db.airtable_record import AirtableRecord
from airtable_db.table_columns import ContractsColumns, TicketPriceLevel
from date_range import Day
from myopt.opt import Opt
from myopt.something import Something



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

    def ticket_price(self, price_level: TicketPriceLevel) -> float:
        price = self._airtable_value(ContractsColumns.ticket_price_column(price_level), allow_missing=True)
        if price is None:
            price = self._airtable_value(ContractsColumns.ticket_price_column(TicketPriceLevel.FULL),
                                         allow_missing=False)
        return price

    @property
    def contract_type(self) -> Opt[str]:
        return Opt.of(self._airtable_value(ContractsColumns.TYPE, allow_missing=True))

    @property
    def is_hire(self):
        return self.contract_type == Something("Hire")

    def event_title(self, allow_missing: bool = False) -> str:
        return self._airtable_value(ContractsColumns.EVENT_TITLE, allow_missing=allow_missing)

    @property
    def door_time(self) -> Opt[str]:
        return Opt.of(self._airtable_value(ContractsColumns.DOOR_TIME_1ST_SHOW, allow_missing=True))
