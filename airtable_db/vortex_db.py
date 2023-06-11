from airtable_db.contracts_and_events import MultipleContractAndEvents, ContractAndEvents
from airtable_db.contracts_table import ContractsTable
from airtable_db.events_table import EventsTable
from airtable_db.table_columns import ContractsColumns, EventColumns
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

    def contracts_and_events_for_period(self, period: DateRange) -> MultipleContractAndEvents:
        contracts = self.contracts_table.records_for_date_range(period, ContractsColumns.RECORD_ID, ContractsColumns.EVENTS_LINK)
        events = self.events_table.records_for_contracts(contracts, EventColumns.EVENT_ID, EventColumns.SHEETS_EVENT_TITLE)
        grouped_events = group_into_dict(events, lambda e: e.event_id)
        return MultipleContractAndEvents([
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