from pyairtable import Table
from pyairtable.formulas import AND, FIELD

from airtable_db.contracts_and_events import ContractRecord
from airtable_db.table_columns import ContractsColumns
from date_range import DateRange
from env import VORTEX_DATABASE_ID, AIRTABLE_TOKEN


class ContractsTable:
    TABLE = "Contracts"

    def __init__(self):
        self.table = Table(AIRTABLE_TOKEN, VORTEX_DATABASE_ID, ContractsTable.TABLE)

    def records_for_date_range(self, date_range: DateRange, *fields):
        # Hack to avoid airtable time zone bug I can't quite figure
        first_day, last_day = date_range.first_day, date_range.last_day
        fields = list(fields)
        if ContractsColumns.PERFORMANCE_DATE not in fields:
            fields += [ContractsColumns.PERFORMANCE_DATE]
        first_date_constraint = f"{FIELD(ContractsColumns.PERFORMANCE_DATE)} >= '{(first_day - 1).iso_repr}'"
        last_date_constraint = f"{FIELD(ContractsColumns.PERFORMANCE_DATE)} <= '{(last_day + 1).iso_repr}'"
        formula = AND(first_date_constraint, last_date_constraint)
        recs = [
            ContractRecord(rec)
            for rec in self.table.all(
                formula=formula,
                fields=fields
            )
        ]
        return [r for r in recs if first_day <= r.performance_date <= last_day]
