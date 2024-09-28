import shelve
from pathlib import Path

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

from utils.logging import log_message


class VortexDB:
    def __init__(self):
        self.contracts_table = ContractsTable()
        self.events_table = EventsTable()

    SHELF = Path(__file__).parent / "_vortex_db.shelf"

    def gigs_info_for_period(self, period: DateRange, force: bool) -> GigsInfo:
        key = f"gig_info_{period}"
        with shelve.open(str(VortexDB.SHELF)) as shelf:
            if key not in shelf or force:
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
                shelf[key] = GigsInfo([
                    ContractAndEvents(
                        contract,
                        flatten([
                            grouped_events[event_id] for event_id in contract.events_link
                        ])
                    )
                    for contract in contracts
                ])
            return shelf[key]


if __name__ == '__main__':
    db = VortexDB()
    period = Month(2023, 1)
    log_message(f"Getting gigs info for {period}")
    contracts_and_events = db.gigs_info_for_period(period, force=True).contracts_and_events
    for c in contracts_and_events:
        print(c.contract)
        for e in c.events:
            print(e)
        print()
    log_message(f"Done")
