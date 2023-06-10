from airtable_db.contracts_and_events import MultipleContractAndEvents
from date_range.month import Month
from sheets import Workbook, Worksheet


class MonthlyAccounts(Worksheet):
    def __init__(self, workbook: Workbook, month: Month):
        super().__init__(workbook, month.tab_name)

    def update(self, contracts_and_events: MultipleContractAndEvents):
        pass