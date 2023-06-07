from pyairtable import Table
from pyairtable.formulas import AND, FIELD

from date_range import DateRange, Day
from date_range.month import Month
from env import VORTEX_DATABASE_ID, AIRTABLE_TOKEN


class ContractRecord:
    def __init__(self, airtable_rec: dict):
        self.airtable_rec = airtable_rec

    def _airtable_value(self, field: str):
        if field not in self.airtable_rec['fields']:
            raise ValueError(f"No field '{field}' in record")
        return self.airtable_rec['fields'][field]

    @property
    def performance_date(self):
        return Day.parse(self._airtable_value(Contracts.PERFORMANCE_DATE))

    @property
    def record_id(self):
        return self._airtable_value(Contracts.RECORD_ID)


class Contracts:
    TABLE = "Contracts"

    CODE = "Code"
    RECORD_ID = "Record ID"
    EVENT_TITLE = "Event title"
    EVENTS_LINK = "Events Link"
    ORGANISERS = "Organisers"
    TYPE = "Type"
    STATUS = "Status"
    LIVE_PAYABLE = "Live Payable"
    VORTEX_PROFIT = "Vortex Profit"
    HIRE_FEE = "Hire fee"
    FOOD_BUDGET = "Food budget"
    COS_REQUIRED = "COS required"
    TOTAL_TICKET_SALES_CALC = "Total Ticket Sales £ calc"
    PERFORMANCE_DATE = "Performance date"

    B_ONLINE = "B - Online"
    C_CARD = "C - Card"
    D_CASH = "D - Cash"
    E_STUDENTS = "E - Students"
    N_CREDIT_CARD_TAKINGS = "N - Credit card takings"
    DEDUCTIONS = "Deductions"
    TOTAL_AUDIENCE = "Total audience"
    HOTEL = "Hotel?"
    HOTELS_COST = "Hotels cost"
    TRANSPORT = "Transport"
    TRANSPORT_COST = "Transport Cost"
    AUDIENCE_FOOD_COST = "Audience Food Cost "
    PRS_PAYABLE = "PRS?"
    PAID = "Paid?"
    NIGHT_MANAGER = "Night Manager"
    GRANTS = "Grants"

    FULL_TICKET_PRICE = "Full ticket price"
    MEMBER_TICKET_PRICE = "Member ticket price"
    STUDENT_TICKET_PRICE = "Student ticket price"
    MUSICIANS_FEE = "Musicians fee"

    def __init__(self):
        self.table = Table(AIRTABLE_TOKEN, VORTEX_DATABASE_ID, Contracts.TABLE)

    def records_for_date_range(self, date_range: DateRange, *fields):
        # Hack to avoid airtable time zone bug I can't quite figure
        first_day, last_day = date_range.first_day, date_range.last_day
        fields = list(fields)
        if Contracts.PERFORMANCE_DATE not in fields:
            fields += [Contracts.PERFORMANCE_DATE]
        first_date_constraint = f"{FIELD(Contracts.PERFORMANCE_DATE)} >= '{(first_day - 1).iso_repr}'"
        last_date_constraint = f"{FIELD(Contracts.PERFORMANCE_DATE)} <= '{(last_day + 1).iso_repr}'"
        formula = AND(first_date_constraint, last_date_constraint)
        recs =  [
            ContractRecord(rec)
            for rec in self.table.all(
                formula=formula,
                fields=fields
            )
        ]
        return [r for r in recs if first_day <= r.performance_date <= last_day]


if __name__ == '__main__':
    c = Contracts()
    period = Month(2023, 1)
    for rec in c.records_for_date_range(period, Contracts.RECORD_ID):
        print(rec.performance_date)
