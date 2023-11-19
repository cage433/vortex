from airtable_db.contracts_and_events import GigsInfo, ContractAndEvents
from airtable_db.contracts_table import ContractsTable
from airtable_db.events_table import EventsTable
from airtable_db.table_columns import ContractsColumns, EventColumns, TicketCategory, TicketPriceLevel
from date_range import DateRange
from date_range.month import Month
from utils.collection_utils import group_into_dict, flatten

__all__ = [
    "VortexDB",
]


class VortexDB:
    def __init__(self):
        self.contracts_table = ContractsTable()
        self.events_table = EventsTable()

    def contracts_and_events_for_period(self, period: DateRange) -> GigsInfo:
        contracts_columns = [
            ContractsColumns.ticket_price_column(level)
            for level in [TicketPriceLevel.FULL, TicketPriceLevel.MEMBER, TicketPriceLevel.CONCESSION]
        ]
        contracts_columns += [
            ContractsColumns.RECORD_ID,
            ContractsColumns.EVENTS_LINK,
            ContractsColumns.MUSICIANS_FEE,
            ContractsColumns.PRS_FEE_EX_VAT,
            ContractsColumns.TRANSPORT_COST,
            ContractsColumns.HOTELS_COST,
            ContractsColumns.FOOD_BUDGET,
            ContractsColumns.TYPE,
        ]
        contracts = self.contracts_table.records_for_date_range(
            period, contracts_columns
        )

        events_columns = [
            EventColumns.num_tickets_column(category, price_level)
            for category in TicketCategory
            for price_level in TicketPriceLevel
            if not (category == TicketCategory.ONLINE and price_level == TicketPriceLevel.OTHER)
        ]
        events_columns += [
            EventColumns.BAR_TAKINGS,
            EventColumns.EVENING_PURCHASES,
            EventColumns.EVENT_ID,
            EventColumns.HIRE_FEE,
            EventColumns.OTHER_TICKET_SALES,
            EventColumns.PROMO_TICKETS,
            EventColumns.SHEETS_EVENT_TITLE,
        ]
        events_columns += [
            EventColumns.sales_override_column(price_level)
            for price_level in TicketPriceLevel
            if price_level != TicketPriceLevel.OTHER
        ]
        events = self.events_table.records_for_contracts(contracts, events_columns)
        grouped_events = group_into_dict(events, lambda e: e.event_id)
        return GigsInfo([
            ContractAndEvents(
                contract,
                flatten([
                    grouped_events[event_id] for event_id in contract.events_link
                ])
            )
            for contract in contracts
        ])


if __name__ == '__main__':
    db = VortexDB()
    period = Month(2023, 1)
    contracts_and_events = db.contracts_and_events_for_period(period)
    for contract_and_events in contracts_and_events.contracts_and_events:
        print()
        print(contract_and_events.contract.record_id)
        for event in contract_and_events.events:
            print(event.title)
