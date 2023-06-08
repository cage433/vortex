from airtable_db.airtable_record import AirtableRecord
from airtable_db.table_columns import ContractsColumns, EventColumns
from date_range import Day
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


class EventRecord(AirtableRecord):
    def __init__(self, airtable_rec: dict):
        super().__init__(airtable_rec)

    @property
    def event_id(self):
        return self._airtable_value(EventColumns.EVENT_ID)

    @property
    def title(self):
        return self._airtable_value(EventColumns.SHEETS_EVENT_TITLE)


class ContractAndEvents:
    def __init__(self, contract: ContractRecord, events: list[EventRecord]):
        self.contract = checked_type(contract, ContractRecord)
        self.events = checked_list_type(events, EventRecord)


class MultipleContractAndEvents:
    def __init__(self, contracts_and_events: list[ContractAndEvents]):
        self.contracts_and_events = checked_list_type(contracts_and_events, ContractAndEvents)
